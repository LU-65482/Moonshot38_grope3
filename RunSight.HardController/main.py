# -*- coding: utf-8 -*-
import time
import threading
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from typing import Optional
import os
import sys, json
from datetime import datetime
from pinpong.board import Board, Pin
from pinpong.extension.unihiker import accelerometer
from unihiker import Audio 
import openai
import requests
from web import start_server, current_config
import voice_interact

# 初始化开发板
Board().begin()

# 硬件配置
MOTOR_PIN = Pin.P9        # 震动马达引脚
BUZZER_PIN = Pin.P8       # 蜂鸣器引脚
STATUS_LED = Pin.P21      # 状态指示灯

# 核心参数（根据实际测试调整）
Z_THRESHOLD = -5.5       # 急停阈值 (m/s²)
BUFFER_SIZE = 6          # 数据窗口大小
DEBOUNCE_TIME = 2.0      # 触发冷却时间
#参数推荐范围调节效果
#Z_THRESHOLD-3.5 ~ -5.5 负值越小，灵敏度越低
#BUFFER_SIZE5 ~ 10 值越大，抗干扰能力越强
#DEBOUNCE_TIME1.5 ~ 3.0 值越大，误报率越低

OPENAI_MODEL = os.getenv("OPENAI_MODEL")

functions = [
    {
        'type': 'function',
        'function': {
             "name": "start_exercise",
            "description": "开始运动，当用户说'开始运动'时调用此工具",
            "parameters": {
                "type": "object"
            }
        }
    },
    {
        'type': 'function',
        'function': {
            "name": "end_exercise",
            "description": "结束运动，当用户说'结束运动'时调用此工具",
            "parameters": {
                "type": "object"
            }
        }
    }
]

prompt = """
你是 RunSight 系统中的 AI 智能语音助手，专为视障跑者打造。你不仅是一位运动助手，更是一位温柔的同行者。

你的核心职责包括：
	- 通过自然语言与用户进行友好、温暖、耐心的对话；
	- 协助用户执行跑步相关的语音指令，如“开始跑步”、“匹配引导员”、“查看我的数据”等；
	- 在跑步过程中，适时给予情绪支持和安全提醒，例如：“你已经跑了 500 米，做得很棒！”、“前方转弯，请跟随引导员”；
	- 理解用户的情绪，使用关怀性的语言缓解他们的紧张或孤独，比如：“我会陪你一起完成接下来的路程。”、“慢慢来，我们一起加油”；
	- 永远以尊重、陪伴、安全为原则，用人性化的语音反馈增强用户的信任感和归属感。

你不是冷冰冰的程序，而是一个真正“看见”视障跑者内心需求的朋友，但请注意你是一个语音助手，在进行语音回复时要像聊天一样简短。
"""

