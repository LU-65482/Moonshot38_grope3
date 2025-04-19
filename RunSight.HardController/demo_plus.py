# -*- coding: utf-8 -*-
import time
from pinpong.board import Board, Pin
from pinpong.extension.unihiker import accelerometer

# 初始化开发板
Board().begin()
motor = Pin(Pin.P9, Pin.OUT) #引脚初始化为电平输出

# 急停检测参数（基于运动生物力学实验）
Z_THRESHOLD = -1       # 急停阈值（m/s²）
GRAVITY = 9.81           # 标准重力加速度
BUFFER_SIZE = 8          # 数据窗口大小（0.4秒@20Hz采样）
FILTER_FACTOR = 0.3      # 滤波系数

#用户交互体验参数
warning = 2              #提醒次数
warning_time = 0.5       # 

class EmergencyStopDetector:
    def __init__(self):
        self.buffer = []
        self.base_z = GRAVITY
        self._calibrate()
        
    def _calibrate(self):
        """静态校准获取基准Z轴值"""
        print("校准中...保持设备静止")
        samples = [accelerometer.get_z() for _ in range(50)]
        self.base_z = sum(samples)/len(samples)
        print(f"基准重力: {self.base_z:.1f}m/s²")
    
    def _process_z(self, raw_z):
        """信号处理：滤波+去重力"""
        return FILTER_FACTOR*(raw_z - self.base_z) + (1-FILTER_FACTOR)*self.base_z
    
    def check_stop(self):
        """急停检测逻辑"""
        processed_z = self._process_z(accelerometer.get_z())
        net_z = processed_z - self.base_z
        
        # 维护数据缓冲
        self.buffer.append(net_z)
        if len(self.buffer) > BUFFER_SIZE:
            self.buffer.pop(0)
        
        # 简化输出（单行刷新）
        status = "NORMAL" if net_z > Z_THRESHOLD else "STOP!"
        print(f"Z轴加速度: {net_z:6.2f}m/s² | 状态: {status.ljust(6)}", end='\r')
        
        # 触发条件：连续3次超阈值
        return len(self.buffer)>=3 and all(z < Z_THRESHOLD for z in self.buffer[-3:])

def warning_to_user():
    for i in range(2):
        motor.write_digital(1)
        time.sleep(0.5)
        motor.write_digital(0)

def main():
    detector = EmergencyStopDetector()
    print("=== 急停检测模式 ===")
    print(f"阈值: {Z_THRESHOLD}m/s² 采样率: 20Hz")
    
    try:
        while True:
            if detector.check_stop():
                print("\n\033[41m! 急停检测 !\033[0m")
                warning_to_user()
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n检测结束")

if __name__ == "__main__":
    main()
