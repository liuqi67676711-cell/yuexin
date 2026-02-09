"""
检查运行时错误 - 模拟真实的API调用
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_recommendation_api_real():
    """测试推荐API - 模拟真实调用"""
    print("=" * 50)
    print("测试推荐API（模拟真实调用）")
    print("=" * 50)
    
    try:
        from app.api.recommendation import semantic_recommendation, RecommendationRequest
        from app.db.database import SessionLocal
        
        db = SessionLocal()
        try:
            # 测试1: 情绪胶囊类型的查询
            print("\n测试1: 情绪查询")
            request = RecommendationRequest(query="周末独处，想找本温暖治愈的书")
            result = await semantic_recommendation(request, db, None)
            print(f"✅ 返回: {len(result.recommendations)} 个推荐")
            print(f"   消息: {result.message}")
            if result.recommendations:
                print(f"   第一个推荐: {result.recommendations[0].title}")
            
            # 测试2: 搜索类型的查询
            print("\n测试2: 搜索查询")
            request = RecommendationRequest(query="科幻小说")
            result = await semantic_recommendation(request, db, None)
            print(f"✅ 返回: {len(result.recommendations)} 个推荐")
            print(f"   消息: {result.message}")
            
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_vector_db():
    """测试向量数据库"""
    print("\n" + "=" * 50)
    print("测试向量数据库")
    print("=" * 50)
    
    try:
        from app.services.vector_db import VectorDBService
        from app.services.embedding import EmbeddingService
        
        vector_db_service = VectorDBService()
        embedding_service = EmbeddingService()
        
        # 检查集合
        count = vector_db_service.collection.count()
        print(f"📊 向量数据库中的书籍数量: {count}")
        
        if count == 0:
            print("⚠️  向量数据库为空！")
            print("   这意味着语义搜索无法工作，但会回退到热门书籍")
            print("   要填充向量数据库，请运行: bash init_data.sh")
        else:
            # 测试搜索
            print("\n测试向量搜索...")
            query_text = "科幻小说"
            embedding = await embedding_service.get_embedding(query_text)
            results = await vector_db_service.search_similar(embedding, top_k=3)
            print(f"✅ 搜索返回: {len(results)} 个结果")
            if results:
                print(f"   第一个结果: book_id={results[0].get('book_id')}")
    except Exception as e:
        print(f"❌ 向量数据库测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_vector_db()
    await test_recommendation_api_real()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
    print("\n💡 提示:")
    print("   如果向量数据库为空，推荐功能会使用热门书籍作为备选")
    print("   这不会导致500错误，但搜索结果可能不够精准")

if __name__ == "__main__":
    asyncio.run(main())
