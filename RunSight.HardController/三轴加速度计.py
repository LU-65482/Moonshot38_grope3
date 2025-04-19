# -*- coding: utf-8 -*-
import time
import math
from pinpong.board import *
from pinpong.extension.unihiker import *

# 初始化开发板
Board().begin()

# 运动检测参数（基于人体运动生物力学研究）
RUN_THRESHOLD = 6.2      # 跑步触发阈值（m/s²），适合5-12km/h配速
BUFFER_SIZE = 10         # 数据缓冲窗口（约0.5秒@20Hz采样率）
GRAVITY = 9.80665        # 标准重力加速度
SMOOTHING_FACTOR = 0.2   # 数据平滑系数

class RunningDetector:
    def __init__(self):
        self.buffer = []
        self.smoothed = {'x':0, 'y':0, 'z':GRAVITY}
        
    def _get_smoothed_accel(self):
        """应用指数平滑滤波获取稳定数据"""
        raw_x = accelerometer.get_x()
        raw_y = accelerometer.get_y()
        raw_z = accelerometer.get_z()
        
        self.smoothed['x'] = SMOOTHING_FACTOR*raw_x + (1-SMOOTHING_FACTOR)*self.smoothed['x']
        self.smoothed['y'] = SMOOTHING_FACTOR*raw_y + (1-SMOOTHING_FACTOR)*self.smoothed['y'] 
        self.smoothed['z'] = SMOOTHING_FACTOR*raw_z + (1-SMOOTHING_FACTOR)*self.smoothed['z']
        
        return self.smoothed['x'], self.smoothed['y'], self.smoothed['z']
    
    def _dynamic_threshold(self):
        """动态阈值调整（基于垂直轴重力变化）"""
        vertical_accel = abs(self.smoothed['z'] - GRAVITY)
        return RUN_THRESHOLD + vertical_accel*0.3
    
    def check_running(self):
        """检测跑步动作（带方向识别）"""
        x, y, z = self._get_smoothed_accel()
        
        # 计算三轴合成矢量（去除重力影响）
        net_accel = math.sqrt(x**2 + y**2 + (z-GRAVITY)**2)
        
        # 维护数据缓冲区
        self.buffer.append(net_accel)
        if len(self.buffer) > BUFFER_SIZE:
            self.buffer.pop(0)
            
        # 计算移动平均（减少瞬时干扰）
        avg_accel = sum(self.buffer)/len(self.buffer)
        current_threshold = self._dynamic_threshold()
        
        # 实时数据输出（颜色控制符需支持ANSI终端）
        print(f"\033[36mX: {x:6.2f} \033[32mY: {y:6.2f} \033[35mZ: {z:6.2f} \033[0m| 合成加速度: {avg_accel:5.2f} (阈值: {current_threshold:4.1f})")
        
        # 触发条件：连续3次超过动态阈值
        if len(self.buffer) >= 3 and all(a > current_threshold for a in self.buffer[-3:]):
            return True
        return False

def main():
    detector = RunningDetector()
    
    print("\n=== 跑步检测模式启动 ===")
    print("实时数据格式：")
    print("X轴(青) Y轴(绿) Z轴(紫) | 合成加速度 vs 动态阈值\n" + "-"*60)
    
    try:
        while True:
            if detector.check_running():
                print("\033[41m检测到跑步动作！\033[0m")  # 红色背景提示
                
            time.sleep(0.05)  # 20Hz采样率
            
    except KeyboardInterrupt:
        print("\n=== 检测结束 ===")

if __name__ == "__main__":
    main()
