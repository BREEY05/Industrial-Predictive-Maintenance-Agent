import asyncio
import time
import threading

from .config import MONITOR_INTERVAL, RASPBERRY_PI_API_PORT, RASPBERRY_PI_API_HOST, RASPBERRY_PI_SUBMIT_LOG_PATH
from .anomaly_detector import AnomalyDetector
from .ollama_analyzer import OllamaAnalyzer
from .feishu_notifier import FeishuNotifier
from ..raspberry import data_simulator # 导入 raspberry 端的 data_simulator 来使用 save_submit_log

class AgentMain:
    def __init__(self, raspberry_pi_ip: str):
        self.anomaly_detector = AnomalyDetector(raspberry_pi_ip)
        self.ollama_analyzer = OllamaAnalyzer()
        self.feishu_notifier = FeishuNotifier()
        self.raspberry_pi_ip = raspberry_pi_ip

    async def run_analysis_loop(self):
        print(f"Agent 端启动，监控树莓派 IP: {self.raspberry_pi_ip}，轮询间隔: {MONITOR_INTERVAL} 秒")
        while True:
            # 检查是否有自动提交信号
            if data_simulator.auto_submit_signal.is_set():
                print("🚨 收到自动提交信号，开始分析...")
                await self.perform_analysis(auto=True)
                data_simulator.reset_auto_submitting_flag() # 重置信号和标志
            
            # 也可以定期检查，以防信号丢失
            # should_analyze, stats = await self.anomaly_detector.check_for_anomaly_and_threshold()
            # if should_analyze:
            #     print("🚨 达到阈值，开始分析...")
            #     await self.perform_analysis(auto=True)

            await asyncio.sleep(MONITOR_INTERVAL)

    async def perform_analysis(self, auto: bool = False):
        """执行一次完整的分析流程"""
        # 从树莓派获取待分析数据
        # 注意：这里需要 Raspberry Pi 端提供一个 API 来获取详细的待分析数据
        # 暂时我们假设可以直接从 data_simulator 获取（仅用于测试，实际部署需通过 API）
        records_to_analyze, analyzed_count, anomaly_count = data_simulator.get_pending_records_for_analysis()

        if not records_to_analyze:
            print("⚠️ 没有待分析数据。")
            return

        print(f"开始分析 {analyzed_count} 条数据 (异常 {anomaly_count} 条)...")
        
        # 调用 Ollama 进行分析
        analysis_result = await self.ollama_analyzer.analyze_data(records_to_analyze, auto=auto)
        
        if analysis_result["status"] == "ok":
            print(f"✅ Ollama 分析完成。回复: {analysis_result['reply'][:100]}...")
            
            # 推送飞书告警
            feishu_status = await self.feishu_notifier.send_feishu_notification(analysis_result)
            print(f"📱 飞书推送状态: {feishu_status}")

            # 保存提交日志 (使用 raspberry 端的 save_submit_log)
            data_simulator.save_submit_log(analysis_result, feishu_status, RASPBERRY_PI_SUBMIT_LOG_PATH)

            # 将结果添加到前端轮询队列
            data_simulator.add_auto_result_for_frontend(analysis_result)
        else:
            print(f"❌ Ollama 分析失败: {analysis_result['reply']}")

async def main():
    # 假设树莓派的 IP 地址是固定的，或者通过命令行参数传入
    raspberry_pi_ip = "127.0.0.1" # 默认本地，实际部署时需修改
    # raspberry_pi_ip = "192.168.43.105" # 示例 IP

    agent = AgentMain(raspberry_pi_ip)
    await agent.run_analysis_loop()

if __name__ == "__main__":
    asyncio.run(main())
