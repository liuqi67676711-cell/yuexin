"""
豆瓣图书 API 服务
文档：https://developers.douban.com/wiki/?title=book_v2
注意：近年可能需 apikey 才能访问，在 .env 中配置 DOUBAN_API_KEY 可尝试解决 400
"""
import logging
from typing import List, Dict, Any, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}


class DoubanBookService:
    """豆瓣图书 API 服务"""

    BASE_URL = "https://api.douban.com/v2/book"
    SEARCH_URL = "https://api.douban.com/v2/book/search"

    async def search_books(
        self, query: str, start: int = 0, count: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索图书
        :param query: 搜索关键词（书名、作者、ISBN 等）
        :param start: 起始位置
        :param count: 返回数量（最大 100）
        :return: 书籍列表，格式与 book_data 兼容
        """
        params = {"q": query, "start": start, "count": min(count, 100)}
        if getattr(settings, "DOUBAN_API_KEY", "") and str(settings.DOUBAN_API_KEY).strip():
            params["apikey"] = settings.DOUBAN_API_KEY.strip()
        try:
            async with httpx.AsyncClient(
                headers=DEFAULT_HEADERS, timeout=15.0
            ) as client:
                response = await client.get(self.SEARCH_URL, params=params)
                response.raise_for_status()
                data = response.json()

            books_raw = data.get("books", [])
            result = []
            for item in books_raw:
                parsed = self._parse_book(item)
                if parsed:
                    result.append(parsed)
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.warning("豆瓣 API 返回 400，可在 .env 中配置 DOUBAN_API_KEY 后重试")
            elif e.response.status_code == 403:
                logger.warning("豆瓣 API 返回 403，可能被限流或需代理")
            else:
                logger.warning("豆瓣 API HTTP 错误: %s %s", e.response.status_code, e.response.text[:200])
            return []
        except httpx.TimeoutException:
            logger.warning("豆瓣 API 请求超时")
            return []
        except Exception as e:
            logger.warning("豆瓣 API 请求失败: %s", e)
            return []

    async def get_book_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """
        根据 ISBN 获取图书详情
        :param isbn: ISBN-10 或 ISBN-13
        :return: 书籍信息，格式与 book_data 兼容
        """
        params = {}
        if getattr(settings, "DOUBAN_API_KEY", "") and str(settings.DOUBAN_API_KEY).strip():
            params["apikey"] = settings.DOUBAN_API_KEY.strip()
        try:
            async with httpx.AsyncClient(
                headers=DEFAULT_HEADERS, timeout=15.0
            ) as client:
                isbn_clean = str(isbn).replace("-", "").strip()
                url = f"{self.BASE_URL}/isbn/{isbn_clean}"
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            return self._parse_book(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.warning("豆瓣 ISBN 查询失败: %s", e.response.status_code)
            return None
        except Exception as e:
            logger.warning("豆瓣 ISBN 查询异常: %s", e)
            return None

    def _parse_book(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析豆瓣返回的数据为统一格式"""
        try:
            title = item.get("title") or item.get("alt_title", "")
            if not title:
                return None

            author = item.get("author", [])
            author_str = ", ".join(author) if isinstance(author, list) else str(author)

            rating_obj = item.get("rating", {})
            rating = None
            if isinstance(rating_obj, dict) and "average" in rating_obj:
                try:
                    rating = float(rating_obj["average"])
                except (TypeError, ValueError):
                    pass

            isbn = item.get("isbn13") or item.get("isbn") or ""

            return {
                "title": title,
                "author": author_str or None,
                "isbn": isbn or None,
                "description": item.get("summary", "").strip() or "暂无简介",
                "cover_url": self._get_large_cover(item.get("image")) if item.get("image") else None,
                "publisher": item.get("publisher"),
                "category": item.get("tags", [None])[0] if item.get("tags") else None,
                "page_count": self._parse_int(item.get("pages")),
                "rating": rating,
                "rating_source": "douban",
                "douban_id": str(item.get("id", "")),
                "open_library_id": None,
            }
        except Exception as e:
            logger.warning("解析豆瓣数据失败: %s", e)
            return None

    @staticmethod
    def _get_large_cover(url: str) -> str:
        """将豆瓣小图 URL 转为大图"""
        if not url:
            return ""
        return url.replace("/s/public/", "/l/public/").replace("/spic/", "/lpic/")

    @staticmethod
    def _parse_int(val: Any) -> Optional[int]:
        if val is None:
            return None
        try:
            return int(val)
        except (TypeError, ValueError):
            return None
