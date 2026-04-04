import httpx
import asyncio

from .config import RASPBERRY_PI_API_PORT, RASPBERRY_PI_API_HOST

class AnomalyDetector:
    def __init__(self, raspberry_pi_ip: str):
        self.raspberry_pi_ip = raspberry_pi_ip
        self.raspberry_pi_url = f"http://{self.raspberry_pi_ip}:{RASPBERRY_PI_API_PORT}"

    async def get_current_stats(self):
        """从树莓派端获取当前统计数据"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.raspberry_pi_url}/api/stats")
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            print(f"❌ 无法连接树莓派 API: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"❌ 树莓派 API 返回错误: {e.response.status_code} - {e.response.text}")
            return None

    async def check_for_anomaly_and_threshold(self):
        """
        检查树莓派端是否有待分析的异常数据，并判断是否达到自动提交阈值。
        返回 (should_analyze: bool, stats: dict)
        """
        stats = await self.get_current_stats()
        if not stats:
            return False, None

        pending_anomaly = stats.get("pending_anomaly", 0)
        threshold_config = stats.get("threshold", {})
        anomaly_count_threshold = threshold_config.get("anomaly_count", 0)
        auto_submit_enabled = threshold_config.get("auto_submit", False)

        should_analyze = (
            auto_submit_enabled and
            pending_anomaly >= anomaly_count_threshold
        )
        return should_analyze, stats

    async def get_pending_records_for_analysis(self):
        """
        从树莓派端获取待分析的记录。
        此接口在 `api_server.py` 中并未直接暴露，需要 Raspberry Pi 端提供。
        为了简化，这里假设 Agent 端可以直接访问 Raspberry Pi 端的内部数据，
        或者 Raspberry Pi 端提供一个专门的 API 来获取这些数据。
        目前，我们将通过 `/api/stats` 获取 pending_anomaly 数量，
        实际数据获取需要 Raspberry Pi 端提供新的 API。
        """
        # 这是一个占位符，实际需要 Raspberry Pi 端提供一个 API 来获取详细的待分析数据
        # 例如：response = await client.post(f"{self.raspberry_pi_url}/api/get_pending_data")
        # 目前，我们只能通过 stats 知道有多少待分析数据，但无法获取具体内容。
        # 在 Agent 端，我们将直接使用 Ollama 分析一个通用的提示，或者等待 Raspberry Pi 端提供数据。
        print("⚠️ 注意：Agent 端获取详细待分析数据的功能尚未实现，需要 Raspberry Pi 端提供相应 API。")
        return None # 暂时返回 None
