import asyncio
from langchain_ollama import ChatOllama
import config

async def test_ollama():
    """测试Ollama连接和基本功能"""
    print("=" * 60)
    print("🧪 Ollama 连接测试")
    print("=" * 60)
    
    try:
        print(f"📍 尝试连接到 Ollama: {config.OLLAMA_BASE_URL}")
        print(f"🤖 使用模型: {config.OLLAMA_MODEL}")
        print()
        
        model = ChatOllama(
            model=config.OLLAMA_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=0.7
        )
        
        print("📤 发送测试消息...")
        response = await model.ainvoke("你好，请用一句话介绍你自己。")
        
        print("✅ Ollama 连接成功！")
        print()
        print("🤖 AI 回复:")
        print(f"   {response.content}")
        print()
        print("=" * 60)
        print("🎉 测试通过！Ollama 可以正常使用。")
        print("=" * 60)
        return True
        
    except Exception as e:
        print("❌ Ollama 连接失败！")
        print()
        print(f"错误信息: {e}")
        print()
        print("💡 请检查:")
        print("   1. Ollama 服务是否正在运行? (运行 'ollama serve')")
        print(f"   2. 模型 '{config.OLLAMA_MODEL}' 是否已下载? (运行 'ollama pull {config.OLLAMA_MODEL}')")
        print(f"   3. OLLAMA_BASE_URL 配置是否正确? (当前: {config.OLLAMA_BASE_URL})")
        print("=" * 60)
        return False

if __name__ == "__main__":
    asyncio.run(test_ollama())
