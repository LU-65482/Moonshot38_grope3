# -*- coding: UTF-8 -*-
import time
from pinpong.board import Board,Pin

Board().begin()               #初始化

led = Pin(Pin.P9, Pin.OUT) #引脚初始化为电平输出
time = 0.1

while True:
  #led.value(1) #输出高电平 方法1
  led.write_digital(1) #输出高电平 方法2
  print("1") #终端打印信息
  time.sleep(time) #等待1秒 保持状态

  #led.value(0) #输出低电平 方法1
  led.write_digital(0) #输出低电平 方法2
  print("0") #终端打印信息
  time.sleep(time) #等待1秒 保持状态