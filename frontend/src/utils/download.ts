import axios from 'axios'

const extractFileName = (disposition?: string) => {
  if (!disposition) return ''
  const parts = disposition.split(';').map(p => p.trim())
  const fnStar = parts.find(p => p.toLowerCase().startsWith('filename*='))
  if (fnStar) {
    const v = fnStar.split('=')[1] || ''
    const decoded = v.replace(/^UTF-8''/i, '')
    try {
      return decodeURIComponent(decoded)
    } catch {
      return decoded
    }
  }
  const fn = parts.find(p => p.toLowerCase().startsWith('filename='))
  if (fn) {
    const v = fn.split('=')[1] || ''
    return v.replace(/^\"|\"$/g, '')
  }
  return ''
}

export const downloadFile = async (url: string, fallbackName = 'download.xlsx') => {
  const token = localStorage.getItem('token')
  const res = await axios.get(url, {
    responseType: 'blob',
    headers: token ? { Authorization: 'Bearer ' + token } : undefined
  })
  const disposition = res.headers?.['content-disposition'] as string | undefined
  const filename = extractFileName(disposition) || fallbackName

  const blobUrl = window.URL.createObjectURL(res.data)
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(blobUrl)
}

