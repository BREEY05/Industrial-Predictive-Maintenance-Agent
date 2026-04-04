# 工业设备预测性维护智能体系统 - API 文档

本文档描述了工业设备预测性维护智能体系统中树莓派端 (Raspberry Pi) 提供的 RESTful API 接口。

## 基础信息

*   **树莓派 API 地址**：`http://<树莓派IP>:8000`
*   **内容类型**：`application/json`

---

## 1. 模拟数据输入

模拟生成一条设备数据并添加到内部记录中。如果达到自动提交阈值，将触发自动分析信号。

*   **URL**：`/api/simulate`
*   **方法**：`POST`
*   **请求体**：无
*   **响应**：
    *   `200 OK`
    ```json
    {
        "status": "ok",
        "data": {
            "时间戳": "2026-04-02 10:30:00",
            "电流(A)": 5.23,
            "温度(°C)": 65.12,
            "振动(mm/s)": 2.56,
            "状态": "正常"
        }
    }
    ```

---

## 2. 获取统计数据与最新记录

获取当前系统的总记录数、异常数、正常数、最新一条记录、最近10条记录以及待分析的异常数据数量和阈值配置。

*   **URL**：`/api/stats`
*   **方法**：`GET`
*   **请求体**：无
*   **响应**：
    *   `200 OK`
    ```json
    {
        "total": 100,
        "anomaly": 10,
        "normal": 90,
        "latest": {
            "时间戳": "2026-04-02 10:30:00",
            "电流(A)": 5.23,
            "温度(°C)": 65.12,
            "振动(mm/s)": 2.56,
            "状态": "正常"
        },
        "recent": [
            // 最近10条记录，按时间倒序
        ],
        "pending_count": 3,
        "pending_anomaly": 2,
        "threshold": {
            "anomaly_count": 3,
            "auto_submit": true,
            "anomaly_ratio": 0.5
        }
    }
    ```

---

## 3. 轮询自动提交结果

前端轮询此接口以获取 Agent 端自动分析的结果。

*   **URL**：`/api/poll_auto`
*   **方法**：`GET`
*   **请求体**：无
*   **响应**：
    *   `200 OK`
    *   如果有新的自动提交结果：
        ```json
        {
            "has_result": true,
            "status": "ok",
            "reply": "AI分析结果...",
            "analyzed_count": 5,
            "anomaly_count": 3,
            "auto": true
        }
        ```
    *   如果没有新的自动提交结果：
        ```json
        {
            "has_result": false
        }
        ```

---

## 4. 提交分析 (已废弃，由 Agent 端处理)

此接口在代码拆分后已不再直接执行分析，而是由电脑端的 Agent 负责轮询数据并进行分析。前端应调用此接口以触发 Agent 端的分析流程。

*   **URL**：`/api/analyze`
*   **方法**：`POST`
*   **请求体**：无
*   **响应**：
    *   `200 OK`
    ```json
    {
        "status": "error",
        "message": "分析功能已移至 Agent 端"
    }
    ```

---

## 5. 设置阈值配置

动态修改数据模拟和自动提交的阈值配置。

*   **URL**：`/api/set_threshold`
*   **方法**：`POST`
*   **请求体**：
    ```json
    {
        "anomaly_count": 5,   // 异常数阈值 (int)
        "auto_submit": false, // 是否开启自动提交 (boolean)
        "anomaly_ratio": 0.8  // 模拟数据异常概率 (float, 0-1)
    }
    ```
*   **响应**：
    *   `200 OK`
    ```json
    {
        "status": "ok",
        "threshold": {
            "anomaly_count": 5,
            "auto_submit": false,
            "anomaly_ratio": 0.8
        }
    }
    ```

---

## 6. AI 自由对话

与 Ollama 模型进行自由对话。

*   **URL**：`/api/chat`
*   **方法**：`POST`
*   **请求体**：
    ```json
    {
        "message": "你的问题" // 用户输入的消息 (string)
    }
    ```
*   **响应**：
    *   `200 OK`
    ```json
    {
        "status": "ok",
        "reply": "AI 的回复" // Ollama 模型的回复 (string)
    }
    ```
    *   `200 OK` (错误情况)
    ```json
    {
        "status": "error",
        "reply": "错误信息"
    }
    ```

---

## 7. 设置 Ollama IP

动态修改 Ollama 服务的 IP 地址。

*   **URL**：`/api/set_ollama`
*   **方法**：`GET`
*   **查询参数**：
    *   `ip` (string, 必需)：新的 Ollama 服务 IP 地址。
*   **响应**：
    *   `200 OK`
    ```json
    {
        "status": "ok",
        "ollama_host": "http://<新的IP>:11434"
    }
    ```

---

## 8. 仪表盘页面

Web 仪表盘主页面，用于实时监控设备数据和交互。

*   **URL**：`/`
*   **方法**：`GET`
*   **请求体**：无
*   **响应**：
    *   `200 OK` (HTML 页面)

---

*文档版本：v1.0*  
*最后更新：2026-04-02*
