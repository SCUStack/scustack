interface UploadTicketResponse {
  upload_id: string
  upload_url: string
  method: 'POST'
}

export async function uploadHostedFile(apiBase: string, file: File): Promise<string> {
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
  const uploaded = await $fetch<{ code: number; data: { upload_id: string }; message: string }>(
    `${apiBase}${ticket.data.upload_url}`,
    { method: ticket.data.method, credentials: 'include', body: formData },
  )
  if (uploaded.code !== 0) throw new Error(uploaded.message || '文件上传失败')
  return uploaded.data.upload_id
}
