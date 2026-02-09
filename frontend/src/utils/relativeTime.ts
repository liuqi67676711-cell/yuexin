/**
 * 将 ISO 日期转为相对时间展示
 * 刚刚 / 1分钟前 / 半小时前 / 1小时前 / 2小时前 / N天前，超过7天显示具体日期
 * 无时区且无 Z 的字符串按 UTC 解析，与后端统一
 */
export function formatRelativeTime(isoDate: string): string {
  if (!isoDate) return ''
  let s = isoDate.trim()
  if (s && !/Z|[+-]\d{2}:?\d{2}$/.test(s)) {
    s = s.endsWith('Z') ? s : s + 'Z'
  }
  const date = new Date(s)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 10) return '刚刚'
  if (diffSec < 60) return `${diffSec}秒前`
  if (diffMin < 2) return '1分钟前'
  if (diffMin < 30) return `${diffMin}分钟前`
  if (diffMin < 60) return '半小时前'
  if (diffHour < 2) return '1小时前'
  if (diffHour < 24) return `${diffHour}小时前`
  if (diffDay === 1) return '1天前'
  if (diffDay < 7) return `${diffDay}天前`
  // 超过7天显示具体日期（如 2月5日 或 2025/2/5）
  const sameYear = date.getFullYear() === now.getFullYear()
  if (sameYear) {
    return `${date.getMonth() + 1}月${date.getDate()}日`
  }
  return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
}
