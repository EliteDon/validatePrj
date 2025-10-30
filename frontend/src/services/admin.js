import http from './http'

export async function fetchCaptchaTypes () {
  return http.get('/admin/captcha-types/')
}

export async function createCaptchaType (payload) {
  return http.post('/admin/captcha-types/', payload)
}

export async function updateCaptchaType (id, payload) {
  return http.put(`/admin/captcha-types/${id}/`, payload)
}

export async function deleteCaptchaType (id) {
  return http.delete(`/admin/captcha-types/${id}/`)
}

export async function fetchLoginRecords (params) {
  return http.get('/admin/login-records/', { params })
}
