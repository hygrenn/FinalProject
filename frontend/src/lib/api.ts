import axios, { type AxiosError } from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE,
  withCredentials: true,
})

export function shouldAttemptTokenRefresh(
  status: number | undefined,
  url: string | undefined,
  alreadyRetried: boolean,
  hasAccessToken: boolean
) {
  return status === 401 && !alreadyRetried && hasAccessToken && !url?.includes('/auth/')
}

api.interceptors.request.use((config) => {
  const token = useAuthTokenRef.getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as (typeof error.config & { _retry?: boolean }) | undefined
    if (
      original
      && shouldAttemptTokenRefresh(
        error.response?.status,
        original.url,
        Boolean(original._retry),
        Boolean(useAuthTokenRef.getToken())
      )
    ) {
      original._retry = true
      try {
        const { data } = await axios.post(
          `${import.meta.env.VITE_API_BASE}/auth/refresh`,
          {},
          { withCredentials: true }
        )
        useAuthTokenRef.setToken(data.access_token)
        if (original.headers) original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        useAuthTokenRef.clearToken()
        window.location.href = '/'
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  }
)

// Axios interceptor는 Zustand store를 직접 import하면 순환 의존성이 생긴다.
// ref 패턴으로 토큰을 주입한다.
export const useAuthTokenRef = {
  _token: null as string | null,
  getToken: () => useAuthTokenRef._token,
  setToken: (t: string) => { useAuthTokenRef._token = t },
  clearToken: () => { useAuthTokenRef._token = null },
}

export default api
