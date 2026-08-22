interface UploadTicketResponse {
  upload_id: string
  upload_url: string
  method: 'POST'
}

function readCookie(name: string): string {
  const prefix = `${encodeURIComponent(name)}=`
  const entry = document.cookie.split('; ').find(value => value.startsWith(prefix))
  return entry ? decodeURIComponent(entry.slice(prefix.length)) : ''
}

export async function uploadHostedFile(apiBase: string, file: File, onProgress?: (progress: number) => void): Promise<string> {
  const ticket = await $fetch<{ code: number; data: UploadTicketResponse; message: string }>(
    `${apiBase}/api/v1/upload/token`,
    {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_name: file.name,
        content_type: file.type || 'application/octet-stream',
        file_size: file.size,
      }),
    },
  )
  if (ticket.code !== 0) throw new Error(ticket.message || '获取上传凭据失败')

  const formData = new FormData()
  formData.append('file', file, file.name)
  const uploaded = await new Promise<{ code: number; data: { upload_id: string }; message: string }>((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open(ticket.data.method, `${apiBase}${ticket.data.upload_url}`)
    request.withCredentials = true
    const csrfToken = readCookie('csrf_token')
    if (csrfToken) request.setRequestHeader('X-CSRF-Token', csrfToken)
    request.upload.onprogress = event => {
      if (event.lengthComputable) onProgress?.(Math.min(90, Math.round(event.loaded / event.total * 90)))
    }
    request.onerror = () => reject(new Error('文件上传失败'))
    request.onload = () => {
      try {
        const response = JSON.parse(request.responseText)
        if (request.status < 200 || request.status >= 300) reject(new Error(response.message || '文件上传失败'))
        else resolve(response)
      } catch {
        reject(new Error('上传服务返回无效响应'))
      }
    }
    request.send(formData)
  })
  if (uploaded.code !== 0) throw new Error(uploaded.message || '文件上传失败')
  onProgress?.(100)
  return uploaded.data.upload_id
}
