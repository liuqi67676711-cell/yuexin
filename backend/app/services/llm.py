"""
LLM 服务
"""
import logging
import httpx
from typing import List, Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 服务：支持 OpenAI 与 DeepSeek 公开接口，未配置时使用内置简单回复"""
    
    def __init__(self):
        # 优先使用 DeepSeek，其次 OpenAI
        if getattr(settings, "DEEPSEEK_API_KEY", "") and str(settings.DEEPSEEK_API_KEY).strip():
            self.api_key = settings.DEEPSEEK_API_KEY.strip()
            self.base_url = getattr(settings, "DEEPSEEK_BASE_URL", "https://api.deepseek.com") or "https://api.deepseek.com"
            self.model = getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat") or "deepseek-chat"
            self._provider = "DeepSeek"
        elif getattr(settings, "OPENAI_API_KEY", "") and str(settings.OPENAI_API_KEY).strip():
            self.api_key = settings.OPENAI_API_KEY.strip()
            self.base_url = getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com") or "https://api.openai.com"
            self.model = getattr(settings, "OPENAI_MODEL", "gpt-3.5-turbo") or "gpt-3.5-turbo"
            self._provider = "OpenAI"
        else:
            self.api_key = ""
            self.base_url = ""
            self.model = ""
            self._provider = "mock"
        if self._provider == "mock":
            logger.warning("LLM 使用内置简单回复（未配置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY，请在 backend/.env 中配置）")
        else:
            logger.info("LLM 提供方: %s (model=%s)", self._provider, self.model)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        timeout: float = 10.0
    ) -> Tuple[str, bool]:
        """调用 LLM 生成回复。返回 (回复内容, 是否使用了内置兜底)。"""
        if not self.api_key:
            return (await self._mock_completion(messages), True)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url.rstrip('/')}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    timeout=60.0
                )
                if response.status_code != 200:
                    body = (response.text or "")[:500]
                    logger.warning(
                        "LLM API 返回非 200: status=%s, body=%s",
                        response.status_code, body
                    )
                    if response.status_code == 402:
                        logger.warning("DeepSeek 返回 402：账户需充值，请到 https://platform.deepseek.com 充值")
                    response.raise_for_status()
                data = response.json()
                content = (data.get("choices") or [{}])[0].get("message") or {}
                text = content.get("content")
                if text is None or (isinstance(text, str) and not text.strip()):
                    logger.warning("LLM API 返回的 content 为空: %s", data)
                    return (await self._mock_completion(messages), True)
                return (text if isinstance(text, str) else str(text), False)
        except httpx.HTTPStatusError as e:
            body = (e.response.text or "")[:500]
            logger.warning(
                "LLM API HTTP 错误（%s）: status=%s, body=%s",
                self._provider, e.response.status_code, body
            )
            return (await self._mock_completion(messages), True)
        except Exception as e:
            logger.warning(
                "LLM API 调用失败（%s），已回退到简单回复。错误: %s",
                self._provider, e, exc_info=True
            )
            return (await self._mock_completion(messages), True)
    
    async def test_api_call(self) -> dict:
        """发起一次真实 API 调用用于诊断（不落库）。返回 { ok, reply? | error?, status_code? }"""
        if not self.api_key:
            return {"ok": False, "error": "未配置 API Key（请在 backend/.env 中配置 DEEPSEEK_API_KEY）"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url.rstrip('/')}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己。"}],
                        "temperature": 0.7,
                        "max_tokens": 100
                    },
                    timeout=30.0
                )
                if response.status_code != 200:
                    body = (response.text or "")[:300]
                    if response.status_code == 402:
                        return {
                            "ok": False,
                            "error": "DeepSeek 返回 402 Payment Required，账户需充值。请到 https://platform.deepseek.com 充值后重试。",
                            "status_code": 402,
                            "response_body": body
                        }
                    return {
                        "ok": False,
                        "error": f"API 返回 {response.status_code}",
                        "status_code": response.status_code,
                        "response_body": body
                    }
                data = response.json()
                content = (data.get("choices") or [{}])[0].get("message") or {}
                reply = content.get("content") or ""
                return {"ok": True, "reply": (reply[:200] + "…") if len(reply) > 200 else reply, "provider": self._provider}
        except httpx.HTTPStatusError as e:
            body = (e.response.text or "")[:300]
            return {
                "ok": False,
                "error": str(e),
                "status_code": e.response.status_code,
                "response_body": body
            }
        except Exception as e:
            logger.exception("DeepSeek 诊断调用异常")
            return {"ok": False, "error": str(e)}
    
    def _parse_book_context(self, messages: List[Dict[str, str]]) -> tuple:
        """从 system 消息中解析书名、作者、简介（用于 mock 时生成更贴合的回复）"""
        title, author, desc = "", "", ""
        for m in messages:
            if m.get("role") != "system":
                continue
            content = m.get("content", "")
            if "当前讨论的书籍信息" not in content and "书名：" not in content:
                continue
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("书名："):
                    title = line.replace("书名：", "").strip()
                elif line.startswith("作者："):
                    author = line.replace("作者：", "").strip()
                elif line.startswith("简介："):
                    desc = line.replace("简介：", "").strip()
        return (title, author, desc)

    async def _mock_completion(self, messages: List[Dict[str, str]]) -> str:
        """模拟 LLM 回复（当没有 API Key 时）"""
        user_message = messages[-1].get("content", "") if messages else ""
        book_title, book_author, book_desc = self._parse_book_context(messages)
        
        # 获取对话历史上下文
        conversation_context = ""
        if len(messages) > 2:
            # 提取之前的对话（排除system和最后一条user消息）
            prev_messages = messages[:-1]
            conversation_context = " ".join([msg.get("content", "") for msg in prev_messages if msg.get("role") != "system"])
        
        # 更智能的回复生成
        if "推荐" in user_message or "推荐语" in user_message:
            return "这是一本值得一读的好书，它能够满足你的阅读需求，带来深刻的思考和愉悦的阅读体验。"
        elif "讲什么" in user_message or "内容" in user_message or "故事" in user_message:
            if book_title or book_author:
                intro = f"《{book_title}》" if book_title else "这本书"
                if book_author:
                    intro += f"是{book_author}的作品。"
                else:
                    intro += "是一本值得一读的作品。"
                return f"好呀，{intro}书中讲述了引人入胜的故事，探讨了深刻的主题，作者通过细腻的笔触和独特的视角为我们展现了一个充满想象力的世界。人物形象鲜明，情节跌宕起伏，值得细细品味。"
            return "这本书讲述了一个引人入胜的故事，探讨了深刻的主题。作者通过细腻的笔触和独特的视角，为我们展现了一个充满想象力的世界。书中的人物形象鲜明，情节跌宕起伏，值得细细品味。"
        elif "心情" in user_message or "情绪" in user_message or "压力" in user_message or "治愈" in user_message:
            return "我理解你的心情。这本书或许能够给你带来一些慰藉和启发。在阅读的过程中，你会发现自己逐渐从低落的情绪中走出来，重新感受到生活的美好和希望。"
        elif "作者" in user_message:
            return "这位作者以其独特的写作风格和深刻的洞察力而闻名。通过这本书，作者展现了对人性、社会和生活的深刻理解，值得我们去细细品味。"
        elif "主题" in user_message or "思想" in user_message:
            return "这本书探讨了深刻的人生主题，引发我们对生活、对世界的思考。作者通过故事的形式，向我们传达了一些重要的价值观和人生智慧。"
        elif "人物" in user_message or "角色" in user_message:
            return "书中的角色形象鲜明，性格各异。他们各自有着独特的经历和成长轨迹，通过他们的故事，我们可以看到人性的复杂和多样。"
        elif "结局" in user_message or "结尾" in user_message:
            return "这本书的结局令人深思，它不仅仅是一个故事的结束，更是对整本书主题的升华和总结。相信你在阅读后会有自己的理解和感悟。"
        elif "命运" in user_message or "人生" in user_message or "理想" in user_message or "你觉得" in user_message or "你怎么看" in user_message:
            return "这类问题很有意思。书里常常会折射出作者对命运和人生的看法，我们读的既是故事，也是对自己的追问。你可以先说说你读这本书时的感受，我们一起聊聊。"
        else:
            # 通用回复：像朋友聊天，不把问题推回用户
            if conversation_context:
                return f"嗯，你提到的这点我也很有同感。书和人生本来就是连在一起的，你有什么想法也可以继续说，我们一起聊。"
            else:
                return "我是苏童童，你的AI阅读伴侣。既可以聊这本书的内容，也可以聊从书里想到的人生、理想。你想从哪儿聊起？"
    
    async def extract_keywords(self, user_input: str) -> Dict[str, Any]:
        """从用户输入中提取关键词和情绪因子"""
        # 简单的关键词提取（当没有 API Key 时）
        if not self.api_key:
            keywords = []
            emotions = []
            scenarios = []
            book_types = []
            
            # 情绪关键词
            emotion_keywords = {
                "压力": "压力", "放松": "放松", "治愈": "治愈", "温暖": "温暖",
                "悲伤": "悲伤", "快乐": "快乐", "孤独": "孤独", "陪伴": "陪伴"
            }
            
            # 书籍类型关键词（含推理、悬疑等，便于「推理小说」等查询匹配）
            type_keywords = {
                "科幻": "科幻", "小说": "小说", "文学": "文学", "历史": "历史",
                "哲学": "哲学", "心理学": "心理学", "传记": "传记",
                "推理": "推理", "推理小说": "推理小说", "悬疑": "悬疑", "侦探": "侦探",
            }
            
            for word, emotion in emotion_keywords.items():
                if word in user_input:
                    emotions.append(emotion)
                    keywords.append(word)
            
            for word, book_type in type_keywords.items():
                if word in user_input:
                    book_types.append(book_type)
                    keywords.append(word)
            
            # 提取其他关键词
            words = user_input.split()
            keywords.extend([w for w in words if len(w) > 1 and w not in keywords])
            
            return {
                "keywords": keywords[:10],
                "emotions": emotions,
                "scenarios": [],
                "book_types": book_types
            }
        
        # 使用 LLM API
        prompt = f"""请分析以下用户输入，提取关键词和情绪因子。用户输入："{user_input}"

