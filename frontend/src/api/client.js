import axios from 'axios'

// In dev, baseURL is '' and Vite proxies /api to the local FastAPI.
// In production, set VITE_API_BASE to the deployed backend URL (e.g. the Koyeb
// service URL); requests then go directly there.
const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE || '' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !location.pathname.startsWith('/login')) {
      localStorage.removeItem('token')
      location.href = '/login'
    }
    return Promise.reject(err)
  },
)

export default api
