import asyncio
import json
from datetime import datetime
from typing import Dict, Any, TypedDict
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import random

import config

load_dotenv()

model = ChatOllama(
    model=config.OLLAMA_MODEL,
    base_url=config.OLLAMA_BASE_URL,
    temperature=0.7
)

class AgentState(TypedDict):
    equipment_data: Dict[str, Any]
    has_anomaly: bool
    analysis_result: str
    risk_level: str

def generate_mock_data():
    """生成模拟的设备数据（用于本地测试）"""
    has_anomaly = random.random() < 0.3  # 30%概率生成异常数据
    
    if has_anomaly:
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current": 1,
            "temperature": 75.5 + random.random() * 10,
            "vibration": 8.2 + random.random() * 5,
            "status": "异常"
        }
    else:
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current": 0,
            "temperature": 45.0 + random.random() * 10,
            "vibration": 2.5 + random.random() * 2,
            "status": "正常"
        }

async def get_equipment_data(state: AgentState) -> AgentState:
    """获取设备数据（本地测试版：使用模拟数据）"""
    data = generate_mock_data()
    state["equipment_data"] = data
    print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] 获取数据: {data}")
    return state

def detect_anomaly(state: AgentState) -> AgentState:
    """检测异常"""
    data = state.get("equipment_data", {})
    
    has_anomaly = False
    risk_level = "低"
    
    if data.get("current") == 1:
        has_anomaly = True
        risk_level = "高"
    elif data.get("temperature", 0) > 80:
        has_anomaly = True
        risk_level = "中"
    elif data.get("vibration", 0) > 10:
        has_anomaly = True
        risk_level = "中"
    
    state["has_anomaly"] = has_anomaly
    state["risk_level"] = risk_level
    
    if has_anomaly:
        print(f"⚠️  检测到异常！风险等级: {risk_level}")
    else:
        print("✅ 设备状态正常")
    
    return state

async def analyze_with_ai(state: AgentState) -> AgentState:
    """使用Ollama进行AI分析"""
    if not state.get("has_anomaly"):
        state["analysis_result"] = "设备运行正常"
        return state
    
    data = state.get("equipment_data", {})
    prompt = f"""作为工业设备维护专家，请分析以下设备数据：

设备数据：{json.dumps(data, ensure_ascii=False)}

请给出：
1. 可能的故障原因分析
2. 建议的处理措施
3. 预估风险等级

用简洁的中文回答，不超过200字。"""
    
    try:
        print("🤖 正在进行AI分析...")
        response = await model.ainvoke(prompt)
        state["analysis_result"] = response.content
        print("🤖 AI分析完成")
        print(f"分析结果: {response.content[:100]}...")
    except Exception as e:
        print(f"❌ AI分析失败: {e}")
        state["analysis_result"] = "AI分析暂不可用，请检查设备数据"
    
    return state

async def send_feishu_alert(state: AgentState) -> AgentState:
    """发送飞书告警（本地测试版：仅打印不发送）"""
    if not state.get("has_anomaly"):
        return state
    
    data = state.get("equipment_data", {})
    print(f"📱 [本地测试] 飞书告警消息:")
    print(f"   时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   风险等级：{state['risk_level']}")
    print(f"   分析结果：{state['analysis_result'][:80]}...")
    
    return state

def should_continue(state: AgentState) -> str:
    """判断是否需要继续处理"""
    if state.get("has_anomaly"):
        return "analyze"
    return END

def build_graph() -> StateGraph:
    """构建LangGraph"""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("get_data", get_equipment_data)
    workflow.add_node("detect", detect_anomaly)
    workflow.add_node("analyze", analyze_with_ai)
    workflow.add_node("alert", send_feishu_alert)
    
    workflow.set_entry_point("get_data")
    workflow.add_edge("get_data", "detect")
    workflow.add_conditional_edges(
        "detect",
        should_continue,
        {
            "analyze": "analyze",
            END: END
        }
    )
    workflow.add_edge("analyze", "alert")
    workflow.add_edge("alert", END)
    
    return workflow.compile()

async def monitor_loop():
    """监控主循环（本地测试版）"""
    print("=" * 60)
    print("🚀 智能体监控系统启动（本地测试模式）")
    print(f"🤖 Ollama模型: {config.OLLAMA_MODEL}")
    print(f"⏱️  监控间隔: {config.MONITOR_INTERVAL}秒")
    print("💡 提示：30%概率生成异常数据用于测试")
    print("=" * 60)
    
    graph = build_graph()
    
    while True:
        try:
            initial_state: AgentState = {
                "equipment_data": {},
                "has_anomaly": False,
                "analysis_result": "",
                "risk_level": "低"
            }
            await graph.ainvoke(initial_state)
        except Exception as e:
            print(f"❌ 监控循环异常: {e}")
        
        print(f"\n💤 等待 {config.MONITOR_INTERVAL} 秒...")
        print("-" * 60)
        await asyncio.sleep(config.MONITOR_INTERVAL)

if __name__ == "__main__":
    asyncio.run(monitor_loop())
