#!/usr/bin/env python3
"""
测试书籍数据源连通性（Open Library、豆瓣）
运行: python scripts/test_book_sources.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_open_library():
    """测试 Open Library API"""
    import httpx
    url = "https://openlibrary.org/search.json"
    print("测试 Open Library API...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url, params={"q": "science fiction", "limit": 3})
            r.raise_for_status()
            data = r.json()
            docs = data.get("docs", [])
            print(f"  ✅ 成功！返回 {len(docs)} 条结果")
            if docs:
                print(f"  示例: {docs[0].get('title', 'N/A')}")
    except httpx.TimeoutException:
        print("  ❌ 超时：无法在 30 秒内连接，可能是网络问题或需要代理")
    except httpx.ConnectError as e:
        print(f"  ❌ 连接失败: {e}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")


async def test_douban():
    """测试豆瓣 API"""
    import httpx
    import os
    from pathlib import Path
    # 加载 .env
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(env_path)
    except Exception:
        pass
    url = "https://api.douban.com/v2/book/search"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    params = {"q": "python", "count": 2}
    apikey = os.getenv("DOUBAN_API_KEY", "").strip()
    if apikey:
        params["apikey"] = apikey
        print("\n测试豆瓣 API（使用 DOUBAN_API_KEY）...")
    else:
        print("\n测试豆瓣 API...")
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            books = data.get("books", [])
            print(f"  ✅ 成功！返回 {len(books)} 条结果")
            if books:
                print(f"  示例: {books[0].get('title', 'N/A')}")
    except httpx.TimeoutException:
        print("  ❌ 超时（可能被墙，需代理）")
    except httpx.HTTPStatusError as e:
        print(f"  ❌ HTTP {e.response.status_code}")
        if e.response.status_code == 400:
            print("     豆瓣 API 可能已需 apikey，可在 .env 中配置 DOUBAN_API_KEY")
            print("     不影响使用：init_books 会回退到仅用 Open Library")
    except Exception as e:
        print(f"  ❌ 失败: {e}")


async def main():
    print("=" * 50)
    print("书籍数据源连通性测试")
    print("=" * 50)
    await test_open_library()
    await test_douban()
    print("\n" + "=" * 50)
    print("若 Open Library 失败，init_books 会尝试用豆瓣兜底")
    print("若两者均失败，请检查网络或使用代理")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
