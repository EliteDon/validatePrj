<template>
  <div class="login-view">
    <header class="login-header">
      <h1>验证码生成与识别系统</h1>
      <p>支持多种验证码类型与多渠道验证</p>
    </header>
    <section class="login-panels">
      <register-form class="panel" @registered="handleRegistered" />
      <div class="panel login-panel">
        <h2>登录</h2>
        <form @submit.prevent="handleSubmit">
          <div class="field">
            <label>用户名</label>
            <input v-model.trim="form.username" required placeholder="请输入用户名" />
          </div>
          <div class="field">
            <label>密码</label>
            <input v-model="form.password" type="password" required placeholder="请输入密码" />
          </div>
          <div class="field">
            <label>验证码类型</label>
            <div class="type-selector">
              <button
                v-for="item in captchaTypes"
                :key="item.type_name"
                type="button"
                class="type-button"
                :class="{ active: item.type_name === activeType }"
                @click="setActiveType(item.type_name)"
              >
                {{ typeLabel(item.type_name, item.description) }}
                <span v-if="item.is_default" class="badge">默认</span>
              </button>
            </div>
          </div>
          <template v-if="activeType === 'email'">
            <div class="field">
              <label>邮箱</label>
              <input v-model.trim="form.email" type="email" required placeholder="请输入邮箱地址" />
            </div>
            <div class="field code-field">
              <label>验证码</label>
              <div class="code-row">
                <input v-model.trim="form.code" required placeholder="请输入邮箱验证码" />
                <button type="button" :disabled="emailCountdown > 0 || sendingCode" @click="requestEmailCode">
                  {{ emailCountdown > 0 ? `重新获取(${emailCountdown}s)` : '获取验证码' }}
                </button>
              </div>
            </div>
          </template>
          <template v-else-if="activeType === 'sms'">
            <div class="field">
              <label>手机号</label>
              <input v-model.trim="form.phone" required placeholder="请输入手机号" />
            </div>
            <div class="field code-field">
              <label>验证码</label>
              <div class="code-row">
                <input v-model.trim="form.code" required placeholder="请输入短信验证码" />
                <button type="button" :disabled="smsCountdown > 0 || sendingCode" @click="requestSmsCode">
                  {{ smsCountdown > 0 ? `重新获取(${smsCountdown}s)` : '获取验证码' }}
                </button>
              </div>
            </div>
          </template>
          <div class="actions">
            <button type="submit" :disabled="loading">
              {{ loading ? '提交中...' : '登录' }}
            </button>
          </div>
        </form>
      </div>
    </section>
    <captcha-modal
      v-if="captchaVisible"
      :challenge="captchaChallenge"
      :loading="loading"
      @submit="handleCaptchaSubmit"
      @close="closeCaptcha"
      @refresh="reloadCaptcha"
    />
  </div>
</template>

<script>
import RegisterForm from '../components/RegisterForm.vue'
import CaptchaModal from '../components/CaptchaModal.vue'
import { requestCaptcha, getCaptchaTypes } from '../services/captcha.js'
import { login, sendEmailCode, sendSmsCode } from '../services/auth.js'

