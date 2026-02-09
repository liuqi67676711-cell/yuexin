import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import UnifiedSearch from '../components/UnifiedSearch'
import RecommendationCard from '../components/RecommendationCard'
import BookDetailModal from '../components/BookDetailModal'
import AgentChatModal from '../components/AgentChatModal'
import { RecommendationItem } from '../api/recommendation'
import { booksAPI, Book } from '../api/books'
import { popularAPI, BookWithReason } from '../api/popular'
import { bookshelfAPI } from '../api/bookshelf'
import { showToast } from '../components/ToastContainer'
import ConfirmDialog from '../components/ConfirmDialog'
import BookCoverPlaceholder from '../components/BookCoverPlaceholder'
import { Sparkles, TrendingUp, X, ArrowUp, RefreshCw } from 'lucide-react'

const INSPIRATION_CAPSULES = [
  { emoji: '☕️', text: '周末独处，想找本温暖治愈的书' },
  { emoji: '💔', text: '最近心情低落，需要一些治愈' },
  { emoji: '🚀', text: '想看点脑洞大开的科幻小说' },
  { emoji: '🌙', text: '深夜了，读点轻松的吧' },
  { emoji: '💡', text: '工作压力大，想放松一下' },
  { emoji: '📚', text: '想深入了解某个历史时期' },
  { emoji: '🎭', text: '想看一些引人深思的文学作品' },
  { emoji: '🌊', text: '心情烦躁，需要平静下来' },
  { emoji: '🔥', text: '想要一些刺激的悬疑推理小说' },
  { emoji: '🌸', text: '春天来了，想读点浪漫的故事' },
  { emoji: '❄️', text: '冬天窝在被子里，想看温暖的故事' },
  { emoji: '🌅', text: '清晨醒来，想找本有启发的书' },
  { emoji: '🌆', text: '下班路上，想听个轻松的故事' },
  { emoji: '🎨', text: '想了解艺术和美的哲学' },
  { emoji: '🧠', text: '想提升自己的认知和思维' },
  { emoji: '💼', text: '职场迷茫，需要一些指导' },
  { emoji: '❤️', text: '想读一些关于爱情和人生的书' },
  { emoji: '🌟', text: '想要一些能激励自己的书' },
  { emoji: '🔮', text: '对未来感到好奇，想看科幻' },
  { emoji: '🏔️', text: '想逃离现实，去另一个世界' },
  { emoji: '🌿', text: '想要一些自然和生活的感悟' },
  { emoji: '🎪', text: '心情不错，想看些有趣的书' },
  { emoji: '🦋', text: '想要一些关于成长和蜕变的故事' },
  { emoji: '🌌', text: '夜晚思考人生，想看哲学书' },
  { emoji: '🎯', text: '想学习一些实用的技能和方法' },
  { emoji: '🌈', text: '想要一些色彩丰富、想象力丰富的书' },
  { emoji: '🕯️', text: '想要一些温暖人心的故事' },
  { emoji: '⚡', text: '想要一些快节奏、紧张刺激的书' },
  { emoji: '🌺', text: '想要一些关于美好生活的书' },
  { emoji: '🔍', text: '想探索一些未知的领域和知识' },
]

const CAPSULES_PER_PAGE = 8 // 每次显示8个胶囊

