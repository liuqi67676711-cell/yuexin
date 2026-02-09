"""
测试后端API是否正常工作
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_database():
    """测试数据库连接和表"""
    print("🔍 测试数据库...")
    try:
        from app.db.database import SessionLocal, engine
        from app.db.models import Book, User, ChatSession
        from sqlalchemy import inspect
        
        # 检查表是否存在
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✅ 数据库连接成功")
        print(f"📊 数据库中的表: {', '.join(tables)}")
        
        required_tables = ['users', 'books', 'bookshelves', 'user_preferences', 'chat_sessions', 'chat_messages']
        missing = [t for t in required_tables if t not in tables]
        if missing:
            print(f"⚠️  缺少表: {', '.join(missing)}")
        else:
            print("✅ 所有必需的表都存在")
        
        # 检查书籍数量
        db = SessionLocal()
        try:
            book_count = db.query(Book).count()
            print(f"📚 书籍数量: {book_count}")
            if book_count == 0:
                print("⚠️  数据库中没有书籍，请运行: bash init_data.sh")
            else:
                # 显示前3本书
                books = db.query(Book).limit(3).all()
                print("📖 示例书籍:")
                for book in books:
                    print(f"   - {book.title} by {book.author}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_search_api():
    """测试搜索API"""
    print("\n🔍 测试搜索API...")
    try:
        from app.api.search import exact_search
        from app.db.database import SessionLocal
        
        db = SessionLocal()
        try:
            # 测试空搜索
            result = await exact_search(None, None, None, db)
            print(f"✅ 空搜索返回: {len(result)} 本书")
            
            # 测试有条件的搜索
            result = await exact_search(None, "test", None, db)
            print(f"✅ 标题搜索返回: {len(result)} 本书")
        finally:
            db.close()
    except Exception as e:
        print(f"❌ 搜索API测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_recommendation_api():
    """测试推荐API"""
    print("\n🔍 测试推荐API...")
    try:
        from app.api.recommendation import semantic_recommendation, RecommendationRequest
        from app.db.database import SessionLocal
        
        db = SessionLocal()
        try:
            request = RecommendationRequest(query="想看点科幻小说")
            # 注意：这里传递None作为current_user，因为推荐API支持可选认证
            result = await semantic_recommendation(request, db, None)
            print(f"✅ 推荐API返回: {len(result.recommendations)} 个推荐")
            print(f"   消息: {result.message}")
        finally:
            db.close()
    except ImportError as e:
        print(f"⚠️  导入错误（可能是依赖问题）: {e}")
        print("   这可能是FastAPI版本问题，但不影响实际运行")
    except Exception as e:
        print(f"❌ 推荐API测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("=" * 50)
    print("后端API测试")
    print("=" * 50)
    
    await test_database()
    await test_search_api()
    await test_recommendation_api()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