export default {
  name: 'LoginView',
  components: {
    RegisterForm,
    CaptchaModal
  },
  data () {
    return {
      form: {
        username: '',
        password: '',
        email: '',
        phone: '',
        code: ''
      },
      captchaTypes: [],
      activeType: 'text',
      captchaChallenge: null,
      captchaVisible: false,
      loading: false,
      sendingCode: false,
      emailCountdown: 0,
      smsCountdown: 0,
      countdownTimer: null,
      pendingCredentials: null
    }
  },
  computed: {
    interactiveTypes () {
      return ['text', 'slider', 'puzzle', 'image_select', 'audio']
    }
  },
  created () {
    this.loadCaptchaTypes()
  },
  beforeDestroy () {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer)
    }
  },
  methods: {
    async loadCaptchaTypes () {
      try {
        const response = await getCaptchaTypes()
        if (response.success) {
          this.captchaTypes = response.data
          const defaultType = this.captchaTypes.find(item => item.is_default)
          this.activeType = defaultType ? defaultType.type_name : (this.captchaTypes[0]?.type_name || 'text')
        }
      } catch (error) {
        console.error(error)
      }
    },
    typeLabel (typeName, description) {
      const labels = {
        text: '字符验证码',
        slider: '滑块验证码',
        puzzle: '拼图验证码',
        image_select: '图片选图',
        email: '邮箱验证码',
        sms: '短信验证码',
        audio: '语音验证码'
      }
      return description || labels[typeName] || typeName
    },
    setActiveType (typeName) {
      this.activeType = typeName
      this.form.code = ''
      if (typeName !== 'email') {
        this.emailCountdown = 0
      }
      if (typeName !== 'sms') {
        this.smsCountdown = 0
      }
    },
    handleRegistered () {
      alert('注册成功，请登录')
    },
    async handleSubmit () {
      if (!this.form.username || !this.form.password) {
        alert('请输入账号和密码')
        return
      }

      if (this.interactiveTypes.includes(this.activeType)) {
        await this.startCaptchaFlow()
      } else {
        await this.submitWithCode()
      }
    },
    async startCaptchaFlow () {
      this.loading = true
      try {
        this.pendingCredentials = {
          username: this.form.username,
          password: this.form.password,
          captcha_type: this.activeType
        }
        const challenge = await requestCaptcha({ type: this.activeType })
        this.captchaChallenge = challenge
        this.captchaVisible = true
      } catch (error) {
        console.error(error)
        alert('验证码加载失败，请稍后再试')
      } finally {
        this.loading = false
      }
    },
    async submitWithCode () {
      this.loading = true
      try {
        const payload = {
          username: this.form.username,
          password: this.form.password,
          captcha_type: this.activeType
        }
        if (this.activeType === 'email') {
          payload.email = this.form.email
        } else if (this.activeType === 'sms') {
          payload.phone = this.form.phone
        }
        payload.code = this.form.code
        const response = await login(payload)
        this.handleLoginResponse(response)
      } catch (error) {
        console.error(error)
        alert('登录失败，请稍后重试')
      } finally {
        this.loading = false
      }
    },
    async handleCaptchaSubmit (answer) {
      if (!this.pendingCredentials || !this.captchaChallenge) return
      this.loading = true
      try {
        const payload = {
          ...this.pendingCredentials,
          captcha_token: this.captchaChallenge.token,
          captcha_answer: answer
        }
        const response = await login(payload)
        if (!response.success) {
          alert(response.message || '登录失败')
          await this.reloadCaptcha()
          return
        }
        this.handleLoginResponse(response)
      } catch (error) {
        console.error(error)
        alert('登录请求失败，请重试')
        await this.reloadCaptcha()
      } finally {
        this.loading = false
      }
    },
    handleLoginResponse (response) {
      if (response.success) {
        this.closeCaptcha()
        this.form.code = ''
        this.$emit('authenticated', response)
      } else {
        alert(response.message || '登录失败')
      }
    },
    closeCaptcha () {
      this.captchaVisible = false
      this.captchaChallenge = null
      this.pendingCredentials = null
    },
    async reloadCaptcha () {
      if (!this.pendingCredentials) return
      try {
        const challenge = await requestCaptcha({ type: this.pendingCredentials.captcha_type })
        this.captchaChallenge = challenge
      } catch (error) {
        console.error(error)
        alert('刷新验证码失败')
      }
    },
    async requestEmailCode () {
      if (!this.form.email) {
        alert('请先填写邮箱地址')
        return
      }
      this.sendingCode = true
      try {
        const response = await sendEmailCode({ email: this.form.email })
        if (response.success) {
          this.startCountdown('email')
          alert('验证码已发送，请查收邮箱')
        } else {
          alert(response.message || '验证码发送失败')
        }
      } catch (error) {
        console.error(error)
        alert('验证码发送失败，请稍后再试')
      } finally {
        this.sendingCode = false
      }
    },
    async requestSmsCode () {
      if (!this.form.phone) {
        alert('请先填写手机号')
        return
      }
      this.sendingCode = true
      try {
        const response = await sendSmsCode({ phone: this.form.phone })
        if (response.success) {
          this.startCountdown('sms')
          alert('验证码已发送，请注意查收')
        } else {
          alert(response.message || '短信发送失败')
        }
      } catch (error) {
        console.error(error)
        alert('短信发送失败，请稍后再试')
      } finally {
        this.sendingCode = false
      }
    },
    startCountdown (type) {
      if (this.countdownTimer) {
        clearInterval(this.countdownTimer)
      }
      if (type === 'email') {
        this.emailCountdown = 60
      } else {
        this.smsCountdown = 60
      }
      this.countdownTimer = setInterval(() => {
        if (this.emailCountdown > 0) {
          this.emailCountdown -= 1
        }
        if (this.smsCountdown > 0) {
          this.smsCountdown -= 1
        }
        if (this.emailCountdown <= 0 && this.smsCountdown <= 0) {
          clearInterval(this.countdownTimer)
          this.countdownTimer = null
        }
      }, 1000)
    }
  }
}
</script>

<style scoped>
.login-view {
  min-height: 100vh;
  padding: 2rem;
  background: #f6f7fb;
  font-family: 'Helvetica Neue', Arial, sans-serif;
  color: #2c3e50;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.panel {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.05);
}

.login-panel h2 {
  margin-top: 0;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.field label {
  font-weight: 600;
}

.field input {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border: 1px solid #dce1f4;
}

.type-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.type-button {
  border: 1px solid #dce1f4;
  border-radius: 20px;
  padding: 0.35rem 0.75rem;
  background: #fff;
  cursor: pointer;
  position: relative;
}

.type-button.active {
  background: #4a67ff;
  color: #fff;
  border-color: #4a67ff;
}

.type-button .badge {
  margin-left: 0.25rem;
  background: rgba(255, 255, 255, 0.2);
  padding: 0 0.35rem;
  border-radius: 999px;
  font-size: 0.75rem;
}

.code-field .code-row {
  display: flex;
  gap: 0.5rem;
}

.code-row button {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border: none;
  background: #4a67ff;
  color: white;
  cursor: pointer;
}

.actions {
  margin-top: 1.5rem;
}

.actions button {
  width: 100%;
  padding: 0.85rem;
  border: none;
  border-radius: 8px;
  background: #52bb7d;
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
}

.actions button[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