// 根据书籍标题和描述推断情绪/需求分类（返回所有匹配的分类）
function inferCategories(book: BookWithReason): string[] {
  const title = (book.title || '').toLowerCase()
  const desc = (book.description || '').toLowerCase()
  const reason = (book.reason || '').toLowerCase()
  const text = `${title} ${desc} ${reason}`
  
  // 情绪/需求分类关键词映射（大幅扩展关键词，提高匹配率）
  const categoryKeywords: Record<string, string[]> = {
    '求抱抱～': [
      // 治愈相关
      '治愈', '温暖', '安慰', '慰藉', '疗愈', '治愈系', '温暖人心', '治愈心灵', 
      '温柔', '温馨', '暖心', '抚慰', '安抚', '关怀', '理解', '共情', '陪伴',
      '温情', '温情脉脉', '温柔', '暖心', '安慰', '慰藉', '疗愈', '安抚',
      // 情感相关
      '感动', '感人', '触动', '打动', '温暖', '温情', '温柔', '柔和',
      '爱', '爱情', '亲情', '友情', '情感', '感情', '情', '爱意',
      // 生活相关
      '生活', '日常', '平凡', '简单', '朴实', '真实', '真诚', '真挚',
      '家', '家庭', '家人', '故乡', '家乡', '回忆', '怀念', '思念'
    ],
    '暴躁上线': [
      // 悬疑推理
      '悬疑', '推理', '犯罪', '谋杀', '惊悚', '恐怖', '刺激', '紧张', '激烈',
      '侦探', '破案', '解谜', '谜案', '案件', '凶手', '线索', '真相',
      '惊险', '惊心动魄', '扣人心弦', '紧张', '刺激', '激烈', '快节奏',
      // 动作冒险
      '动作', '冒险', '战斗', '冲突', '对抗', '激烈', '刺激', '紧张',
      '战争', '战斗', '打斗', '搏斗', '厮杀', '激战', '血战',
      // 情绪释放
      '宣泄', '释放', '发泄', '情绪', '压力', '愤怒', '激烈', '刺激',
      '复仇', '报复', '仇恨', '愤怒', '怒火', '愤恨', '怨恨'
    ],
    '蒜鸟蒜鸟': [
      // 平静相关
      '平静', '安静', '宁静', '平和', '放松', '舒缓', '慢节奏', '内心',
      '宁静', '安静', '平和', '平静', '放松', '舒缓', '慢节奏', '内心',
      '静谧', '恬静', '安详', '祥和', '安宁', '安逸', '舒适', '惬意',
      // 专注相关
      '专注', '冥想', '禅', '禅意', '禅修', '静心', '专注', '沉思',
      '内省', '自省', '反思', '思考', '沉思', '冥想', '静坐', '打坐',
      // 自然相关
      '自然', '山水', '风景', '田园', '乡村', '田野', '山林', '湖泊',
      '花', '草', '树', '鸟', '虫', '鱼', '自然', '生态', '环境'
    ],
    '支棱起来': [
      // 激励相关
      '激励', '鼓舞', '力量', '勇气', '坚强', '励志', '成长', '突破', '奋斗',
      '励志', '激励', '鼓舞', '力量', '勇气', '坚强', '成长', '突破', '奋斗',
      '激励人心', '鼓舞', '振奋', '振奋人心', '激励', '鼓舞', '激励',
      // 成功相关
      '成功', '坚持', '努力', '拼搏', '挑战', '克服', '战胜', '胜利', '成就',
      '成功', '胜利', '成就', '辉煌', '荣耀', '荣誉', '功绩', '业绩',
      // 成长相关
      '成长', '进步', '提升', '发展', '进步', '提升', '改善', '改进',
      '学习', '教育', '培训', '培养', '锻炼', '磨练', '历练', '经验'
    ],
    '大开脑洞': [
      // 科幻相关
      '科幻', '未来', '科技', '太空', '星际', '机器人', '人工智能', '虚拟', '赛博',
      '科幻', '科学', '技术', '未来', '太空', '宇宙', '星球', '外星',
      '机器人', '人工智能', 'ai', '智能', '自动化', '数字化', '虚拟', '赛博',
      // 探索相关
      '好奇', '探索', '发现', '未知', '神秘', '冒险', '新奇', '发现', '求知',
      '探索', '发现', '未知', '神秘', '冒险', '新奇', '求知', '发现',
      '探险', '冒险', '探索', '发现', '揭秘', '解密', '揭示', '揭示',
      // 历史相关（探索历史）
      '历史', '古代', '古代', '古代', '古代', '古代', '古代', '古代',
      '考古', '考古', '考古', '考古', '考古', '考古', '考古', '考古'
    ],
    '洗洗眼睛': [
      // 艺术相关
      '艺术', '美学', '审美', '优雅', '精致', '品味', '美感', '诗意',
      '艺术', '美学', '审美', '优雅', '精致', '品味', '美感', '诗意', '唯美',
      '绘画', '音乐', '文学', '诗歌', '散文', '艺术', '美学', '审美', '美感',
      // 文学相关
      '文学', '文学', '文学', '文学', '文学', '文学', '文学', '文学',
      '诗歌', '散文', '小说', '文学', '文学', '文学', '文学', '文学',
      // 美学相关
      '美', '美丽', '美好', '优美', '优美', '优美', '优美', '优美',
      '优雅', '优雅', '优雅', '优雅', '优雅', '优雅', '优雅', '优雅',
      // 文化相关
      '文化', '文化', '文化', '文化', '文化', '文化', '文化', '文化',
      '传统', '传统', '传统', '传统', '传统', '传统', '传统', '传统'
    ],
    '思考到裂开': [
      // 哲学相关
      '哲学', '思想', '思辨', '深度', '反思', '智慧', '人生', '意义', '真理',
      '哲学', '思想', '思辨', '深度', '反思', '智慧', '人生', '意义', '真理',
      '思考', '思辨', '深度', '反思', '智慧', '人生', '意义', '真理', '哲理',
      // 思考相关
      '思考', '思考', '思考', '思考', '思考', '思考', '思考', '思考',
      '反思', '反思', '反思', '反思', '反思', '反思', '反思', '反思',
      // 智慧相关
      '智慧', '智慧', '智慧', '智慧', '智慧', '智慧', '智慧', '智慧',
      '哲理', '哲理', '哲理', '哲理', '哲理', '哲理', '哲理', '哲理',
      // 人生相关
      '人生', '人生', '人生', '人生', '人生', '人生', '人生', '人生',
      '意义', '意义', '意义', '意义', '意义', '意义', '意义', '意义'
    ],
    '家人们谁懂啊': [
      // 共鸣相关
      '共鸣', '理解', '共情', '社交', '人际关系', '沟通', '情感', '陪伴', '理解',
      '共鸣', '理解', '共情', '社交', '人际关系', '沟通', '情感', '陪伴', '理解',
      '爱情', '友情', '亲情', '情感', '关系', '交流', '沟通', '理解', '共鸣',
      // 情感相关
      '情感', '情感', '情感', '情感', '情感', '情感', '情感', '情感',
      '感情', '感情', '感情', '感情', '感情', '感情', '感情', '感情',
      // 关系相关
      '关系', '关系', '关系', '关系', '关系', '关系', '关系', '关系',
      '交流', '交流', '交流', '交流', '交流', '交流', '交流', '交流',
      // 人物相关
      '人物', '人物', '人物', '人物', '人物', '人物', '人物', '人物',
      '角色', '角色', '角色', '角色', '角色', '角色', '角色', '角色'
    ],
  }
  
  // 去重关键词，避免重复计算
  const uniqueKeywords: Record<string, Set<string>> = {}
  for (const [category, keywords] of Object.entries(categoryKeywords)) {
    uniqueKeywords[category] = new Set(keywords)
  }
  
  // 计算每个分类的匹配分数
  const categoryScores: Record<string, number> = {}
  
  for (const [category, keywordSet] of Object.entries(uniqueKeywords)) {
    let score = 0
    for (const keyword of keywordSet) {
      // 计算关键词出现次数（不区分大小写）
      if (text.includes(keyword.toLowerCase())) {
        score += 1
      }
    }
    if (score > 0) {
      categoryScores[category] = score
    }
  }
  
  // 收集所有匹配的分类（匹配分数 >= 1 的都算）
  const matchedCategories: string[] = []
  
  // 按分数排序，优先添加高分分类
  const sortedCategories = Object.entries(categoryScores)
    .sort((a, b) => b[1] - a[1])
    .map(([category]) => category)
  
  // 如果匹配到分类，返回所有匹配的分类
  if (sortedCategories.length > 0) {
    matchedCategories.push(...sortedCategories)
  }
  
  // 使用更宽松的推断逻辑，确保每本书至少有一个分类
  const fallbackKeywords: Record<string, string[]> = {
    '求抱抱～': ['治愈', '温暖', '安慰', '温柔', '感动', '爱', '家', '生活', '情感', '关怀'],
    '暴躁上线': ['悬疑', '推理', '犯罪', '刺激', '紧张', '动作', '冒险', '战争', '惊悚', '恐怖'],
    '蒜鸟蒜鸟': ['平静', '安静', '宁静', '专注', '冥想', '自然', '山水', '田园', '舒缓', '放松'],
    '支棱起来': ['激励', '鼓舞', '力量', '勇气', '成功', '成长', '坚持', '努力', '奋斗', '励志'],
    '大开脑洞': ['科幻', '未来', '科技', '探索', '发现', '神秘', '历史', '古代', '未知', '新奇'],
    '洗洗眼睛': ['艺术', '美学', '审美', '优雅', '文学', '诗歌', '文化', '传统', '精致', '品味'],
    '思考到裂开': ['哲学', '思考', '思辨', '智慧', '人生', '意义', '真理', '反思', '深度', '哲理'],
    '家人们谁懂啊': ['共鸣', '理解', '情感', '关系', '交流', '人物', '角色', '故事', '小说', '叙事']
  }
  
  // 检查所有分类，如果匹配就添加（避免重复）
  for (const [category, words] of Object.entries(fallbackKeywords)) {
    if (!matchedCategories.includes(category)) {
      for (const word of words) {
        if (text.includes(word.toLowerCase())) {
          matchedCategories.push(category)
          break
        }
      }
    }
  }
  
  // 如果还是没有匹配，根据书籍类型进行推断
  if (matchedCategories.length === 0) {
    // 小说类 -> 共鸣之音
    if (text.includes('小说') || text.includes('故事') || text.includes('叙事') || text.includes('人物')) {
      matchedCategories.push('家人们谁懂啊')
    }
    
    // 历史类 -> 大开脑洞
    if (text.includes('历史') || text.includes('古代') || text.includes('年代') || text.includes('时期')) {
      matchedCategories.push('大开脑洞')
    }
    
    // 文学类 -> 洗洗眼睛
    if (text.includes('文学') || text.includes('诗歌') || text.includes('散文') || text.includes('艺术')) {
      matchedCategories.push('洗洗眼睛')
    }
    
    // 如果包含"思考"、"哲学"等 -> 思考到裂开
    if (text.includes('思考') || text.includes('哲学') || text.includes('智慧') || text.includes('人生')) {
      matchedCategories.push('思考到裂开')
    }
    
    // 如果包含"激励"、"成功"等 -> 支棱起来
    if (text.includes('激励') || text.includes('成功') || text.includes('成长') || text.includes('坚持')) {
      matchedCategories.push('支棱起来')
    }
    
    // 如果包含"悬疑"、"推理"等 -> 暴躁上线
    if (text.includes('悬疑') || text.includes('推理') || text.includes('犯罪') || text.includes('刺激')) {
      matchedCategories.push('暴躁上线')
    }
    
    // 如果包含"平静"、"安静"等 -> 蒜鸟蒜鸟
    if (text.includes('平静') || text.includes('安静') || text.includes('宁静') || text.includes('自然')) {
      matchedCategories.push('蒜鸟蒜鸟')
    }
    
    // 如果包含"治愈"、"温暖"等 -> 抚慰心灵
    if (text.includes('治愈') || text.includes('温暖') || text.includes('安慰') || text.includes('温柔')) {
      matchedCategories.push('求抱抱～')
    }
  }
  
  // 确保至少有一个分类（默认"家人们谁懂啊"）
  if (matchedCategories.length === 0) {
    matchedCategories.push('家人们谁懂啊')
  }
  
  // 去重并返回
  return Array.from(new Set(matchedCategories))
}

