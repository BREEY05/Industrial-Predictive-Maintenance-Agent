# 工业设备预测性维护智能体系统

基于 **Ollama 本地大模型** 和 **FastAPI + 树莓派** 的轻量化工业设备预测性维护原型系统。

## 🎯 项目简介

这是一个完整的工业设备预测性维护系统原型，包含：
- **树莓派数据采集端**：模拟异常/正常数据输入 → Excel持久化 → FastAPI服务 → Web可视化界面。
- **电脑智能分析端**：Agent 轮询树莓派数据 → Ollama本地大模型分析 → 飞书告警推送。
- **Web可视化界面**：实时设备状态展示，支持阈值配置与自动提交。

## 📁 项目结构

```
equipment_monitor/
├── raspberry/                  # 树莓派端代码
│   ├── raspberry_main.py       # 树莓派主程序，启动 FastAPI 服务
│   ├── data_simulator.py       # 数据模拟和 Excel 存储
│   ├── api_server.py           # FastAPI Web 服务接口
│   └── requirements.txt        # 树莓派端 Python 依赖
├── agent/                      # 电脑端智能体代码
│   ├── agent_main.py           # 电脑端主程序，运行分析循环
│   ├── config.py               # 全局配置
│   ├── anomaly_detector.py     # 异常检测模块
│   ├── ollama_analyzer.py      # Ollama 分析模块
│   ├── feishu_notifier.py      # 飞书告警推送模块
│   └── requirements.txt        # 电脑端 Python 依赖
└── docs/                       # 文档
    ├── 部署指南.md             # 详细部署文档
    └── API文档.md              # API 接口文档
```

## 🚀 快速开始

### 1. 环境准备

#### 1.1 Python 环境

确保你的树莓派和电脑都安装了 Python 3.9+ 和 `pip`。

#### 1.2 Ollama 安装与模型下载 (仅限电脑端)

