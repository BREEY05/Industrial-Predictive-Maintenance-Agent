import threading
import random
import os
from datetime import datetime

import pandas as pd

# ─────────────────────────────────────────
# 配置 (部分配置项将从外部传入或在 config.py 中定义)
# ─────────────────────────────────────────
# SUBMIT_LOG_PATH = "/home/pi/Desktop/submit_log.xlsx" # 最终会从 config 中获取
LOG_COLUMNS = ["timestamp", "trigger", "analyzed_count", "anomaly_count", "threshold", "risk_level", "feishu_status"]

# ─────────────────────────────────────────
# 内存数据 & 阈值配置
# ─────────────────────────────────────────
data_lock = threading.Lock()
pending_records = [] # 待分析数据
all_records = []     # 所有历史数据

# 阈值配置，用于数据生成和自动提交判断
threshold_config = {
    "anomaly_count": 3,
    "auto_submit": True,
    "anomaly_ratio": 0.5,
}

# 自动提交结果队列（用于通知外部进行分析）
auto_submit_signal = threading.Event() # 用于通知外部有自动提交请求
auto_submitting = False  # 防止重复触发

# ─────────────────────────────────────────
# 数据生成
# ─────────────────────────────────────────
def generate_data():
    is_anomaly = random.random() < threshold_config["anomaly_ratio"]
    if is_anomaly:
        return {
            "时间戳": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "电流(A)": round(random.uniform(8.0, 15.0), 2),
            "温度(°C)": round(random.uniform(85.0, 120.0), 2),
            "振动(mm/s)": round(random.uniform(8.0, 20.0), 2),
            "状态": "异常"
        }
    else:
        return {
            "时间戳": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "电流(A)": round(random.uniform(3.0, 6.0), 2),
            "温度(°C)": round(random.uniform(40.0, 70.0), 2),
            "振动(mm/s)": round(random.uniform(1.0, 5.0), 2),
            "状态": "正常"
        }

def add_record():
    """
    生成一条新数据并添加到记录中。
    如果达到自动提交阈值，则设置自动提交信号。
    """
    global auto_submitting
    data = generate_data()
    with data_lock:
        all_records.append(data)
        if data["状态"] == "异常":
            pending_records.append(data)
        pending_anomaly = sum(1 for r in pending_records if r["状态"] == "异常")
        should_auto = (
            threshold_config["auto_submit"] and
            pending_anomaly >= threshold_config["anomaly_count"] and
            not auto_submitting
        )
        if should_auto:
            auto_submitting = True
            auto_submit_signal.set() # 设置信号，通知外部进行自动分析

    print(f"{'⚠️ 异常' if data['状态']=='异常' else '✅ 正常'} | {data['时间戳']} | 电流:{data['电流(A)']}A | 温度:{data['温度(°C)']}°C")

    if should_auto:
        print(f"🚨 阈值触发自动提交（异常数:{pending_anomaly}）")
    return data

def get_pending_records_for_analysis():
    """
    获取待分析的记录，并清空 pending_records。
    此函数应由外部（如 agent 端）调用。
    """
    with data_lock:
        if not pending_records:
            return None, 0, 0
        records_to_analyze = list(pending_records)
        pending_records.clear()
        anomaly_count = sum(1 for r in records_to_analyze if r["状态"] == "异常")
        return records_to_analyze, len(records_to_analyze), anomaly_count

def reset_auto_submitting_flag():
    """重置自动提交标志，允许再次触发自动提交"""
    global auto_submitting
    auto_submitting = False
    auto_submit_signal.clear() # 清除信号

def get_current_stats():
    """获取当前统计数据"""
    with data_lock:
        total = len(all_records)
        anomaly = sum(1 for r in all_records if r.get("状态") == "异常")
        latest = all_records[-1] if all_records else None
        recent = list(reversed(all_records[-10:]))
        pending_anomaly = sum(1 for r in pending_records if r["状态"] == "异常")
        pending_count = len(pending_records)
    return {
        "total": total,
        "anomaly": anomaly,
        "normal": total - anomaly,
        "latest": latest,
        "recent": recent,
        "pending_count": pending_count,
        "pending_anomaly": pending_anomaly,
        "threshold": threshold_config,
    }

def update_threshold_config(new_config: dict):
    """更新阈值配置"""
    if "anomaly_count" in new_config:
        threshold_config["anomaly_count"] = int(new_config["anomaly_count"])
    if "auto_submit" in new_config:
        threshold_config["auto_submit"] = bool(new_config["auto_submit"])
    if "anomaly_ratio" in new_config:
        v = float(new_config["anomaly_ratio"])
        threshold_config["anomaly_ratio"] = max(0.0, min(1.0, v))
    return threshold_config

# ─────────────────────────────────────────
# Excel 提交记录
# ─────────────────────────────────────────
log_lock = threading.Lock()

def extract_risk_level(reply: str) -> str:
    """从AI回复中提取风险等级"""
    for keyword in ["高", "中", "低"]:
        if f"风险等级：{keyword}" in reply or f"风险等级:{keyword}" in reply or f"风险：{keyword}" in reply:
            return keyword
    if "高风险" in reply or "高危" in reply:
        return "高"
    if "中风险" in reply or "中等" in reply:
        return "中"
    if "低风险" in reply:
        return "低"
    return "unknown"

def save_submit_log(result: dict, feishu_status: str, submit_log_path: str):
    """把每次提交记录写入Excel"""
    with log_lock:
        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "trigger": "auto" if result.get("auto") else "manual",
            "analyzed_count": result.get("analyzed_count", 0),
            "anomaly_count": result.get("anomaly_count", 0),
            "threshold": threshold_config["anomaly_count"],
            "risk_level": extract_risk_level(result.get("reply", "")),
            "feishu_status": feishu_status,
        }
        if os.path.exists(submit_log_path):
            try:
                df = pd.read_excel(submit_log_path)
            except Exception:
                df = pd.DataFrame(columns=LOG_COLUMNS)
        else:
            df = pd.DataFrame(columns=LOG_COLUMNS)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_excel(submit_log_path, index=False)
        print(f"📝 提交记录已保存: {row['trigger']} | risk:{row['risk_level']} | feishu:{feishu_status}")

# ─────────────────────────────────────────
# 自动提交结果队列（前端轮询取走）
# ─────────────────────────────────────────
auto_results_for_frontend = []
auto_results_for_frontend_lock = threading.Lock()

def add_auto_result_for_frontend(result: dict):
    """添加自动提交结果到队列，供前端轮询"""
    with auto_results_for_frontend_lock:
        auto_results_for_frontend.append(result)

def pop_auto_result_for_frontend():
    """从队列中取出自动提交结果，供前端轮询"""
    with auto_results_for_frontend_lock:
        if auto_results_for_frontend:
            return auto_results_for_frontend.pop(0)
    return None
