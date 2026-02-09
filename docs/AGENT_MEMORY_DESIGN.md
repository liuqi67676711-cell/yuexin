# AI 书童记忆机制技术方案

> 结合四层记忆架构与阅心实际场景，提出的增强版记忆设计

---

## 一、设计目标

1. **阅读兴趣向量**：从书架 + 对话中提取用户阅读偏好，用于个性化推荐与回复
2. **跨 session 摘要**：长对话结束时生成 1～2 句摘要，下次进入时注入 system prompt
3. **记忆衰减/过期**：为不同类型记忆设定 TTL 或权重衰减，避免陈年偏好主导行为

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户画像层 (User Profile)                       │
│  基础信息、身份标签、使用习惯、阅读偏好向量（书架+对话提取）            │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   偏好设置层 (Preference Settings)                 │
│  交互风格、回复格式、语言偏好、书童名称 (agent_name)                  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   上下文记忆层 (Context Memory)                    │
│  对话历史（滑动窗口 10 条）、会话摘要、话题关联、时序信息              │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   知识索引层 (Knowledge Index)                     │
│  用户提及的书名/作者/主题、专业领域、关注点、记忆衰减权重              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、数据模型设计

### 3.1 新增/扩展表结构

#### 表 1：`user_reading_profile`（用户阅读画像）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 外键 → users.id |
| interest_vector | JSON | 阅读兴趣向量 [float]，与书籍向量同维（1024） |
| interest_source | String | 来源：bookshelf \| chat_extracted |
| last_updated | DateTime | 最后更新时间 |
| created_at | DateTime | 创建时间 |

- **interest_vector**：由书架书籍 embedding 加权平均得到；或由对话中提及的书名/作者 embedding 融合
- 每个 user 可保留一条记录，每次书架/对话变化时增量更新

#### 表 2：`chat_session_summaries`（会话摘要）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| session_id | Integer | 外键 → chat_sessions.id |
| summary | Text | 1～2 句摘要内容 |
| key_topics | JSON | 提及的书名/作者/主题列表 ["三体", "刘慈欣", "科幻"] |
| message_count | Integer | 生成摘要时的消息条数 |
| created_at | DateTime | 创建时间 |

- 每个 session 一条摘要，在对话结束（用户关闭/超时）或达到 N 轮后异步生成

#### 表 3：`user_interest_facts`（用户兴趣事实 / 知识索引）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| user_id | Integer | 外键 → users.id |
| fact_type | String | book_title \| author \| topic \| genre |
| fact_value | String | 具体值，如 "三体"、"刘慈欣"、"科幻" |
| source_session_id | Integer | 来源会话（可选） |
| weight | Float | 权重 0～1，用于衰减 |
| last_mentioned_at | DateTime | 最近提及时间 |
| expires_at | DateTime | 过期时间（可选） |
| created_at | DateTime | 创建时间 |

- 从对话中抽取：书名、作者、主题、领域
- **记忆衰减**：`weight` 随 `last_mentioned_at` 间隔衰减；或 `expires_at` 到期后软删除/降权

#### 表 4：扩展 `chat_sessions`

| 新增字段 | 类型 | 说明 |
|----------|------|------|
| summary_id | Integer | 外键 → chat_session_summaries.id，nullable |
| has_summary | Boolean | 是否已生成摘要 |

---

## 四、核心流程

### 4.1 阅读兴趣向量

```
触发时机：
  - 用户添加/移除书架书籍
  - 用户与书童对话中提及书名/作者（抽取后）
  - 定时任务（如每日）增量更新

流程：
  1. 收集数据源：书架 bookshelf 中的 book_id + user_interest_facts 中 fact_type=book_title 关联的书籍
  2. 从 vector_db 获取各 book_id 的 embedding
  3. 加权平均：想读=0.3, 在读=0.6, 已读=1.0；弃读=-0.2
  4. 归一化后写入 user_reading_profile.interest_vector
```

**与推荐系统联动**：`popular.py` 中的个性化推荐已使用书架向量，可将 `user_reading_profile.interest_vector` 作为补充，与书架 embedding 融合后用于相似度检索。

### 4.2 跨 session 摘要

```
触发时机：
  - 用户关闭 AgentChatModal（前端调用 POST /api/agent/sessions/{id}/summarize）
  - 会话消息数达到阈值（如 10 条）且距上次摘要超过 5 分钟

流程：
  1. 取 session 下最近 N 条消息（如 20）
  2. 调用 LLM：输入为消息列表，输出格式为 JSON
     {
       "summary": "用户喜欢科幻，讨论了《三体》结局与 AI 伦理。",
       "key_topics": ["三体", "刘慈欣", "科幻", "AI伦理"]
     }
  3. 写入 chat_session_summaries
  4. 将 key_topics 中未出现的条目插入/更新 user_interest_facts
```

