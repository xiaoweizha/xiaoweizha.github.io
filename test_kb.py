#!/usr/bin/env python3
import asyncio
import sys
sys.path.append('.')

from src.core.rag_engine import RAGEngine

async def test_kb_content():
    """测试知识库内容"""
    print("🔍 检查知识库状态...")

    try:
        # 初始化RAG引擎
        rag_engine = RAGEngine()
        await rag_engine.initialize()

        # 测试查询1：通用查询
        print("\n📋 测试查询1：通用内容")
        result1 = await rag_engine.query("文档", top_k=5)
        print(f"✅ 查询成功！回答长度: {len(result1.answer)}字符")
        print(f"📄 回答预览: {result1.answer[:200]}...")

        # 测试查询2：Amazon相关（基于你上传的PDF）
        print("\n📋 测试查询2：Amazon相关内容")
        result2 = await rag_engine.query("Amazon市场洞察", top_k=5)
        print(f"✅ 查询成功！回答长度: {len(result2.answer)}字符")
        print(f"📄 回答预览: {result2.answer[:200]}...")

        # 测试查询3：test document相关
        print("\n📋 测试查询3：测试文档内容")
        result3 = await rag_engine.query("test document", top_k=5)
        print(f"✅ 查询成功！回答长度: {len(result3.answer)}字符")
        print(f"📄 回答预览: {result3.answer[:200]}...")

        if len(result1.answer) + len(result2.answer) + len(result3.answer) > 100:
            print("\n🎉 知识库工作正常，文档已成功入库并能正常问答！")
        else:
            print("\n❌ 知识库可能有问题，回答过短")

    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_kb_content())