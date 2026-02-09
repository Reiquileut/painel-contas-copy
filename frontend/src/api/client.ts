import axios from 'axios'

const API_URL = (window as any).__ENV__?.VITE_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'
const CSRF_COOKIE = 'ct_csrf'
const CSRF_HEADER = 'X-CSRF-Token'

function getCookieValue(name: string): string | null {
  const cookies = document.cookie.split(';').map((cookie) => cookie.trim())
  const match = cookies.find((cookie) => cookie.startsWith(`${name}=`))
  if (!match) return null
  return decodeURIComponent(match.split('=').slice(1).join('='))
}

const client = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const method = config.method?.toLowerCase()
  const isUnsafe = method !== 'get' && method !== 'head' && method !== 'options'
  if (isUnsafe) {
    const csrfToken = getCookieValue(CSRF_COOKIE)
    if (csrfToken) {
      config.headers[CSRF_HEADER] = csrfToken
    }
  }
  return config
})

let refreshPromise: Promise<void> | null = null

function doRefresh(): Promise<void> {
  if (refreshPromise) return refreshPromise
  refreshPromise = client
    .post('/api/v2/auth/refresh')
    .then(() => {})
    .finally(() => {
      refreshPromise = null
    })
  return refreshPromise
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status
    const config = error.config
    const requestUrl = String(config?.url || '')
    const isAuthEndpoint = requestUrl.includes('/api/v2/auth/')
    const currentPath = window.location?.pathname || ''
    const isLoginPath = currentPath === '/login' || currentPath.startsWith('/login/')

    if (status === 401 && !isAuthEndpoint && !isLoginPath && !config._retry) {
      config._retry = true
      try {
        await doRefresh()
        return client(config)
      } catch {
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  }
)

export default client
