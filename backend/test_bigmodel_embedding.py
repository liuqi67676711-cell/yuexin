"""
測試智譜 Embedding-3 API 是否正常工作
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.embedding import EmbeddingService
from app.services.vector_db import VectorDBService
from app.core.config import settings


async def test_bigmodel_embedding():
    """測試智譜 Embedding API"""
    print("=" * 60)
    print("🔍 測試智譜 Embedding-3 API")
    print("=" * 60)
    print()
    
    # 檢查配置
    bigmodel_key = getattr(settings, "BIGMODEL_API_KEY", "") or ""
    print(f"📋 配置檢查:")
    print(f"   BIGMODEL_API_KEY: {'已配置' if bigmodel_key.strip() else '❌ 未配置'}")
    print(f"   BIGMODEL_EMBEDDING_MODEL: {getattr(settings, 'BIGMODEL_EMBEDDING_MODEL', 'embedding-3')}")
    print(f"   BIGMODEL_EMBEDDING_DIMENSIONS: {getattr(settings, 'BIGMODEL_EMBEDDING_DIMENSIONS', 1024)}")
    print()
    
    if not bigmodel_key.strip():
        print("⚠️  警告：未配置 BIGMODEL_API_KEY，將使用備用方案")
        print()
    
    # 初始化服務
    embedding_service = EmbeddingService()
    
    # 檢查使用的服務類型
    if embedding_service._use_bigmodel:
        print("✅ Embedding 服務已配置為使用智譜 BigModel Embedding-3")
        print(f"   API URL: {embedding_service._embed_url}")
        print(f"   模型: {embedding_service.model}")
        print(f"   維度: {embedding_service.dimensions}")
    elif embedding_service._use_openai:
        print("⚠️  Embedding 服務使用 OpenAI（未配置智譜 API Key）")
    else:
        print("⚠️  Embedding 服務使用本地模型（未配置任何 API Key）")
    print()
    
    # 測試單個文本的 embedding
    test_text = "最近工作壓力大，想看看輕鬆的推理小說"
    print(f"🧪 測試文本: \"{test_text}\"")
    print("   正在生成 embedding...")
    
    try:
        embedding = await embedding_service.get_embedding(test_text)
        
        if embedding:
            print(f"✅ Embedding 生成成功！")
            print(f"   向量長度: {len(embedding)}")
            print(f"   向量前5個值: {embedding[:5]}")
            print(f"   向量後5個值: {embedding[-5:]}")
            
            # 檢查維度是否符合預期
            expected_dim = embedding_service.dimensions if embedding_service._use_bigmodel else None
            if expected_dim and len(embedding) != expected_dim:
                print(f"⚠️  警告：向量維度 {len(embedding)} 與預期 {expected_dim} 不符")
            elif expected_dim:
                print(f"✅ 向量維度符合預期: {len(embedding)}")
        else:
            print("❌ Embedding 生成失敗：返回為空")
            
    except Exception as e:
        print(f"❌ Embedding 生成失敗：{e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("📊 檢查向量資料庫狀態")
    print("=" * 60)
    print()
    
    try:
        vector_db_service = VectorDBService()
        collection = vector_db_service.collection
        
        # 獲取集合中的向量數量
        count = collection.count()
        print(f"📚 向量資料庫中的書籍數量: {count}")
        
        if count > 0:
            # 獲取一個樣本向量來檢查維度
            results = collection.peek(limit=1)
            if results['embeddings'] and len(results['embeddings']) > 0:
                sample_embedding = results['embeddings'][0]
                sample_dim = len(sample_embedding)
                print(f"📏 樣本向量維度: {sample_dim}")
                
                # 檢查維度是否匹配
                if embedding_service._use_bigmodel:
                    expected_dim = embedding_service.dimensions
                    if sample_dim == expected_dim:
                        print(f"✅ 向量資料庫中的向量維度與智譜 Embedding-3 配置一致 ({expected_dim})")
                    else:
                        print(f"⚠️  警告：向量資料庫中的向量維度 ({sample_dim}) 與當前配置 ({expected_dim}) 不一致")
                        print(f"   這表示向量可能是用其他模型生成的")
                        print(f"   建議：刪除 chroma_db 目錄並重新初始化")
                else:
                    print(f"ℹ️  當前未使用智譜 API，無法判斷向量來源")
                
                # 顯示樣本書籍信息
                if results['metadatas'] and len(results['metadatas']) > 0:
                    sample_meta = results['metadatas'][0]
                    print(f"📖 樣本書籍: {sample_meta.get('title', 'N/A')}")
            else:
                print("⚠️  無法獲取樣本向量")
        else:
            print("⚠️  向量資料庫為空，需要運行初始化腳本")
            print("   執行: python scripts/init_books.py")
            
    except Exception as e:
        print(f"❌ 檢查向量資料庫失敗: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("✅ 測試完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_bigmodel_embedding())
