"""
Embedding 服务：优先智谱 BigModel Embedding-3，其次 OpenAI，未配置时使用本地 sentence-transformers
"""
import asyncio
import logging
from typing import List
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

# 本地模型缓存：未配置任何 API 时使用
_cached_model = None


def _get_model():
    """同步获取或加载本地模型（在线程中调用）"""
    global _cached_model
    if _cached_model is not None:
        return _cached_model
    from sentence_transformers import SentenceTransformer
    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    _cached_model = SentenceTransformer(model_name)
    return _cached_model


def _encode_sync(text: str) -> List[float]:
    """同步编码（本地模型），不阻塞事件循环"""
    try:
        model = _get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except ImportError:
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        vector = [float(b) / 255.0 * 2 - 1 for b in hash_bytes] * (384 // len(hash_bytes) + 1)
        return vector[:384]
    except Exception:
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        vector = [float(b) / 255.0 * 2 - 1 for b in hash_bytes] * (384 // len(hash_bytes) + 1)
        return vector[:384]


class EmbeddingService:
    """Embedding 服务：优先 BigModel Embedding-3，其次 OpenAI，否则本地 sentence-transformers"""

    def __init__(self):
        bigmodel_key = getattr(settings, "BIGMODEL_API_KEY", "") or ""
        openai_key = getattr(settings, "OPENAI_API_KEY", "") or ""
        self._use_bigmodel = bool(bigmodel_key.strip())
        self._use_openai = not self._use_bigmodel and bool(openai_key.strip())

        if self._use_bigmodel:
            self.api_key = bigmodel_key.strip()
            self.base_url = (getattr(settings, "BIGMODEL_EMBEDDING_BASE_URL", "https://open.bigmodel.cn") or "https://open.bigmodel.cn").rstrip("/")
            self.model = getattr(settings, "BIGMODEL_EMBEDDING_MODEL", "embedding-3") or "embedding-3"
            dim = getattr(settings, "BIGMODEL_EMBEDDING_DIMENSIONS", 1024)
            self.dimensions = dim if dim in (256, 512, 1024, 2048) else 1024
            self._embed_url = f"{self.base_url}/api/paas/v4/embeddings"
            logger.info("Embedding 使用智谱 BigModel: model=%s, dimensions=%s", self.model, self.dimensions)
        elif self._use_openai:
            self.api_key = openai_key.strip()
            self.base_url = (getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com") or "https://api.openai.com").rstrip("/")
            self.model = getattr(settings, "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small") or "text-embedding-3-small"
            self.dimensions = None
            self._embed_url = f"{self.base_url}/v1/embeddings"
            logger.info("Embedding 使用 OpenAI: model=%s", self.model)
        else:
            self.api_key = ""
            self._embed_url = ""
            self.model = ""
            self.dimensions = None
            logger.info("Embedding 使用本地 sentence-transformers（未配置 BIGMODEL_API_KEY / OPENAI_API_KEY）")

    async def get_embedding(self, text: str) -> List[float]:
        """获取单个文本的 embedding"""
        if self._use_bigmodel:
            return await self._get_embedding_bigmodel(text)
        if self._use_openai:
            return await self._get_embedding_openai(text)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _encode_sync, text)

    async def _get_embedding_bigmodel(self, text: str) -> List[float]:
        """调用智谱 BigModel Embedding-3 API"""
        if not text or not text.strip():
            text = " "
        body = {"model": self.model, "input": text[:8191]}
        if self.dimensions is not None:
            body["dimensions"] = self.dimensions
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._embed_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                emb = (data.get("data") or [{}])[0].get("embedding")
                if not emb:
                    raise ValueError("BigModel 返回的 embedding 为空")
                return list(emb)
        except httpx.HTTPStatusError as e:
            logger.warning("BigModel Embedding API 错误: %s %s", e.response.status_code, e.response.text[:200])
            raise
        except Exception as e:
            logger.warning("BigModel Embedding 请求失败: %s", e)
            raise

    async def _get_embedding_openai(self, text: str) -> List[float]:
        """调用 OpenAI Embeddings API"""
        if not text or not text.strip():
            text = " "
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._embed_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"model": self.model, "input": text[:8191]},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                emb = (data.get("data") or [{}])[0].get("embedding")
                if not emb:
                    raise ValueError("OpenAI 返回的 embedding 为空")
                return list(emb)
        except httpx.HTTPStatusError as e:
            logger.warning("OpenAI Embedding API 错误: %s %s", e.response.status_code, e.response.text[:200])
            raise
        except Exception as e:
            logger.warning("OpenAI Embedding 请求失败: %s", e)
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量获取 embeddings"""
        if not texts:
            return []
        if self._use_bigmodel:
            return await self._get_embeddings_bigmodel(texts)
        if self._use_openai:
            return await self._get_embeddings_openai(texts)
        return [await self.get_embedding(t) for t in texts]

    async def _get_embeddings_bigmodel(self, texts: List[str]) -> List[List[float]]:
        """BigModel 单次最多 64 条，超过则分批请求"""
        inputs = [t[:8191] if t and t.strip() else " " for t in texts]
        all_embeddings = []
        batch_size = 64
        for i in range(0, len(inputs), batch_size):
            batch = inputs[i : i + batch_size]
            body = {"model": self.model, "input": batch}
            if self.dimensions is not None:
                body["dimensions"] = self.dimensions
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self._embed_url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json=body,
                        timeout=60.0,
                    )
                    response.raise_for_status()
                    data = response.json()
                    items = sorted((data.get("data") or []), key=lambda x: x.get("index", 0))
                    all_embeddings.extend([list(item["embedding"]) for item in items if "embedding" in item])
            except Exception as e:
                logger.warning("BigModel 批量 Embedding 第 %d 批失败: %s，该批回退逐条", i // batch_size + 1, e)
                for t in texts[i : i + len(batch)]:
                    all_embeddings.append(await self.get_embedding(t))
        return all_embeddings

    async def _get_embeddings_openai(self, texts: List[str]) -> List[List[float]]:
        """OpenAI 批量"""
        inputs = [t[:8191] if t and t.strip() else " " for t in texts]
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._embed_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"model": self.model, "input": inputs},
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
                items = sorted((data.get("data") or []), key=lambda x: x.get("index", 0))
                return [list(item["embedding"]) for item in items if "embedding" in item]
        except Exception as e:
            logger.warning("OpenAI 批量 Embedding 失败，回退逐条: %s", e)
            return [await self.get_embedding(t) for t in texts]
