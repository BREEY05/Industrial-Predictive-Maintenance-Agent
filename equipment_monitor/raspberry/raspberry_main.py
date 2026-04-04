import threading
import uvicorn
import os

# 导入拆分后的模块
from . import data_simulator
from . import api_server

# ─────────────────────────────────────────
# 配置
# ─────────────────────────────────────────
API_HOST = "0.0.0.0"
API_PORT = 8000
SUBMIT_LOG_PATH = "/home/pi/Desktop/submit_log.xlsx" # 树莓派端日志路径

# 将 SUBMIT_LOG_PATH 传递给 data_simulator
data_simulator.SUBMIT_LOG_PATH = SUBMIT_LOG_PATH

# ─────────────────────────────────────────
# 启动 FastAPI 应用
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("🏭 工业设备预测性维护系统 - 树莓派端")
    print("=" * 50)
    print(f"📡 Web: http://0.0.0.0:{API_PORT}")
    print(f"📝 提交日志: {SUBMIT_LOG_PATH}")
    print("=" * 50)
    uvicorn.run(api_server.app, host=API_HOST, port=API_PORT)
