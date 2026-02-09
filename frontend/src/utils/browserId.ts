/**
 * 生成并保存浏览器唯一标识
 */
export function getBrowserId(): string {
  let browserId = localStorage.getItem('browser_id')
  
  if (!browserId) {
    // 生成唯一ID：时间戳 + 随机数
    browserId = `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    localStorage.setItem('browser_id', browserId)
  }
  
  return browserId
}
