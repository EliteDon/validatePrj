import http from './http'

export async function register (payload) {
  try {
    const response = await http.post('/auth/register', payload)
    return response
  } catch (error) {
    if (error && typeof error === 'object') {
      return error
    }
    throw error
  }
}

export async function login (payload) {
  try {
    const response = await http.post('/auth/login', payload)
    return response
  } catch (error) {
    if (error && typeof error === 'object') {
      return error
    }
    throw error
  }
}

export async function sendEmailCode (payload) {
  try {
    const response = await http.post('/auth/send-email-code', payload)
    return response
  } catch (error) {
    if (error && typeof error === 'object') {
      return error
    }
    throw error
  }
}

export async function sendSmsCode (payload) {
  try {
    const response = await http.post('/auth/send-sms-code', payload)
    return response
  } catch (error) {
    if (error && typeof error === 'object') {
      return error
    }
    throw error
  }
}
