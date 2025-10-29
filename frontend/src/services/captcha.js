import http from './http'

export async function requestCaptcha ({ type = 'text', config = {} } = {}) {
  const response = await http.post('/captcha/request', { type, config })
  if (response.success) {
    return {
      token: response.token,
      type: response.type,
      data: response.data
    }
  }
  throw new Error(response.message || '验证码请求失败')
}

export async function verifyCaptcha (payload) {
  const response = await http.post('/captcha/verify', payload)
  return response
}

export async function getCaptchaTypes () {
  const response = await http.get('/captcha/available')
  return response
}
