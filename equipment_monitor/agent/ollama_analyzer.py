import httpx
from typing import List, Dict

from .config import OLLAMA_HOST, OLLAMA_MODEL

class OllamaAnalyzer:
    def __init__(self):
        pass

    async def analyze_data(self, records_to_analyze: List[Dict], auto: bool = False):
        """
        使用 Ollama 分析设备数据。
        records_to_analyze: 待分析的设备记录列表。
        auto: 是否为自动触发的分析。
        """
        if not records_to_analyze:
            return {"status": "no_data", "message": "没有待分析数据"}

        data_str = "\n".join([
            f"[{r['时间戳']}] 电流:{r['电流(A)']}A, 温度:{r['温度(°C)']}°C, 振动:{r['振动(mm/s)']}mm/s, 状态:{r['状态']}"
            for r in records_to_analyze
        ])
        anomaly_count = sum(1 for r in records_to_analyze if r["状态"] == "异常")

        prompt = f"""你是一名工业设备维护专家。以下是设备最新采集的数据（共{len(records_to_analyze)}条，其中异常{anomaly_count}条）：

{data_str}

请给出：
1. 可能的故障原因
2. 建议处理措施
3. 风险等级（高/中/低）

用简洁中文回答，不超过300字。"""

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
                )
                response.raise_for_status()
                result = response.json()
                return {
                    "status": "ok",
                    "reply": result.get("response", "模型未返回内容"),
                    "analyzed_count": len(records_to_analyze),
                    "anomaly_count": anomaly_count,
                    "auto": auto
                }
        except httpx.ConnectError:
            return {"status": "error", "reply": f"❌ 无法连接Ollama ({OLLAMA_HOST})"}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "reply": f"❌ Ollama API 返回错误: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"status": "error", "reply": f"❌ 请求失败: {str(e)}"}

    async def chat_with_ollama(self, message: str):
        """
        与 Ollama 进行自由对话。
        """
        if not message:
            return {"status": "error", "reply": "消息不能为空"}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={"model": OLLAMA_MODEL, "prompt": f"你是工业设备维护专家助手，请用中文回答：{message}", "stream": False}
                )
                response.raise_for_status()
                result = response.json()
                return {"status": "ok", "reply": result.get("response", "")}
        except httpx.ConnectError:
            return {"status": "error", "reply": f"❌ 无法连接Ollama ({OLLAMA_HOST})"}
        except httpx.HTTPStatusError as e:
            return {"status": "error", "reply": f"❌ Ollama API 返回错误: {e.response.status_code} - {e.response.text}"}
        except Exception as e:
            return {"status": "error", "reply": f"❌ 请求失败: {str(e)}"}
