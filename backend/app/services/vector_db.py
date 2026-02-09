"""
向量数据库服务
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from app.core.config import settings


class VectorDBService:
    """向量数据库服务，使用 Chroma"""
    
    def __init__(self):
        # 禁用 ChromaDB telemetry 以避免错误
        import os
        os.environ["ANONYMIZED_TELEMETRY"] = "False"
        
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection_name = "books"
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """获取或创建集合"""
        try:
            return self.client.get_collection(name=self.collection_name)
        except:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "书籍向量数据库"}
            )
    
    async def add_book(
        self,
        book_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ):
        """添加书籍向量"""
        try:
            # 确保 metadata 中的值都是字符串或数字
            clean_metadata = {}
            for key, value in metadata.items():
                if value is None:
                    clean_metadata[key] = ""
                elif isinstance(value, (str, int, float)):
                    clean_metadata[key] = value
                else:
                    clean_metadata[key] = str(value)
            
            self.collection.add(
                ids=[str(book_id)],
                embeddings=[embedding],
                metadatas=[clean_metadata]
            )
        except Exception as e:
            # 如果向量数据库添加失败，记录错误但不抛出异常
            print(f"向量数据库添加失败 (book_id={book_id}): {e}")
            raise
    
    async def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似书籍"""
        try:
            where = filter_metadata if filter_metadata else None
            
            # 检查集合是否为空
            collection_count = self.collection.count()
            if collection_count == 0:
                print("⚠️  向量数据库为空，返回空结果")
                return []
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, collection_count),
                where=where
            )
            
            books = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i, book_id in enumerate(results["ids"][0]):
                    books.append({
                        "book_id": book_id,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0.0
                    })
            
            return books
        except Exception as e:
            print(f"⚠️  向量搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_book_by_id(self, book_id: str) -> Dict[str, Any]:
        """根据ID获取书籍向量"""
        results = self.collection.get(ids=[str(book_id)])
        if results["ids"]:
            return {
                "book_id": book_id,
                "metadata": results["metadatas"][0] if results["metadatas"] else {}
            }
        return None

    def get_embeddings_by_ids(self, book_ids: List[str]) -> Dict[str, List[float]]:
        """根据书籍ID列表获取对应的 embedding，返回 book_id -> embedding 映射"""
        if not book_ids:
            return {}
        try:
            ids_str = [str(bid) for bid in book_ids]
            results = self.collection.get(ids=ids_str, include=["embeddings"])
            out = {}
            if results.get("ids") and results.get("embeddings"):
                for i, bid in enumerate(results["ids"]):
                    emb = results["embeddings"][i]
                    if emb is not None:
                        out[str(bid)] = emb
            return out
        except Exception as e:
            print(f"⚠️  获取书籍 embedding 失败: {e}")
            return {}
