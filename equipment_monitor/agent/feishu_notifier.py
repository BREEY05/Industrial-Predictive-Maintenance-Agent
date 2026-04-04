import httpx
from datetime import datetime

from .config import FEISHU_WEBHOOK

class FeishuNotifier:
    def __init__(self):
        pass

    async def send_feishu_notification(self, result: dict):
        """
        发送飞书告警通知。
        result: 包含分析结果的字典。
        """
        if not FEISHU_WEBHOOK:
            print("⚠️ 未配置飞书 Webhook，跳过推送。")
            return "skipped"

        reply = result.get("reply", "")
        analyzed = result.get("analyzed_count", 0)
        anomaly = result.get("anomaly_count", 0)
        trigger = "🚨 自动触发" if result.get("auto") else "📤 手动提交"

        # 截取前200字防止消息太长
        short_reply = reply[:200] + "..." if len(reply) > 200 else reply

        msg = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"⚠️ 工业设备异常告警 {trigger}"},
                    "template": "red"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": f"**分析数据：** {analyzed} 条（异常 {anomaly} 条）"}
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": f"**AI分析结果：**\n{short_reply}"}
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": f"**时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
                    }
                ]
            }
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(FEISHU_WEBHOOK, json=msg)
                resp.raise_for_status()
                print(f"📱 飞书推送: {resp.status_code} {resp.text[:100]}")
                return "ok"
        except httpx.RequestError as e:
            print(f"❌ 飞书推送失败: {e}")
            return "error"
        except httpx.HTTPStatusError as e:
            print(f"❌ 飞书 API 返回错误: {e.response.status_code} - {e.response.text}")
            return "error"
        except Exception as e:
            print(f"❌ 飞书推送失败: {e}")
            return "error"