在你的电脑上：
1.  访问 [Ollama 官网](https://ollama.com/) 下载并安装 Ollama。
2.  安装完成后，拉取 `qwen3:4b` 模型：
    ```bash
    ollama pull qwen3:4b
    ```
3.  **重要**：确保 Ollama 服务监听所有网络接口，以便树莓派可以访问。
    在 Windows 上，可以设置环境变量 `OLLAMA_HOST="0.0.0.0:11434"`。
    在 Linux/macOS 上，可能需要修改 Ollama 的配置文件。

### 2. 配置

编辑 `equipment_monitor/agent/config.py` 文件，根据你的实际情况修改以下配置项：

```python
# equipment_monitor/agent/config.py

# Raspberry Pi 端配置
# RASPBERRY_PI_API_HOST 和 RASPBERRY_PI_API_PORT 通常不需要修改
# RASPBERRY_PI_SUBMIT_LOG_PATH 树莓派端 Excel 日志的保存路径

# Agent 端配置
OLLAMA_HOST = "http://<你的电脑IP>:11434"   # 替换为你的电脑的实际 IP 地址
OLLAMA_MODEL = "qwen3:4b"                  # Ollama 模型名称
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/你的飞书Webhook地址" # 替换为你的飞书群机器人 Webhook 地址
MONITOR_INTERVAL = 5                       # Agent 端轮询树莓派 API 的间隔（秒）
```

### 3. 依赖安装

#### 3.1 树莓派端

在树莓派上，进入 `equipment_monitor/raspberry` 目录，安装依赖：

```bash
cd /path/to/equipment_monitor/raspberry
pip install -r requirements.txt
```

#### 3.2 电脑端

在电脑上，进入 `equipment_monitor/agent` 目录，安装依赖：

```bash
cd /path/to/equipment_monitor/agent
pip install -r requirements.txt
```

### 4. 启动服务

#### 4.1 启动 Ollama 服务 (仅限电脑端)

确保 Ollama 服务已在电脑上运行。如果你设置了 `OLLAMA_HOST="0.0.0.0:11434"`，可以直接运行：

```bash
ollama serve
```

#### 4.2 启动树莓派端服务

在树莓派上，进入 `equipment_monitor/raspberry` 目录，运行主程序：

```bash
cd /path/to/equipment_monitor/raspberry
python raspberry_main.py
```

服务启动后，你可以在浏览器中访问 `http://<树莓派IP>:8000` 查看仪表盘。

#### 4.3 启动电脑端 Agent

在电脑上，进入 `equipment_monitor/agent` 目录，运行主程序：

```bash
cd /path/to/equipment_monitor/agent
python agent_main.py
```

Agent 将开始轮询树莓派 API，并在检测到异常时进行分析和告警。

## 🛠️ 技术栈

| 层级 | 技术选型 |
|------|---------|
| AI模型 | Ollama (qwen3:4b) 本地部署 |
| Web框架 | FastAPI + Uvicorn |
| 数据存储 | 内存 (运行时) + Excel (提交记录持久化) |
| 消息推送 | 飞书自定义机器人 Webhook |
| 硬件 | 树莓派5 |
| HTTP 客户端 | httpx |

## 📊 系统架构

```
[树莓派]
  数据模拟 (data_simulator.py)
  ↓
  FastAPI Web 服务 (api_server.py)
  ↑ ↓ HTTP/API
[电脑]
  Agent 主程序 (agent_main.py)
  ↓
  异常检测 (anomaly_detector.py)
  ↓
  Ollama AI 分析 (ollama_analyzer.py)
  ↓
  飞书告警推送 (feishu_notifier.py)
  ↓
[手机] 飞书接收告警
```

## 📝 功能特性

- ✅ **树莓派数据采集端**：模拟异常/正常数据输入，Excel 持久化存储。
- ✅ **Web 可视化仪表盘**：实时设备状态展示，支持阈值配置与自动提交。
- ✅ **电脑智能分析端**：Agent 轮询树莓派数据，实现异常检测。
- ✅ **Ollama 本地 AI 分析**：数据不出网，提供故障原因、处理措施和风险等级。
- ✅ **飞书机器人告警推送**：AI 分析完成后自动推送告警卡片到飞书群。
- ✅ **AI 自由对话面板**：Web 界面内置 AI 对话功能。
- ✅ **一键启动**：简化部署和运行流程。

## 🔧 配置说明

主要配置项在 `equipment_monitor/agent/config.py` 文件：

```python
# equipment_monitor/agent/config.py

# Raspberry Pi 端配置
RASPBERRY_PI_API_HOST = "0.0.0.0"
RASPBERRY_PI_API_PORT = 8000
RASPBERRY_PI_SUBMIT_LOG_PATH = "/home/pi/Desktop/submit_log.xlsx"

# Agent 端配置
OLLAMA_HOST = "http://<你的电脑IP>:11434"
OLLAMA_MODEL = "qwen3:4b"
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/你的飞书Webhook地址"
MONITOR_INTERVAL = 5

# 阈值配置
THRESHOLD_CONFIG = {
    "anomaly_count": 3,
    "auto_submit": True,
    "anomaly_ratio": 0.5,
}
```

## 📚 文档

- [部署指南.md](docs/部署指南.md) - 详细的部署和测试步骤
- [API文档.md](docs/API文档.md) - 树莓派端 API 接口文档
- [项目实施规划.md](工业设备预测性维护系统规划.md) - 详细的项目实施规划

## 🎓 后续优化方向

### 短期优化
- [ ] **真实传感器数据接入**：替换模拟数据为实际硬件采集数据。
- [ ] **历史数据图表展示**：在 Web 界面增加数据趋势图。
- [ ] **多设备监控支持**：扩展系统以支持同时监控多个设备。

### 长期优化
- [ ] **机器学习模型集成**：引入更高级的机器学习模型进行预测性分析。
- [ ] **云端部署**：支持将部分或全部服务部署到云平台。
- [ ] **移动端 App**：开发专属移动应用进行监控和告警。

## 📄 许可证

本项目仅供学习和研究使用。

---

*项目版本：v1.1*  
*最后更新：2026-04-02*
