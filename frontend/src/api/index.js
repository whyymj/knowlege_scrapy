import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000  // AI接口可能需要更长时间
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    const data = response.data
    if (data.code === 200) {
      return data.data || data
    } else {
      const errorMsg = data.message || '请求失败'
      ElMessage.error(errorMsg)
      return Promise.reject(new Error(errorMsg))
    }
  },
  error => {
    let errorMsg = '请求失败'
    if (error.response) {
      errorMsg = error.response.data?.message || `HTTP ${error.response.status} 错误`
    } else if (error.request) {
      errorMsg = '网络错误，请检查网络连接'
    } else {
      errorMsg = error.message || '请求失败'
    }
    ElMessage.error(errorMsg)
    return Promise.reject(error)
  }
)

export default api