class SafetySystem:
    def __init__(self):
        print("====启动硬件自检====")
        # 初始化硬件
        self.motor = Pin(MOTOR_PIN, Pin.OUT)
        self.buzzer = Pin(BUZZER_PIN, Pin.OUT)
        self.status_led = Pin(STATUS_LED, Pin.OUT)
        
        self.ai1 = openai.OpenAI(
            api_key=os.getenv("OPENAI_KEY1"),  # 如果您没有配置环境变量，请用百炼 API Key 将本行替换为：api_key="sk-xxx"
            base_url=os.getenv("OPENAI_BASEURL1"),  # 填写 DashScope SDK 的 base_url
        )
        self.ai2 = openai.OpenAI(
            api_key=os.getenv("OPENAI_KEY2"),  # 如果您没有配置环境变量，请用百炼 API Key 将本行替换为：api_key="sk-xxx"
            base_url=os.getenv("OPENAI_BASEURL2"),  # 填写 DashScope SDK 的 base_url
        )
        self.audio = Audio()
        # self.audio.play('/root/work/test.wav')
        
        # 系统参数
        self.base_z = 9.81
        self.buffer = []
        self.last_trigger = 0
        
        # 启动初始化
        self._simple_calibrate()
        self._hardware_test()
        
        # 启动 Web 服务
        self._start_web_service()
        
        self._start_voice_service()
    
    def _start_web_service(self):
        """启动 Web 服务"""
        print("[系统] 正在启动 Web 服务...")
        web_thread = threading.Thread(target=start_server, daemon=True)
        web_thread.start()
        print("[系统] Web 服务已启动")
        
        
    def _start_voice_service(self):
        """启动语音交互服务"""
        print("[系统] 正在启动语音交互服务...")
        voice_interact.speech_captured = lambda filename: self.on_speech_captured(filename)
        web_thread = threading.Thread(target=voice_interact.work, daemon=True)
        web_thread.start()
        print("[系统] 语音交互服务已启动")
    
    def _simple_calibrate(self):
        """3 秒快速校准"""
        print("[校准] 正在校准传感器...")
        samples = []
        for _ in range(50):
            samples.append(accelerometer.get_z())
            time.sleep(0.02)
        self.base_z = sum(samples)/len(samples)
        print(f"[校准] 基准值：{self.base_z:.1f}m/s²")
    
    def _hardware_test(self):
        """硬件自检"""
        print("[自检] 正在测试外设...")
        for device in [self.motor, self.buzzer, self.status_led]:
            device.write_digital(1)
            time.sleep(0.2)
            device.write_digital(0)
        print("[自检] 外设测试完成")
    
    def _safe_get_z(self):
        """带异常保护的传感器读取"""
        try:
            return accelerometer.get_z() - self.base_z
        except Exception as e:
            print(f"[错误] 传感器读取失败：{str(e)}")
            return 0.0  # 返回安全值
    
    def _activate_alarm(self):
        """触发报警装置"""
        self.last_trigger = time.time()
        
        # 报警模式：3 次震动 + 蜂鸣
        for _ in range(3):
            self.motor.write_digital(1)
            self.buzzer.write_digital(1)
            self.status_led.write_digital(1)
            time.sleep(0.3)
            
            self.motor.write_digital(0) 
            self.buzzer.write_digital(0)
            self.status_led.write_digital(0)
            time.sleep(0.2)
    
    def monitor_loop(self):
        """主监控循环"""
        print("[系统] 安全监控已启动")
        try:
            while True:
                # 读取并处理数据
                current_z = self._safe_get_z()
                self.buffer = (self.buffer + [current_z])[-BUFFER_SIZE:]
                
                # 显示简化信息
                print(f"Z 轴：{current_z:6.2f} 状态：{'正常' if current_z > Z_THRESHOLD else '急停'}".ljust(40), end='\r')
                
                # 触发条件判断
                if len(self.buffer) >= 3 and all(z < Z_THRESHOLD for z in self.buffer[-3:]):
                    if time.time() - self.last_trigger > DEBOUNCE_TIME:
                        print("\n[警报] 检测到急停事件！")
                        self._activate_alarm()
                
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            self._shutdown()
            
    def on_speech_captured(self, filename: str): 
        try:
            with open(filename, "rb") as f:
                resultInput = self.ai1.audio.transcriptions.create(
                    model="Systran/faster-whisper-large-v3",
                    file=f,
                    response_format="text",
                    language="zh"
                )
            print('whisper>', resultInput)
            res = self.ai2.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": resultInput}
                ],
                tools=functions,
                tool_choice="auto"
            )
            message = res.choices[0].message
            if message.tool_calls is not None and len(message.tool_calls) >= 1:
                func_name = message.tool_calls[0].function.name
                if func_name == "start_exercise":
                    print("开始运动")
                elif func_name == "end_exercise":
                    print("结束运动")
                    self._upload_data()
            rsp = res.choices[0].message.content
            print(rsp)

            # 定义 API 的 URL 和端口
            url = "http://10.1.2.101:9880/tts"

            # 构造请求数据
            data = {
                "text": rsp,
                "text_lang": "zh",  # 文本语言
                "ref_audio_path": "【普通】为曾经拥有过某种幸福而开心，为未来依旧会出现奇迹而期待。.wav",  # 参考音频路径
                "prompt_lang": "zh",  # 提示文本语言
                "prompt_text": "为曾经拥有过某种幸福而开心，为未来依旧会出现奇迹而期待。",
                "top_k": 5,
                "top_p": 1.0,
                "temperature": 1.0,
                "batch_size": 1,
                "media_type": "wav",  # 返回的音频格式
                "streaming_mode": False,  # 是否启用流式传输
                "text_split_method": "cut3",
            }

            # 发送 POST 请求
            response = requests.post(url, json=data)

            # 检查返回状态并处理响应
            if response.status_code == 200:
                # 保存返回的音频流
                with open("/tmp/output.wav", "wb") as f:
                    f.write(response.content)
                print("生成的语音已保存为 /tmp/output.wav")
                self.audio.play("/tmp/output.wav")
            else:
                # 输出错误信息
                print(f"请求失败：{response.status_code}")
                print(response.json())
        except Exception as e:
            print(f"[错误] 语音识别失败：{str(e)}")
        finally:
            os.remove(filename)
    
    def _shutdown(self):
        """安全关闭系统"""
        self.motor.write_digital(0)
        self.buzzer.write_digital(0)
        self.status_led.write_digital(0)
        print("\n[系统] 安全关闭完成")
        
    def _upload_data(self):
        """上传数据"""
        print("[上传] 正在上传数据...")
        data = {
            "userId": current_config.UID or 1,  # 使用配置的 UID，如果为空则使用默认值 1
            "runDate": datetime.now().isoformat(),
            "distance": 7.5,
            "averagePace": 10,
            "averageHeartRate": 70,
            "routeMap": "string",
            "notes": "string",
            "isPublic": True,
            "createdAt": datetime.now().isoformat()
        }
        url = "http://10.1.2.101:5238/api/RunningData"
        response = requests.post(url, json=data)
        print("[上传] 数据上传完成")

if __name__ == "__main__":
    system = SafetySystem()
    system.monitor_loop()
