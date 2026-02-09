"""
测试 Open Library API 连接
"""
import asyncio
import httpx


async def test_api():
    """测试 API 连接"""
    url = "https://openlibrary.org/search.json"
    
    try:
        async with httpx.AsyncClient() as client:
            print("测试 Open Library API 连接...")
            response = await client.get(
                url,
                params={"q": "science fiction", "limit": 5},
                timeout=30.0
            )
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                docs = data.get("docs", [])
                print(f"✅ 连接成功！获取到 {len(docs)} 条结果")
                
                if docs:
                    print("\n示例数据：")
                    first = docs[0]
                    print(f"  标题: {first.get('title', 'N/A')}")
                    print(f"  作者: {first.get('author_name', [])}")
                    print(f"  ISBN: {first.get('isbn', [])}")
                    print(f"  封面ID: {first.get('cover_i', 'N/A')}")
            else:
                print(f"❌ 错误: HTTP {response.status_code}")
                print(response.text[:200])
                
    except httpx.TimeoutException:
        print("❌ 连接超时！请检查网络连接")
    except httpx.ConnectError:
        print("❌ 无法连接到服务器！请检查网络连接或代理设置")
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    asyncio.run(test_api())
