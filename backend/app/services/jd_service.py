"""
京东图书 API 服务（占位）
京东开放平台需要企业资质和 API Key 申请：https://open.jd.com
暂无公开免 Key 接口。
如需接入，请在 .env 中配置：
  JD_APP_KEY=your_app_key
  JD_APP_SECRET=your_app_secret
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class JDBookService:
    """京东图书 API 服务（需 API Key 后实现）"""

    def __init__(self):
        # 从配置读取，暂无 Key 时禁用
        self.enabled = False
        logger.info("京东图书 API 未配置 Key，已禁用。配置 JD_APP_KEY 后生效。")

    async def search_books(
        self, query: str, start: int = 0, count: int = 20
    ) -> List[Dict[str, Any]]:
        """搜索图书（需配置 API Key 后实现）"""
        if not self.enabled:
            return []
        # TODO: 实现京东商品搜索 API 调用
        return []

    async def get_book_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """根据 ISBN 获取图书（需配置 API Key 后实现）"""
        if not self.enabled:
            return None
        return None
