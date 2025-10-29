import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 8000
})

http.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response) {
      return Promise.reject(error.response.data)
    }
    return Promise.reject(error)
  }
)

export default http