export default function HomePage() {
  const navigate = useNavigate()
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([])
  const [_message, setMessage] = useState('')
  const [isLoading, _setIsLoading] = useState(false)
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isAgentModalOpen, setIsAgentModalOpen] = useState(false)
  const [selectedBookId, setSelectedBookId] = useState<number | null>(null)
  const [selectedBookTitleForAsk, setSelectedBookTitleForAsk] = useState<string | null>(null)
  const [popularBooks, setPopularBooks] = useState<BookWithReason[]>([])
  const [notInterestedBook, setNotInterestedBook] = useState<{ id: number; title: string } | null>(null)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [isInitialLoading, setIsInitialLoading] = useState(true)
  const [showBackToTop, setShowBackToTop] = useState(false)
  const observerTarget = useRef<HTMLDivElement>(null)
  const PAGE_SIZE = 20
  const [visibleCapsules, setVisibleCapsules] = useState<typeof INSPIRATION_CAPSULES>([])

  useEffect(() => {
    document.title = '阅心 - 首页'
    return () => { document.title = '阅心' }
  }, [])
  const [usedIndices, setUsedIndices] = useState<Set<number>>(new Set())
  const [selectedCategory, setSelectedCategory] = useState<string>('全部')
  
  // 定义分类顺序（按用户要求的顺序）
  const categoryOrder = [
    '全部',
    '求抱抱～',
    '暴躁上线',
    '蒜鸟蒜鸟',
    '支棱起来',
    '大开脑洞',
    '洗洗眼睛',
    '思考到裂开',
    '家人们谁懂啊',
    '其他'
  ]
  
  // 获取所有分类（每本书可以属于多个分类）
  const categories = useMemo(() => {
    const categorySet = new Set<string>()
    
    popularBooks.forEach(book => {
      // 获取书籍的所有匹配分类
      const bookCategories = inferCategories(book)
      bookCategories.forEach(cat => categorySet.add(cat))
    })
    
    // 按照定义的顺序排序，确保所有8个分类都显示
    const sortedCategories = categoryOrder.filter(cat => 
      cat === '全部' || categorySet.has(cat)
    )
    
    console.log('📚 分类列表:', sortedCategories, '书籍数量:', popularBooks.length, '有分类的书籍:', Array.from(categorySet))
    return sortedCategories
  }, [popularBooks])
  
  // 根据选中的分类过滤书籍（一本书可以出现在多个分类下）
  const filteredBooks = useMemo(() => {
    if (selectedCategory === '全部') {
      return popularBooks
    }
    return popularBooks.filter(book => {
      // 获取书籍的所有匹配分类
      const bookCategories = inferCategories(book)
      // 如果书籍匹配该分类，就显示
      return bookCategories.includes(selectedCategory)
    })
  }, [popularBooks, selectedCategory])

  // 监听滚动，显示/隐藏回到顶部按钮
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop
      setShowBackToTop(scrollTop > 300) // 滚动超过300px时显示按钮
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // 回到顶部
  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    })
  }

  // 初始化显示的情绪胶囊
  const initializeCapsules = useCallback(() => {
    // 创建索引数组并打乱
    const indices = INSPIRATION_CAPSULES.map((_, idx) => idx)
    const shuffledIndices = indices.sort(() => Math.random() - 0.5)
    const selectedIndices = shuffledIndices.slice(0, CAPSULES_PER_PAGE)
    const initial = selectedIndices.map(idx => INSPIRATION_CAPSULES[idx])
    setVisibleCapsules(initial)
    setUsedIndices(new Set(selectedIndices))
  }, [])

  // 换一批情绪胶囊
  const refreshCapsules = useCallback(() => {
    // 如果所有胶囊都用过了，重置
    if (usedIndices.size >= INSPIRATION_CAPSULES.length) {
      setUsedIndices(new Set())
    }

    // 获取未使用的胶囊索引
    const availableIndices = INSPIRATION_CAPSULES
      .map((_, idx) => idx)
      .filter(idx => !usedIndices.has(idx))

    // 如果可用胶囊不足，重置并重新开始
    if (availableIndices.length < CAPSULES_PER_PAGE) {
      const indices = INSPIRATION_CAPSULES.map((_, idx) => idx)
      const shuffledIndices = indices.sort(() => Math.random() - 0.5)
      const selectedIndices = shuffledIndices.slice(0, CAPSULES_PER_PAGE)
      const newCapsules = selectedIndices.map(idx => INSPIRATION_CAPSULES[idx])
      setVisibleCapsules(newCapsules)
      setUsedIndices(new Set(selectedIndices))
    } else {
      // 从未使用的胶囊中随机选择
      const shuffled = availableIndices.sort(() => Math.random() - 0.5)
      const selectedIndices = shuffled.slice(0, CAPSULES_PER_PAGE)
      const newCapsules = selectedIndices.map(idx => INSPIRATION_CAPSULES[idx])
      setVisibleCapsules(newCapsules)
      setUsedIndices(prev => {
        const newSet = new Set(prev)
        selectedIndices.forEach(idx => newSet.add(idx))
        return newSet
      })
    }
  }, [usedIndices])

  useEffect(() => {
    // 初始加载"推荐你看"
    loadPopularBooks(0)
    // 初始化情绪胶囊
    initializeCapsules()
  }, [initializeCapsules])

  // 无限滚动：监听滚动到底部（全部 + 各分类 tab 均支持）
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoadingMore) {
          const nextSkip = popularBooks.length
          setIsLoadingMore(true)
          loadPopularBooks(nextSkip).finally(() => {
            setIsLoadingMore(false)
          })
        }
      },
      { threshold: 0.1, rootMargin: '0px 0px 150px 0px' }
    )

    const currentTarget = observerTarget.current
    if (currentTarget) {
      observer.observe(currentTarget)
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget)
      }
    }
  }, [hasMore, isLoadingMore, popularBooks.length])

  const loadPopularBooks = async (skip: number = 0, refresh = false) => {
    try {
      if (skip === 0) {
        setIsInitialLoading(true)
      }
      console.log(`开始加载热门书籍 (skip=${skip}, refresh=${refresh})...`)
      const books = await popularAPI.getEveryoneWatching(skip, PAGE_SIZE, { refresh })
      console.log('热门书籍加载成功:', books?.length || 0)
      
      if (books && books.length > 0) {
        if (skip === 0) {
          // 首次加载，随机排序
          const shuffled = [...books].sort(() => Math.random() - 0.5)
          setPopularBooks(shuffled)
        } else {
          // 追加加载
          setPopularBooks((prev) => [...prev, ...books])
        }
        setHasMore(books.length === PAGE_SIZE)
        console.log(`已加载 ${skip + books.length} 本书，还有更多: ${books.length === PAGE_SIZE}`)
      } else {
        console.warn('热门书籍列表为空')
        if (skip === 0) {
          setPopularBooks([])
        }
        setHasMore(false)
      }
    } catch (error: any) {
      console.error('加载热门书籍失败:', error)
      console.error('错误详情:', error.response?.data || error.message)
      if (skip === 0) {
        setPopularBooks([])
      }
      setHasMore(false)
    } finally {
      if (skip === 0) {
        setIsInitialLoading(false)
      }
    }
  }


  const handleRecommendations = (items: RecommendationItem[], msg: string) => {
    setRecommendations(items)
    setMessage(msg)
  }

  const handleRemoveCard = (bookId: number) => {
    setRecommendations((prev) => prev.filter((item) => item.book_id !== bookId))
  }

  const handleViewDetails = async (bookId: number) => {
    try {
      const book = await booksAPI.getBook(bookId)
      setSelectedBook(book)
      setIsDetailModalOpen(true)
    } catch (error: any) {
      console.error('获取书籍详情失败:', error)
      showToast('获取书籍详情失败，请稍后重试', 'error')
    }
  }

  const handleAskAgent = (bookId: number, bookTitle?: string) => {
    setSelectedBookId(bookId)
    setSelectedBookTitleForAsk(bookTitle ?? null)
    setIsAgentModalOpen(true)
  }

  const handleCapsuleClick = (text: string) => {
    navigate(`/recommendations?q=${encodeURIComponent(text)}`)
  }

  const handlePopularNotInterested = async (e: React.MouseEvent, bookId: number, bookTitle: string) => {
    e.stopPropagation()
    setNotInterestedBook({ id: bookId, title: bookTitle })
  }

  const confirmNotInterested = async () => {
    if (!notInterestedBook) return
    
    try {
      await bookshelfAPI.markNotInterested(notInterestedBook.id)
      setPopularBooks((prev) => prev.filter((b) => b.id !== notInterestedBook.id))
      showToast('已标记为不感兴趣', 'success')
    } catch (error: any) {
      console.error('标记不感兴趣失败:', error)
      showToast('操作失败，请稍后重试', 'error')
    } finally {
      setNotInterestedBook(null)
    }
  }

  return (
    <div className="space-y-8">
      {/* 搜索区域 */}
      <div className="text-center space-y-6">
        <div className="space-y-2">
          <h1 className="text-6xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-600 bg-clip-text text-transparent" style={{ fontFamily: '"Alibaba PuHuiTi 2.0", "Alibaba PuHuiTi", "阿里巴巴普惠体", sans-serif', letterSpacing: '0.05em', fontWeight: 700 }}>
            阅心
          </h1>
          <p className="text-foreground/70 text-lg">懂书，懂你心</p>
        </div>

        <UnifiedSearch onRecommendations={handleRecommendations} />

        {/* 情绪胶囊 */}
        <div className="pt-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-purple-500" />
              <h2 className="text-xl font-semibold text-foreground">情绪胶囊</h2>
            </div>
            <button
              onClick={refreshCapsules}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-card border border-border hover:bg-background transition-all text-sm hover:scale-105 disabled:opacity-50 text-purple-600 dark:text-purple-400"
              title="换一批"
            >
              <RefreshCw className="w-4 h-4" />
              <span>换一批</span>
            </button>
          </div>
          <div className="flex flex-wrap justify-start gap-2 max-h-[88px] overflow-hidden">
            {visibleCapsules.map((capsule, index) => (
              <button
                key={`${capsule.text}-${index}`}
                onClick={() => handleCapsuleClick(capsule.text)}
                disabled={isLoading}
                className="px-4 py-2 rounded-full bg-card border border-border hover:bg-background transition-all text-sm hover:scale-105 disabled:opacity-50 whitespace-nowrap"
              >
                <span className="mr-1">{capsule.emoji}</span>
                {capsule.text}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 推荐你看 - Feed流 */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-purple-500" />
            <h2 className="text-xl font-semibold text-foreground">推荐你看</h2>
          </div>
          <button
            onClick={() => loadPopularBooks(0, true)}
            disabled={isInitialLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-card border border-border hover:bg-background transition-all text-sm hover:scale-105 disabled:opacity-50 text-purple-600 dark:text-purple-400"
            title="重新推荐"
          >
            <RefreshCw className={`w-4 h-4 ${isInitialLoading ? 'animate-spin' : ''}`} />
            <span>重新推荐</span>
          </button>
        </div>
        
        {/* 分类Tab - 加载时显示所有分类（排除"其他"） */}
        <div className="flex flex-wrap gap-2 mb-6">
          {isInitialLoading ? (
            // 加载时显示所有分类（排除"其他"）
            categoryOrder.filter(cat => cat !== '其他').map((category) => (
              <button
                key={category}
                disabled={true}
                className={`px-4 py-2 rounded-full text-sm transition-all ${
                  selectedCategory === category
                    ? 'bg-purple-500 text-white shadow-md'
                    : 'bg-card border border-border text-foreground'
                } opacity-50 cursor-not-allowed`}
              >
                {category}
              </button>
            ))
          ) : (
            // 加载完成后显示实际有书籍的分类
            categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-full text-sm transition-all ${
                  selectedCategory === category
                    ? 'bg-purple-500 text-white shadow-md'
                    : 'bg-card border border-border text-foreground hover:bg-background'
                }`}
              >
                {category}
              </button>
            ))
          )}
        </div>
        
        {isInitialLoading ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* 骨架屏：封面、书名、作者、推荐语站位 */}
            {[...Array(6)].map((_, index) => (
              <div
                key={index}
                className="relative bg-card border border-border rounded-lg p-4 overflow-hidden"
              >
                <div className="flex gap-4">
                  {/* 封面站位 */}
                  <div className="w-20 h-28 rounded flex-shrink-0 relative overflow-hidden bg-background/30">
                    <div
                      className="absolute inset-0 bg-gradient-to-br from-background/20 via-background/50 to-background/20 animate-breathing rounded"
                      style={{ animationDelay: `${index * 0.15}s` }}
                    />
                  </div>
                  {/* 右侧：书名、作者、推荐语站位 */}
                  <div className="flex-1 min-w-0 flex flex-col gap-2">
                    {/* 书名站位 - 两行 */}
                    <div className="space-y-1.5">
                      <div className="relative h-4 rounded w-4/5 overflow-hidden">
                        <div
                          className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 animate-breathing rounded"
                          style={{ animationDelay: `${index * 0.15 + 0.05}s` }}
                        />
                      </div>
                      <div className="relative h-4 rounded w-2/3 overflow-hidden">
                        <div
                          className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 animate-breathing rounded"
                          style={{ animationDelay: `${index * 0.15 + 0.1}s` }}
                        />
                      </div>
                    </div>
                    {/* 作者站位 */}
                    <div className="relative h-3.5 rounded w-1/2 overflow-hidden">
                      <div
                        className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 animate-breathing rounded"
                        style={{ animationDelay: `${index * 0.15 + 0.15}s` }}
                      />
                    </div>
                    {/* 评分站位（小条） */}
                    <div className="relative h-3 rounded w-14 overflow-hidden">
                      <div
                        className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 animate-breathing rounded"
                        style={{ animationDelay: `${index * 0.15 + 0.2}s` }}
                      />
                    </div>
                    {/* 推荐语站位 - 多行 */}
                    <div className="mt-auto pt-2 pl-3 space-y-2 bg-background/30 rounded-r">
                      <div className="relative h-3 rounded w-full overflow-hidden">
                        <div
                          className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 animate-breathing rounded"
                          style={{ animationDelay: `${index * 0.15 + 0.25}s` }}
                        />
                      </div>
                      <div className="relative h-3 rounded w-11/12 overflow-hidden">
                        <div
                          className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 animate-breathing rounded"
                          style={{ animationDelay: `${index * 0.15 + 0.3}s` }}
                        />
                      </div>
                      <div className="relative h-3 rounded w-3/4 overflow-hidden">
                        <div
                          className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 animate-breathing rounded"
                          style={{ animationDelay: `${index * 0.15 + 0.35}s` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            </div>
            {/* 骨架屏下方加载动效 */}
            <div className="flex items-center justify-center gap-2 py-4 text-foreground/60">
              <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" aria-hidden />
              <span className="text-sm">正在为你推荐...</span>
            </div>
          </div>
        ) : filteredBooks.length > 0 ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredBooks.map((book) => (
                <div
                  key={book.id}
                  className="relative bg-card border border-border rounded-lg p-4 hover:shadow-lg transition-all cursor-pointer hover:scale-[1.02] group flex gap-4"
                >
                  <button
                    onClick={(e) => handlePopularNotInterested(e, book.id, book.title)}
                    className="absolute top-2 right-2 p-1.5 rounded-full hover:bg-background transition-colors z-10"
                    title="不感兴趣"
                  >
                    <X className="w-4 h-4 text-foreground/60" />
                  </button>
                  <div
                    onClick={() => handleViewDetails(book.id)}
                    className="flex gap-4 flex-1 min-w-0"
                  >
                    {book.cover_url ? (
                      <img
                        src={book.cover_url}
                        alt={book.title}
                        className="w-20 h-28 object-cover rounded flex-shrink-0 group-hover:brightness-110 transition-all"
                        loading="lazy"
                        decoding="async"
                      />
                    ) : (
                      <BookCoverPlaceholder
                        title={book.title}
                        className="w-20 h-28 rounded flex-shrink-0"
                      />
                    )}
                    <div className="flex-1 min-w-0 flex flex-col">
                      <h3 className="text-base font-semibold text-foreground mb-1 line-clamp-2">
                        {book.title}
                      </h3>
                      <p className="text-sm text-foreground/60 mb-2">{book.author}</p>
                      {book.rating && (
                        <p className="text-sm text-purple-500 mb-2">⭐ {book.rating.toFixed(1)}</p>
                      )}
                      {book.reason && (
                        <div className="mt-auto pt-2 border-l-2 border-purple-500/50 pl-3 bg-background/50 rounded-r">
                          <p className="text-sm text-foreground/90 leading-relaxed font-medium">
                            {book.reason}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {/* 无限滚动触发点 - 所有分类都支持 */}
            <div ref={observerTarget} className="h-10 flex items-center justify-center">
              {isLoadingMore && (
                <div className="flex items-center gap-2 text-foreground/60">
                  <div className="w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-sm">加载更多...</span>
                </div>
              )}
              {!hasMore && popularBooks.length > 0 && (
                <p className="text-sm text-foreground/50">已加载全部书籍</p>
              )}
            </div>
            {filteredBooks.length === 0 && !isLoadingMore && (
              <div className="text-center text-foreground/60 py-8">
                <p>该分类下暂无书籍</p>
              </div>
            )}
          </>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* 骨架屏：封面、书名、作者、推荐语站位（空状态复用） */}
            {[...Array(6)].map((_, index) => (
              <div
                key={index}
                className="relative bg-card border border-border rounded-lg p-4 overflow-hidden"
              >
                <div className="flex gap-4">
                  <div className="w-20 h-28 rounded flex-shrink-0 relative overflow-hidden bg-background/30">
                    <div
                      className="absolute inset-0 bg-gradient-to-br from-background/20 via-background/50 to-background/20 rounded"
                      style={{
                        animation: 'breathing 2s ease-in-out infinite',
                        animationDelay: `${index * 0.15}s`,
                      }}
                    />
                  </div>
                  <div className="flex-1 min-w-0 flex flex-col gap-2">
                    <div className="space-y-1.5">
                      <div className="relative h-4 rounded w-4/5 overflow-hidden">
                        <div
                          className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 rounded"
                          style={{
                            animation: 'breathing 2s ease-in-out infinite',
                            animationDelay: `${index * 0.15 + 0.05}s`,
                          }}
                        />
                      </div>
                      <div className="relative h-4 rounded w-2/3 overflow-hidden">
                        <div
                          className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 rounded"
                          style={{
                            animation: 'breathing 2s ease-in-out infinite',
                            animationDelay: `${index * 0.15 + 0.1}s`,
                          }}
                        />
                      </div>
                    </div>
                    <div className="relative h-3.5 rounded w-1/2 overflow-hidden">
                      <div
                        className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 rounded"
                        style={{
                          animation: 'breathing 2s ease-in-out infinite',
                          animationDelay: `${index * 0.15 + 0.15}s`,
                        }}
                      />
                    </div>
                    <div className="relative h-3 rounded w-14 overflow-hidden">
                      <div
                        className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 rounded"
                        style={{
                          animation: 'breathing 2s ease-in-out infinite',
                          animationDelay: `${index * 0.15 + 0.2}s`,
                        }}
                      />
                    </div>
                    <div className="mt-auto pt-2 pl-3 space-y-2 bg-background/30 rounded-r">
                      <div className="relative h-3 rounded w-full overflow-hidden">
                        <div
                          className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 rounded"
                          style={{
                            animation: 'breathing 2s ease-in-out infinite',
                            animationDelay: `${index * 0.15 + 0.25}s`,
                          }}
                        />
                      </div>
                      <div className="relative h-3 rounded w-11/12 overflow-hidden">
                        <div
                          className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 rounded"
                          style={{
                            animation: 'breathing 2s ease-in-out infinite',
                            animationDelay: `${index * 0.15 + 0.3}s`,
                          }}
                        />
                      </div>
                      <div className="relative h-3 rounded w-3/4 overflow-hidden">
                        <div
                          className="absolute inset-0 bg-gradient-to-r from-background/20 via-background/50 to-background/20 rounded"
                          style={{
                            animation: 'breathing 2s ease-in-out infinite',
                            animationDelay: `${index * 0.15 + 0.35}s`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 推荐结果（仅当从其他方式设置时显示，通常推荐结果在新页面） */}
      {recommendations.length > 0 && (
        <div className="space-y-6">
          {recommendations.map((item) => (
            <RecommendationCard
              key={item.book_id}
              item={item}
              onRemove={handleRemoveCard}
              onViewDetails={handleViewDetails}
              onAskAgent={handleAskAgent}
            />
          ))}
        </div>
      )}

      {/* 详情模态窗 */}
      <BookDetailModal
        book={selectedBook}
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        onAskAgent={handleAskAgent}
      />

      {/* AI 书童对话模态窗 */}
      <AgentChatModal
        bookId={selectedBookId}
        isOpen={isAgentModalOpen}
        onClose={() => {
          setIsAgentModalOpen(false)
          setSelectedBookId(null)
          setSelectedBookTitleForAsk(null)
        }}
        initialSessionName={selectedBookTitleForAsk}
        initialQuestion={selectedBookTitleForAsk ? `《${selectedBookTitleForAsk}》这本书讲了什么` : undefined}
      />

      {/* 不感兴趣确认对话框 */}
      <ConfirmDialog
        isOpen={!!notInterestedBook}
        title="不感兴趣"
        message={notInterestedBook ? `确定要将《${notInterestedBook.title}》标记为不感兴趣吗？这将帮助系统更好地为你推荐书籍。` : ''}
        confirmText="确认"
        cancelText="取消"
        onConfirm={confirmNotInterested}
        onCancel={() => setNotInterestedBook(null)}
      />

      {/* 回到顶部按钮 - 使用不同的样式以区别于AI书童按钮 */}
      {showBackToTop && (
        <button
          onClick={scrollToTop}
          className="fixed bottom-24 right-6 z-40 px-4 py-2 bg-card border-2 border-purple-500/30 text-purple-600 dark:text-purple-400 rounded-lg shadow-md hover:shadow-lg hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-all hover:scale-105 active:scale-95 flex items-center gap-2 backdrop-blur-sm"
          aria-label="回到顶部"
        >
          <ArrowUp className="w-5 h-5" />
          <span className="text-sm font-medium hidden sm:inline">顶部</span>
        </button>
      )}
    </div>
  )
}