请以JSON格式返回：
{{
    "keywords": ["关键词1", "关键词2", ...],
    "emotions": ["情绪1", "情绪2", ...],
    "scenarios": ["场景1", "场景2", ...],
    "book_types": ["书籍类型1", "书籍类型2", ...]
}}"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的阅读推荐助手，擅长分析用户的需求和情绪。"},
            {"role": "user", "content": prompt}
        ]
        
        content, _ = await self.chat_completion(messages, temperature=0.3)
        response = content
        # 这里需要解析 JSON，简化处理
        import json
        try:
            # 尝试提取 JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # 如果解析失败，返回默认值
        return {
            "keywords": user_input.split(),
            "emotions": [],
            "scenarios": [],
            "book_types": []
        }
    
    async def generate_recommendation_text(
        self,
        user_input: str,
        book_title: str,
        book_author: str,
        book_description: str
    ) -> str:
        """生成推荐语（50-100字）"""
        # 如果没有 API Key，使用模板库生成推荐语
        if not self.api_key:
            from app.services.recommendation_templates import get_recommendation_template
            return get_recommendation_template(user_input, book_title, book_author, book_description)
            # 分析用户输入中的情绪关键词
            emotion_map = {
                "压力": "缓解压力", "放松": "带来放松", "治愈": "治愈心灵", "温暖": "带来温暖",
                "悲伤": "抚慰悲伤", "快乐": "带来快乐", "孤独": "陪伴孤独", "陪伴": "给予陪伴",
                "迷茫": "指引方向", "疲惫": "恢复精力", "焦虑": "平复焦虑", "低落": "提升心情"
            }
            
            # 提取情绪关键词
            detected_emotion = None
            for keyword, emotion_desc in emotion_map.items():
                if keyword in user_input:
                    detected_emotion = emotion_desc
                    break
            
            # 构建详细的推荐语（确保50-100字）
            book_desc_snippet = book_description[:80] if book_description else ""
            author_info = f"由{book_author}创作" if book_author else "这是一本"
            
            if detected_emotion:
                recommendation = f"当你感到{user_input[:15]}时，《{book_title}》或许正是你需要的。{author_info}的作品，{book_desc_snippet}。这本书能够{detected_emotion}，通过{book_title}中{book_desc_snippet[:30] if book_desc_snippet else '深刻的内容'}，为你带来心灵的慰藉和启发。相信在阅读的过程中，你会找到内心的平静与力量。"
            else:
                # 如果没有检测到特定情绪，根据用户输入生成
                user_needs = user_input[:20] if len(user_input) > 20 else user_input
                recommendation = f"如果你正在寻找{user_needs}，那么《{book_title}》或许正是你需要的。{author_info}的这部作品，{book_desc_snippet}。这本书不仅内容丰富、引人入胜，更能够满足你当前的阅读期待。通过{book_title}中{book_desc_snippet[:30] if book_desc_snippet else '深刻的故事和思考'}，相信会为你带来深刻的思考和愉悦的阅读体验，让你在阅读中找到共鸣与启发。"
            
            # 确保推荐语长度在50-100字之间
            if len(recommendation) < 50:
                recommendation += f"这本书值得你细细品味，相信会给你带来意想不到的收获和感悟。"
            elif len(recommendation) > 100:
                recommendation = recommendation[:97] + "..."
            
            return recommendation
        
        # 使用 LLM API - 优化prompt使其更简洁，加快响应速度
        desc_snippet = book_description[:200] if book_description else '暂无简介'
        prompt = f"""用户需求："{user_input}"

书籍：《{book_title}》{book_author and f'（{book_author}）' or ''}
简介：{desc_snippet}

生成50-100字推荐语，说明这本书如何满足用户需求。语言温暖有感染力，直接返回推荐语。"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的阅读推荐助手，擅长深度分析用户情绪，并根据情绪推荐合适的书籍。你的推荐语要温暖、具体、有针对性。"},
            {"role": "user", "content": prompt}
        ]
        
        # 优化：减少 max_tokens 以加快响应速度，同时保持推荐语质量
        content, _ = await self.chat_completion(messages, temperature=0.8, max_tokens=200)
        return content.strip()
    
    async def generate_agent_response(
        self,
        user_message: str,
        book_context: str = "",
        conversation_history: List[Dict[str, str]] = None,
        session_summary: str = "",
        user_interests: List[str] = None
    ) -> Tuple[str, bool]:
        """生成 AI 书童回复。返回 (回复内容, 是否使用了内置兜底未走 DeepSeek)。"""
        system_prompt = """你是"苏童童"，一个温暖、智慧、有思想的AI阅读伴侣。你不仅是介绍书的助手，更是可以一起聊书、聊人生、聊理想的伙伴。

