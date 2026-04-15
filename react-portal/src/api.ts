export type ApiResult<T> = {
  code: number
  message: string
  data: T | null
}

export async function apiRequest<T>(path: string, init?: RequestInit, token?: string): Promise<ApiResult<T>> {
  const headers = new Headers(init?.headers || {})
  if (!(init?.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  const res = await fetch(path, {
    ...init,
    headers,
  })
  return res.json()
}

export function buildUrl(path: string) {
  return path
}
