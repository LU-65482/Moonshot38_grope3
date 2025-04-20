import serial
import time

def parse_gprmc(data):
    try:
        if not data.startswith('$GPRMC'):
            return None
        parts = data.split(',')
        if len(parts) < 10 or parts[2] != 'A':
            return None
        lat = float(parts[3][:2]) + float(parts[3][2:])/60
        lon = float(parts[5][:3]) + float(parts[5][3:])/60
        if parts[4] == 'S': lat = -lat
        if parts[6] == 'W': lon = -lon
        return (lat, lon)
    except Exception as e:
        print("解析错误:", e)
        return None

# 使用未被系统占用的串口（如 /dev/ttyS3）
try:
    uart = serial.Serial('/dev/ttyS3', baudrate=9600, timeout=1)
    print("串口已连接，等待数据...")
except Exception as e:
    print(f"串口连接失败: {e}")
    exit()

try:
    while True:
        if uart.in_waiting > 0:
            raw_data = uart.read(uart.in_waiting())
            lines = raw_data.decode('utf-8', errors='ignore').split('\r\n')
            for line in lines:
                line = line.strip()
                if line:
                    print("原始数据:", line)
                    pos = parse_gprmc(line)
                    if pos:
                        print(f"纬度: {pos[0]:.6f}, 经度: {pos[1]:.6f}")
        time.sleep(0.1)
except KeyboardInterrupt:
    uart.close()
