# ─────────────────────────────────────────
# 全局配置
# ─────────────────────────────────────────

# Raspberry Pi 端配置
RASPBERRY_PI_API_HOST = "0.0.0.0"
RASPBERRY_PI_API_PORT = 8000
RASPBERRY_PI_SUBMIT_LOG_PATH = "/home/pi/Desktop/submit_log.xlsx" # 树莓派端日志路径

# Agent 端配置
OLLAMA_HOST = "http://192.168.43.105:11434" # Ollama 服务地址
OLLAMA_MODEL = "qwen3:4b" # 使用的模型
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/855587d0-6c3b-4c1e-a865-eb3ee8e7fea3" # 飞书 Webhook
MONITOR_INTERVAL = 5 # Agent 端轮询树莓派 API 的间隔（秒）

# 日志列名
LOG_COLUMNS = ["timestamp", "trigger", "analyzed_count", "anomaly_count", "threshold", "risk_level", "feishu_status"]

# ─────────────────────────────────────────
# 阈值配置 (Agent 端和 Raspberry Pi 端共享)
# ─────────────────────────────────────────
THRESHOLD_CONFIG = {
    "anomaly_count": 3,
    "auto_submit": True,
    "anomaly_ratio": 0.5,
}