你的能力与风格：
1. **介绍书**：当用户问「这本书讲了什么」「主要内容」「简介」时，根据「当前讨论的书籍信息」用 2～4 段话给出具体、有内容的介绍。
2. **聊书**：围绕书的主题、人物、结局、隐喻等，和用户深入讨论，表达你的理解和看法。
3. **聊人生与理想**：当用户问「你觉得…」「你怎么看…」「人类的命运」「人生」等开放式、思辨类问题时，要认真回答，发表你的思考，而不是把问题推回给用户。可以结合当前讨论的书籍主题来谈，也可以就问题本身真诚交流。
4. 用亲切、自然的语气，像一位爱读书的朋友在聊天；避免套路式回复如「如果你有具体的问题，我很乐意解答」——用户就是在和你聊天，请直接参与对话。"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if book_context:
            messages.append({
                "role": "system",
                "content": f"当前讨论的书籍信息：{book_context}"
            })
        
        if session_summary:
            messages.append({
                "role": "system",
                "content": f"之前对话摘要（供延续话题参考）：{session_summary}"
            })
        
        if user_interests:
            interests_str = "、".join(user_interests[:10])
            messages.append({
                "role": "system",
                "content": f"用户曾关注或提及：{interests_str}"
            })
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_message})
        
        # 提高 max_tokens，便于大模型返回更完整的介绍
        content, used_fallback = await self.chat_completion(messages, temperature=0.7, max_tokens=1024)
        return (content.strip(), used_fallback)

    async def generate_session_summary(
        self, messages_text: List[str]
    ) -> Dict[str, Any]:
        """生成会话摘要与关键主题。返回 {"summary": str, "key_topics": [...]}"""
        if not messages_text:
            return {"summary": "", "key_topics": []}
        conv = "\n".join(messages_text[-20:])  # 最近 20 条
        prompt = f"""请根据以下对话，生成 1～2 句简洁摘要，并提取用户提到的书名、作者、阅读相关主题。
若无明显主题则 key_topics 为空数组。

对话记录：
{conv}

请严格输出 JSON 格式，不要其他文字：
{{"summary": "摘要内容", "key_topics": ["主题1", "主题2"]}}"""
        try:
            if not self.api_key:
                return {"summary": "", "key_topics": []}
            content, _ = await self.chat_completion(
                [{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
                timeout=8.0
            )
            import json
            text = content.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            data = json.loads(text)
            return {
                "summary": (data.get("summary") or "").strip(),
                "key_topics": data.get("key_topics") or []
            }
        except Exception as e:
            logger.warning("生成会话摘要失败: %s", e)
            return {"summary": "", "key_topics": []}

    async def generate_popular_reason(
        self,
        title: str,
        author: str = "",
        description: str = "",
        rating: float = None
    ) -> str:
        """生成热门推荐理由（20-40字）"""
        # 如果没有 API Key，生成详细的推荐理由
        if not self.api_key:
            # 根据书籍描述和评分生成更具体的推荐理由
            desc_keywords = []
            if description:
                if "科幻" in description or "未来" in description:
                    desc_keywords.append("科幻")
                if "爱情" in description or "情感" in description:
                    desc_keywords.append("情感")
                if "历史" in description:
                    desc_keywords.append("历史")
                if "哲学" in description or "思考" in description:
                    desc_keywords.append("思考")
            
            # 构建推荐理由
            reason_parts = []
            
            if rating and rating >= 8.0:
                reason_parts.append(f"豆瓣评分{rating:.1f}分")
            elif rating and rating >= 7.0:
                reason_parts.append(f"评分{rating:.1f}分")
            
            if desc_keywords:
                reason_parts.append(f"探讨{desc_keywords[0]}主题")
            elif description:
                # 从描述中提取关键词
                desc_snippet = description[:30].replace("。", "").replace("，", "")
                if desc_snippet:
                    reason_parts.append(f"讲述{desc_snippet}")
            
            if author:
                reason_parts.append(f"{author}的经典作品")
            
            # 组合推荐理由
            if reason_parts:
                reason = "，".join(reason_parts) + "，深受读者喜爱"
            else:
                reason = f"内容引人入胜，值得细细品味"
            
            # 确保长度在20-40字之间
            if len(reason) < 20:
                reason += "，是值得一读的好书"
            elif len(reason) > 40:
                reason = reason[:37] + "..."
            
            return reason
        
        # 使用 LLM API
        rating_text = f"{rating:.1f}分（满分10分）" if rating else "暂无评分"
        prompt = f"""书籍信息：
- 书名：{title}
- 作者：{author}
- 简介：{description[:200] if description else '暂无简介'}
- 评分：{rating_text}

请生成一段20-40字的推荐理由，说明为什么大家都在看这本书。要：
1. 简洁有力，突出书籍的核心价值
2. 可以提及评分、内容特色、读者关注点等
3. 语气亲切自然

直接返回推荐理由，不要其他说明文字。"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的阅读推荐助手，擅长用简洁的语言说明书籍的推荐理由。"},
            {"role": "user", "content": prompt}
        ]
        
        content, _ = await self.chat_completion(messages, temperature=0.7, max_tokens=100)
        return content.strip()
