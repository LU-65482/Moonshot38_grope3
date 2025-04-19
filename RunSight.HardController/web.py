# -*- coding: utf-8 -*-
import time
import threading
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from typing import Optional
import os


# 配置模型
class Configure(BaseModel):
    SpeedThreshold: Optional[float]
    WifiSSID: Optional[str] = None
    WifiPassword: Optional[str] = None

# 响应模型
class Response(BaseModel):
    RetCode: int  # 0: 成功，1: 失败
    Message: str

# 创建 FastAPI 应用
app = FastAPI(title="RunSight 硬件控制器 API")

# 全局配置
current_config = Configure(
    SpeedThreshold=-5.5,
    WifiSSID="",
    WifiPassword=""
)

@app.get("/configure", response_model=Configure)
async def get_configure():
    """获取当前配置"""
    return current_config

@app.post("/configure", response_model=Response)
async def update_configure(configure: Configure):
    """更新配置"""
    try:
        # 记录接收到的配置
        print(f"[API] 接收到配置更新请求: {configure}")
        
        # 验证配置
        if configure.SpeedThreshold is not None and not isinstance(configure.SpeedThreshold, (int, float)):
            return Response(
                RetCode=1,
                Message=f"SpeedThreshold 必须是数字类型，收到: {type(configure.SpeedThreshold)}"
            )
        
        # 更新配置
        global current_config
        prev_config = current_config
        current_config = configure
        if prev_config.WifiSSID != current_config.WifiSSID or prev_config.WifiPassword != current_config.WifiPassword:
            update_wifi()
        
        # 返回成功响应
        return Response(
            RetCode=0,
            Message="配置更新成功"
        )
    except Exception as e:
        # 记录详细错误信息
        print(f"[API] 配置更新失败: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # 返回失败响应
        return Response(
            RetCode=1,
            Message=f"配置更新失败：{str(e)}"
        )

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """启动 FastAPI 服务器"""
    uvicorn.run(app, host=host, port=port)
    
def update_wifi():
    os.system("nmcli connection modify wifi 802-11-wireless-security.leap-password \"{}\"".format(current_config.WifiPassword))
    os.system("nmcli connection modify wifi 802-11-wireless.ssid \"{}\"".format(current_config.WifiSSID))
    os.system("nmcli connection down wifi")
    os.system("nmcli connection up wifi")