**下次进入对话时**：若该 session 有摘要，在 `generate_agent_response` 的 system prompt 中注入：

```
之前的对话摘要：{summary}
用户曾提及：{key_topics}
```

### 4.3 知识索引与抽取

```
抽取时机：
  - 每次 chat 请求返回后，异步任务分析 user_message + agent_message

抽取方式（二选一）：
  A. 规则 + 关键词：匹配《》内书名、常见作者名、预设主题词
  B. LLM 抽取：小模型/轻量 prompt 输出结构化 JSON

写入 user_interest_facts：
  - fact_type: book_title | author | topic
  - fact_value: 具体值
  - weight: 1.0（新），已存在则 last_mentioned_at 更新，weight 根据衰减公式调整
  - expires_at: created_at + 90 天（可配置）
```

### 4.4 记忆衰减策略

| 记忆类型 | 衰减策略 | 参数 |
|----------|----------|------|
| user_interest_facts | 时间衰减 | 每 30 天 weight × 0.9，低于 0.1 则归档/忽略 |
| user_interest_facts | 过期删除 | expires_at 到期后标记为 inactive |
| chat_session_summaries | 不衰减 | 永久保留，供「回顾」功能使用 |
| 上下文滑动窗口 | 固定窗口 | 维持现有 10 条 |

---

## 五、API 设计

### 5.1 新增接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/agent/sessions/{session_id}/summarize | 触发会话摘要生成（幂等） |
| GET | /api/agent/users/me/profile | 获取当前用户阅读画像（供前端展示） |
| POST | /api/agent/users/me/profile/refresh | 手动刷新阅读兴趣向量 |

### 5.2 修改现有接口

| 接口 | 修改点 |
|------|--------|
| POST /api/agent/chat | 成功后触发：1）异步抽取 user_interest_facts；2）若消息数达阈值，触发 summarize |
| GET /api/agent/sessions/{id}/messages | 若有 summary，在响应中附带 summary 字段 |

---

## 六、实现优先级与分阶段计划

### Phase 1（最小可行）

1. 新增 `chat_session_summaries` 表
2. 实现 `POST /sessions/{id}/summarize`，用 LLM 生成摘要
3. 在 `generate_agent_response` 中，若 session 有 summary，注入到 system prompt

### Phase 2

1. 新增 `user_interest_facts` 表
2. 在 chat 成功后异步抽取 fact（规则或轻量 LLM）
3. 在推荐/对话时读取 `user_interest_facts`，注入「用户曾关注：xxx」

### Phase 3

1. 新增 `user_reading_profile` 表
2. 实现阅读兴趣向量计算（书架 + interest_facts）
3. 与 `popular.py`、`recommendation.py` 对接，增强个性化

### Phase 4

1. 实现记忆衰减任务（定时 job 或惰性计算）
2. 前端「我的阅读画像」展示
3. 优化抽取 prompt、衰减参数调优

---

## 七、技术依赖与约束

| 项目 | 说明 |
|------|------|
| Embedding | 复用现有 `EmbeddingService`（智谱/OpenAI/本地） |
| Vector DB | 复用 Chroma `books` 集合；如需用户向量可新增 `user_interests` 集合 |
| LLM | 复用 `LLMService.chat_completion`，摘要/抽取可用 temperature=0.3 |
| 异步任务 | 可选：FastAPI BackgroundTasks，或 Celery/Redis 若已有队列 |

---

## 八、风险与缓解

| 风险 | 缓解 |
|------|------|
| LLM 摘要/抽取延迟 | 异步执行，不阻塞主流程 |
| 抽取噪音（误判书名等） | 规则预过滤 + 置信度阈值 |
| 存储与算力成本 | 衰减策略控制规模；摘要仅保留最近 N 个 session |
| 隐私 | 所有数据按 user_id 隔离；不对外暴露原始对话 |

---

## 九、附录：LLM Prompt 示例

### 会话摘要 Prompt

```
请根据以下对话，生成 1～2 句简洁摘要，并提取用户提到的书名、作者、主题。

对话记录：
{messages}

输出 JSON 格式：
{"summary": "摘要内容", "key_topics": ["主题1", "主题2", ...]}
```

### 知识抽取 Prompt（可选）

```
从下面这句用户消息中，抽取其提到的书名（《》内）、作者名、阅读相关主题。
若无则返回空数组。

用户消息：{user_message}

输出 JSON：{"books": [], "authors": [], "topics": []}
```
