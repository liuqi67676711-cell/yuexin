"""
初始化书籍数据脚本
从 Open Library API 获取热门书籍并导入数据库和向量数据库
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.db.models import Book
from app.services.book_data import BookDataService
from app.services.embedding import EmbeddingService
from app.services.vector_db import VectorDBService


async def init_books():
    """初始化书籍数据"""
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    book_data_service = BookDataService()
    embedding_service = EmbeddingService()
    vector_db_service = VectorDBService()
    
    # 热门搜索关键词（扩充至约 1000+ 本：优先中文书籍 + 外文书籍）
    popular_queries = [
        # ========== 中文书籍优先（70+个）==========
        # 中文文学经典与作者
        "chinese literature", "中文小说", "中国文学", "现代文学", "当代文学",
        "鲁迅", "茅盾", "巴金", "老舍", "沈从文",
        "莫言", "余华", "贾平凹", "路遥", "陈忠实",
        "张爱玲", "三毛", "亦舒", "琼瑶", "金庸",
        "古龙", "梁羽生", "温瑞安", "黄易", "倪匡",
        "苏童", "迟子建", "王安忆", "阎连科", "刘震云",
        "王小波", "汪曾祺", "钱钟书", "林语堂", "萧红",
        "张恨水", "史铁生", "毕飞宇", "格非", "阿城",
        "韩少功", "刘慈欣", "王朔", "严歌苓", "李碧华",
        "白先勇", "林清玄", "龙应台", "余秋雨", "周国平",
        # 中文非虚构
        "中国历史", "中国哲学", "中国文化", "中国艺术", "中国古典",
        "唐诗", "宋词", "元曲", "明清小说", "四大名著",
        "史记", "资治通鉴", "论语", "道德经", "孙子兵法",
        # 中文现代类别（推理类多列几条，便于「想看推理小说」有足够候选）
        "中文科幻", "中文悬疑", "中文推理", "推理小说", "悬疑小说", "东野圭吾", "阿加莎", "中文言情", "中文武侠",
        "中文散文", "中文诗歌", "中文传记", "中文游记", "中文随笔",
        # 中文专业书籍
        "中文经济", "中文管理", "中文心理", "中文教育", "中文科技",
        "中文医学", "中文法律", "中文建筑", "中文设计", "中文编程",
        # 中文工具类技术类书籍
        "Python 编程", "Java 编程", "JavaScript", "机器学习", "人工智能",
        "数据分析", "产品经理", "项目管理", "UI 设计", "用户体验",
        "Excel 教程", "办公软件", "PPT 制作", "写作技巧", "沟通表达",
        "投资理财", "股票基金", "摄影入门", "Photoshop", "视频剪辑",
        "运营手册", "市场营销", "创业指南", "时间管理", "高效学习",
        
        # ========== 外文书籍（50个）==========
        # 文学与小说类
        "science fiction", "romance", "mystery", "fantasy", "literature",
        "novel", "classic", "thriller", "horror", "comedy",
        "drama", "adventure", "crime", "detective", "historical fiction",
        "japanese literature", "british literature", "american literature", "russian literature",
        "french literature", "german literature", "spanish literature", "italian literature",
        # 非虚构类
        "history", "philosophy", "biography", "psychology", "self help",
        "business", "economics", "politics", "sociology", "anthropology",
        "journalism", "true crime", "war", "diplomacy", "culture",
        # 专业与兴趣类
        "travel", "cooking", "art", "poetry", "music",
        "science", "mathematics", "physics", "biology", "chemistry",
        "astronomy", "geology", "engineering", "medicine", "psychiatry",
        # 其他类别
        "children fiction", "young adult", "graphic novel", "essay", "memoir",
        "religion", "spirituality", "health", "fitness", "education",
        "parenting", "relationships", "motivation", "leadership", "creativity",
        "technology", "computer science", "design", "architecture", "photography",
    ]
    # 每类取约 25 本，100 类 × 25 ≈ 2500（去重后约 1200-1500，已有 365 本，继续新增）
    # 优先搜索中文书籍（前 50 个关键词），确保有足够的中文书籍
    books_per_query = 25
    target_total = 1000

    print(f"开始获取书籍数据（目标约 {target_total} 本）...")
    all_books = []

    for query in popular_queries:
        print(f"搜索: {query}")
        try:
            # 中文关键词同时查 Open Library + 豆瓣，合并结果
            use_douban = any("\u4e00" <= c <= "\u9fff" for c in query)
            books = await book_data_service.search_books_with_douban(
                query, limit=books_per_query, use_douban=use_douban
            )
            print(f"  -> 找到 {len(books)} 本书籍")
            if books:
                print(f"  -> 示例: {books[0].get('title', 'N/A')}")
            all_books.extend(books)
            await asyncio.sleep(1)  # 避免 Open Library 请求过快
            if use_douban:
                await asyncio.sleep(0.5)  # 豆瓣限流：单 IP 约 150 次/小时
        except Exception as e:
            print(f"搜索 {query} 失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n共获取 {len(all_books)} 本书籍（去重前）")
    
    # 去重（基于 ISBN 或 title+author）
    unique_books = {}
    books_with_isbn = 0
    books_without_isbn = 0
    
    for book in all_books:
        if book.get("isbn"):
            key = book["isbn"]
            books_with_isbn += 1
        else:
            # 如果没有ISBN，使用title+author作为key
            key = f"{book.get('title', '')}_{book.get('author', '')}"
            books_without_isbn += 1
        
        if key and key not in unique_books:
            unique_books[key] = book
    
    print(f"去重后: {len(unique_books)} 本书籍")
    print(f"  -> 有 ISBN: {books_with_isbn} 本")
    print(f"  -> 无 ISBN: {books_without_isbn} 本")
    
    # 保存到数据库并生成向量
    saved_count = 0
    error_count = 0
    skip_count = 0

    if len(unique_books) == 0:
        print("\n⚠️  警告：没有找到任何书籍数据！")
        print("可能的原因：")
        print("  1. 网络连接问题，无法访问 openlibrary.org 或豆瓣 API")
        print("  2. 若在中国大陆，可尝试使用代理/VPN 后重试")
        print("  3. API 返回的数据格式不符合预期")
        return
    
    print(f"\n开始保存 {len(unique_books)} 本书籍到数据库...")
    
    # 先检查数据库中现有书籍数量
    existing_count = db.query(Book).count()
    print(f"\n数据库中现有书籍数量: {existing_count}")
    
    if existing_count > 0:
        print("⚠️  数据库中已有书籍，将跳过重复的书籍")
        print("   如果想重新初始化，请先删除数据库文件：")
        print("   rm yuexin.db")
        print("   rm -rf chroma_db")
        print()
    
    for idx, (key, book_data) in enumerate(unique_books.items(), 1):
        try:
            # 检查是否已存在（通过ISBN或title+author）
            existing = None
            title = book_data.get("title", "").strip()
            author = book_data.get("author", "").strip() if book_data.get("author") else ""
            isbn = book_data.get("isbn")
            
            # 先通过ISBN查找
            if isbn:
                existing = db.query(Book).filter(Book.isbn == isbn).first()
            
            # 如果没找到，通过title+author查找
            if not existing and title:
                if author:
                    existing = db.query(Book).filter(
                        Book.title == title,
                        Book.author == author
                    ).first()
                else:
                    # 如果没有作者，只通过标题查找
                    existing = db.query(Book).filter(Book.title == title).first()
            
            if existing:
                skip_count += 1
                print(f"[{idx}/{len(unique_books)}] ⏭️  跳过已存在: {title[:40]}... (ID: {existing.id})")
                continue
            
            # 验证必要字段
            if not book_data.get("title"):
                print(f"[{idx}/{len(unique_books)}] 跳过：缺少书名")
                continue

            # 有 ISBN 时尝试用豆瓣补充评分、封面（可选，会稍慢）
            if book_data.get("isbn") and (not book_data.get("rating") or not book_data.get("cover_url")):
                try:
                    book_data = await book_data_service.enrich_with_douban(book_data)
                except Exception as e:
                    pass  # 补充失败不影响保存

            # 创建书籍记录
            book = Book(
                isbn=book_data.get("isbn") or None,
                title=book_data["title"],
                author=book_data.get("author") or None,
                publisher=book_data.get("publisher") or None,
                description=(book_data.get("description", "")[:1000] if book_data.get("description") else "") or None,
                cover_url=book_data.get("cover_url") or None,
                rating=book_data.get("rating"),
                rating_source=book_data.get("rating_source") or None,
                category=book_data.get("category") or None,
                page_count=book_data.get("page_count") or None,
                open_library_id=book_data.get("open_library_id") or None,
                douban_id=book_data.get("douban_id") or None,
            )
            db.add(book)
            db.commit()
            db.refresh(book)
            
            # 生成向量并保存到向量数据库
            # 使用书名 + 作者 + 简介作为向量化的文本
            text_for_embedding = f"{book.title} {book.author or ''} {book.description or ''}"
            if len(text_for_embedding.strip()) == 0:
                text_for_embedding = book.title  # 至少使用书名
            
            print(f"[{idx}/{len(unique_books)}] 生成向量: {book.title[:30]}...")
            try:
                embedding = await embedding_service.get_embedding(text_for_embedding)
                
                if not embedding or len(embedding) == 0:
                    print(f"  ⚠️  向量生成失败，跳过向量保存")
                else:
                    await vector_db_service.add_book(
                        book_id=str(book.id),
                        embedding=embedding,
                        metadata={
                            "title": book.title,
                            "author": book.author or "",
                            "isbn": book.isbn or "",
                            "category": book.category or "",
                        }
                    )
            except Exception as vec_error:
                print(f"  ⚠️  向量生成/保存失败: {vec_error}")
                # 向量失败不影响书籍保存，继续
            
            saved_count += 1
            print(f"  ✅ 已保存: {book.title} (ID: {book.id}, ISBN: {book.isbn or 'N/A'})")
            
            if saved_count % 10 == 0:
                print(f"\n📊 进度: {saved_count}/{len(unique_books)} 本书籍已处理\n")
            
        except Exception as e:
            error_count += 1
            error_msg = str(e)
            print(f"  ❌ [{idx}/{len(unique_books)}] 保存失败: {book_data.get('title', 'N/A')[:40]}")
            print(f"     错误: {error_msg}")
            
            # 只在前5个错误时打印详细堆栈
            if error_count <= 5:
                import traceback
                print(f"     详细错误:")
                traceback.print_exc()
            
            db.rollback()
            continue
    
    db.close()
    print(f"\n{'='*50}")
    print(f"✅ 完成！")
    print(f"   - 共保存: {saved_count} 本书籍")
    print(f"   - 跳过已存在: {skip_count}")
    print(f"   - 错误数: {error_count}")
    print(f"{'='*50}")

    if saved_count == 0:
        print("\n⚠️  没有保存任何书籍！")
        if skip_count > 0 and error_count == 0:
            print("\n📌 所有书籍都已存在于数据库中（共跳过 %d 本）" % skip_count)
            print("   若要重新初始化，请先删除数据库后重试：")
            print("   cd backend")
            print("   rm -f yuexin.db")
            print("   rm -rf chroma_db")
            print("   python scripts/init_books.py")
        elif error_count > 0:
            print("\n📌 保存过程中出现错误（共 %d 个）" % error_count)
            print("   可能原因：网络超时、向量生成失败等，请查看上方错误详情")
            print("   若在中国大陆，可尝试使用代理访问 Open Library")
        else:
            print("\n请检查：")
            print("1. 网络连接是否正常（需要访问 openlibrary.org 或豆瓣 API）")
            print("2. 查看上方的错误信息")
            print("3. 手动测试 Open Library：")
            print("   curl 'https://openlibrary.org/search.json?q=science+fiction&limit=5'")


if __name__ == "__main__":
    asyncio.run(init_books())
