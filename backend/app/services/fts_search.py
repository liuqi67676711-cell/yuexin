"""
SQLite FTS（全文搜索）服务
用于精确搜索的性能优化：比 LIKE 查询快 10-100 倍
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from app.db.models import Book


class FTSSearchService:
    """SQLite FTS 全文搜索服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self._ensure_fts_table()
    
    def _ensure_fts_table(self):
        """确保 FTS 虚拟表存在（如果不存在则创建）"""
        try:
            # 检查 FTS 表是否存在
            result = self.db.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='books_fts'"
            )).fetchone()
            
            if not result:
                # 创建 FTS5 虚拟表（SQLite 3.9+ 支持）
                # FTS5 支持中文分词（需要编译时启用，但大多数 SQLite 版本都支持）
                self.db.execute(text("""
                    CREATE VIRTUAL TABLE books_fts USING fts5(
                        book_id UNINDEXED,
                        title,
                        author,
                        isbn,
                        description,
                        content='books',
                        content_rowid='id'
                    )
                """))
                
                # 填充 FTS 表（从 books 表同步数据）
                self.db.execute(text("""
                    INSERT INTO books_fts(book_id, title, author, isbn, description)
                    SELECT id, title, author, isbn, description FROM books
                """))
                
                # 创建触发器，保持 FTS 表与 books 表同步
                # INSERT 触发器
                self.db.execute(text("""
                    CREATE TRIGGER books_fts_insert AFTER INSERT ON books BEGIN
                        INSERT INTO books_fts(book_id, title, author, isbn, description)
                        VALUES (new.id, new.title, new.author, new.isbn, new.description);
                    END
                """))
                
                # UPDATE 触发器
                self.db.execute(text("""
                    CREATE TRIGGER books_fts_update AFTER UPDATE ON books BEGIN
                        UPDATE books_fts SET
                            title = new.title,
                            author = new.author,
                            isbn = new.isbn,
                            description = new.description
                        WHERE book_id = new.id;
                    END
                """))
                
                # DELETE 触发器
                self.db.execute(text("""
                    CREATE TRIGGER books_fts_delete AFTER DELETE ON books BEGIN
                        DELETE FROM books_fts WHERE book_id = old.id;
                    END
                """))
                
                self.db.commit()
                print("✅ FTS 全文搜索表已创建并同步数据")
        except Exception as e:
            # 如果 FTS5 不可用（旧版 SQLite），回退到普通 LIKE 搜索
            print(f"⚠️  FTS5 不可用: {e}，将使用普通 LIKE 搜索")
            self.db.rollback()
    
    def search(
        self,
        isbn: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        limit: int = 100
    ) -> List[Book]:
        """使用 FTS 全文搜索书籍"""
        try:
            # 构建 FTS 查询条件
            conditions = []
            params = {}
            
            if isbn:
                # ISBN 精确匹配优先
                conditions.append("isbn MATCH :isbn")
                params["isbn"] = f'"{isbn}"'  # 双引号表示精确匹配
            
            if title:
                # FTS5 支持中文分词，直接搜索即可
                # 使用 OR 连接多个词（空格分隔）
                title_terms = title.strip().split()
                title_query = " OR ".join([f'title:{term}' for term in title_terms])
                conditions.append(f"({title_query})")
            
            if author:
                author_terms = author.strip().split()
                author_query = " OR ".join([f'author:{term}' for term in author_terms])
                conditions.append(f"({author_query})")
            
            if not conditions:
                return []
            
            # 组合查询条件（用 AND 连接）
            where_clause = " AND ".join(conditions)
            
            # FTS 查询（使用 rank 排序，相关性高的在前）
            query = text(f"""
                SELECT DISTINCT b.*
                FROM books b
                INNER JOIN books_fts fts ON b.id = fts.book_id
                WHERE {where_clause}
                ORDER BY rank, b.rating DESC NULLS LAST
                LIMIT :limit
            """)
            
            params["limit"] = limit
            result = self.db.execute(query, params)
            rows = result.fetchall()
            
            # 转换为 Book 对象
            books = []
            for row in rows:
                book = Book(
                    id=row.id,
                    isbn=row.isbn,
                    title=row.title,
                    author=row.author,
                    publisher=row.publisher,
                    description=row.description,
                    cover_url=row.cover_url,
                    rating=row.rating,
                    category=row.category,
                    page_count=row.page_count,
                )
                books.append(book)
            
            return books
            
        except Exception as e:
            # 如果 FTS 查询失败，回退到普通 LIKE 查询
            print(f"⚠️  FTS 搜索失败: {e}，回退到普通搜索")
            return self._fallback_search(isbn, title, author, limit)
    
    def _fallback_search(
        self,
        isbn: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        limit: int = 100
    ) -> List[Book]:
        """回退到普通 LIKE 搜索（当 FTS 不可用时）"""
        from sqlalchemy import or_
        
        conditions = []
        if isbn:
            conditions.append(Book.isbn.contains(isbn))
        if title:
            conditions.append(Book.title.contains(title))
        if author:
            conditions.append(Book.author.contains(author))
        
        if not conditions:
            return []
        
        query = self.db.query(Book).filter(or_(*conditions))
        return query.limit(limit).all()
    
    def rebuild_fts_index(self):
        """重建 FTS 索引（当书籍数据更新后调用）"""
        try:
            # 清空 FTS 表
            self.db.execute(text("DELETE FROM books_fts"))
            
            # 重新填充
            self.db.execute(text("""
                INSERT INTO books_fts(book_id, title, author, isbn, description)
                SELECT id, title, author, isbn, description FROM books
            """))
            
            self.db.commit()
            print("✅ FTS 索引已重建")
        except Exception as e:
            print(f"⚠️  重建 FTS 索引失败: {e}")
            self.db.rollback()
