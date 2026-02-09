"""
书籍数据服务（Open Library 为主，豆瓣为补充）
"""
import asyncio
import logging
import httpx
from typing import List, Dict, Any, Optional

from app.services.douban_service import DoubanBookService

logger = logging.getLogger(__name__)


class BookDataService:
    """书籍数据服务（Open Library + 豆瓣）"""

    OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
    OPEN_LIBRARY_BOOK_URL = "https://openlibrary.org/works/{work_id}.json"
    OPEN_LIBRARY_COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

    def __init__(self):
        self.douban = DoubanBookService()

    async def search_books(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索书籍（超时 60 秒，失败时重试一次）"""
        last_err = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(
                        self.OPEN_LIBRARY_SEARCH_URL,
                        params={"q": query, "limit": limit},
                    )
                    response.raise_for_status()
                    data = response.json()
                    books = []
                    docs = data.get("docs", [])
                    print(f"    API 返回 {len(docs)} 条结果")
                    for doc in docs[:limit]:
                        book = await self._parse_book_data(doc)
                        if book:
                            books.append(book)
                        else:
                            print(f"    ⚠️  解析失败: {doc.get('title', 'N/A')}")
                    return books
            except (httpx.HTTPError, httpx.TimeoutException, Exception) as e:
                last_err = e
                print(f"    ⚠️  Open Library 请求失败 (尝试 {attempt + 1}/2): {e}")
                if attempt == 0:
                    await asyncio.sleep(2)
        print(f"    ❌ Open Library 重试后仍失败: {last_err}")
        raise last_err
    
    async def get_book_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """根据 ISBN 获取书籍"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.OPEN_LIBRARY_SEARCH_URL,
                params={"isbn": isbn},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("docs"):
                return await self._parse_book_data(data["docs"][0])
            return None
    
    async def _parse_book_data(self, doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析 Open Library 数据"""
        try:
            # 获取基本信息
            title = doc.get("title", "未知书名")
            author = ", ".join(doc.get("author_name", ["未知作者"])) if doc.get("author_name") else "未知作者"
            # 处理ISBN - 可能是列表或字符串
            isbn_list = doc.get("isbn", [])
            isbn = None
            if isinstance(isbn_list, list) and len(isbn_list) > 0:
                # 优先使用ISBN13，如果没有则使用第一个
                isbn = next((i for i in isbn_list if len(str(i)) == 13), isbn_list[0])
            elif isinstance(isbn_list, str):
                isbn = isbn_list
            
            # 如果没有ISBN，使用Open Library ID作为唯一标识
            if not isbn:
                isbn = doc.get("key", "").replace("/works/", "").replace("/books/", "")
            
            # 获取简介（可能需要额外请求）
            description = doc.get("first_sentence", [""])[0] if doc.get("first_sentence") else ""
            if not description:
                description = doc.get("subtitle", "")
            
            # 获取封面
            cover_id = doc.get("cover_i")
            cover_url = None
            if cover_id:
                cover_url = self.OPEN_LIBRARY_COVER_URL.format(cover_id=cover_id)
            
            # 获取出版社和出版日期
            publisher = ", ".join(doc.get("publisher", [])) if doc.get("publisher") else None
            publish_year = doc.get("first_publish_year")
            
            # 获取分类
            subject = doc.get("subject", [])
            category = subject[0] if subject else None
            
            # 获取页数
            page_count = doc.get("number_of_pages_median")
            
            return {
                "title": title,
                "author": author,
                "isbn": isbn,
                "description": description or "暂无简介",
                "cover_url": cover_url,
                "publisher": publisher,
                "publish_year": publish_year,
                "category": category,
                "page_count": page_count,
                "open_library_id": doc.get("key", "").replace("/works/", ""),
                "subject": subject[:5] if subject else []
            }
        except Exception as e:
            print(f"解析书籍数据错误: {e}")
            return None
    
    async def search_books_with_douban(
        self, query: str, limit: int = 20, use_douban: bool = True
    ) -> List[Dict[str, Any]]:
        """
        搜索书籍（Open Library + 豆瓣合并）
        对中文关键词会同时查豆瓣；若 Open Library 失败则回退到豆瓣
        """
        ol_books = []
        try:
            ol_books = await self.search_books(query, limit=limit)
        except Exception as e:
            logger.warning("Open Library 搜索失败: %s，尝试豆瓣", e)
            ol_books = []

        # 中文关键词时合并豆瓣；或 Open Library 无结果时用豆瓣兜底
        use_douban_for_merge = use_douban and (
            self._is_chinese_query(query) or len(ol_books) == 0
        )
        if use_douban_for_merge:
            try:
                douban_books = await self.douban.search_books(
                    query, start=0, count=min(limit, 25)
                )
                if douban_books:
                    seen = set()
                    for b in ol_books:
                        key = (b.get("isbn") or "") or f"{b.get('title','')}_{b.get('author','')}"
                        if key:
                            seen.add(key)
                    for b in douban_books:
                        key = (b.get("isbn") or "") or f"{b.get('title','')}_{b.get('author','')}"
                        if key and key not in seen:
                            seen.add(key)
                            ol_books.append(b)
                    ol_books.sort(
                        key=lambda x: (x.get("rating") or 0, bool(x.get("cover_url"))),
                        reverse=True,
                    )
                    ol_books = ol_books[:limit]
            except Exception as e:
                logger.debug("豆瓣搜索失败: %s", e)

        return ol_books

    def _is_chinese_query(self, query: str) -> bool:
        """简单判断是否为中文搜索"""
        return any("\u4e00" <= c <= "\u9fff" for c in query)

    async def enrich_with_douban(self, book_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        用豆瓣数据补充书籍信息（评分、封面、简介）
        有 ISBN 时按 ISBN 查，否则不补充
        """
        isbn = book_data.get("isbn")
        if not isbn or not str(isbn).replace("-", "").isdigit():
            return book_data
        try:
            douban_book = await self.douban.get_book_by_isbn(str(isbn))
            if douban_book:
                if douban_book.get("rating") and not book_data.get("rating"):
                    book_data["rating"] = douban_book["rating"]
                    book_data["rating_source"] = "douban"
                if douban_book.get("cover_url") and not book_data.get("cover_url"):
                    book_data["cover_url"] = douban_book["cover_url"]
                if (
                    douban_book.get("description")
                    and (not book_data.get("description") or book_data.get("description") == "暂无简介")
                ):
                    book_data["description"] = douban_book["description"]
                if douban_book.get("douban_id"):
                    book_data["douban_id"] = douban_book["douban_id"]
                await asyncio.sleep(0.5)  # 避免豆瓣限流
        except Exception as e:
            logger.debug("豆瓣补充失败: %s", e)
        return book_data

    async def get_douban_rating(self, isbn: str) -> Optional[float]:
        """根据 ISBN 获取豆瓣评分"""
        book = await self.douban.get_book_by_isbn(isbn)
        return book.get("rating") if book else None
