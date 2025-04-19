# -*- coding: utf-8 -*-
import time
import threading
import os
import sys
from pinpong.board import Board, Pin
from pinpong.extension.unihiker import accelerometer
from unihiker import Audio 
import openai


# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from web import start_server
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
        self.audio.play('/root/work/test.wav')
        
        # 系统参数
        self.base_z = 9.81
        self.buffer = []
        self.last_trigger = 0
        
        # 启动初始化
        self._simple_calibrate()
        self._hardware_test()
        
        # 启动 Web 服务
        self._start_web_service()
    
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
        with open(filename, "rb") as f:
            resultInput = self.ai1.audio.transcribe(
                model="Systran/faster-whisper-large-v3",
                file=f,
                response_format="text",
                language="zh"
            )
        print('>', resultInput)
        res = self.ai2.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个中文客服助理。"},
                {"role": "user", "content": resultInput}
            ]
        )
        rsp = res["choices"][0]["message"]["content"]
        print(rsp)
        os.remove(filename)
    
    def _shutdown(self):
        """安全关闭系统"""
        self.motor.write_digital(0)
        self.buzzer.write_digital(0)
        self.status_led.write_digital(0)
        print("\n[系统] 安全关闭完成")

if __name__ == "__main__":
    system = SafetySystem()
    system.monitor_loop()
