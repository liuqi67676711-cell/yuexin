/**
 * 高亮文本中的搜索关键词
 */
export function highlightText(text: string, keywords: string[]): string {
  if (!text || !keywords || keywords.length === 0) {
    return text
  }

  // 去重并过滤空字符串
  const validKeywords = [...new Set(keywords.filter(k => k && k.trim()))]
  if (validKeywords.length === 0) {
    return text
  }

  // 按长度降序排序，优先匹配长词
  validKeywords.sort((a, b) => b.length - a.length)

  // 转义特殊字符用于正则表达式
  const escapedKeywords = validKeywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  
  // 构建正则表达式：匹配任一关键词（不区分大小写）
  const pattern = new RegExp(`(${escapedKeywords.join('|')})`, 'gi')
  
  // 替换匹配的文本，添加高亮标记
  return text.replace(pattern, '<mark class="bg-purple-500/25 text-purple-600 dark:text-purple-300 px-1 rounded font-medium">$1</mark>')
}
