<template>
  <div class="app">
    <header class="app__header">
      <h1>验证码生成与识别系统</h1>
      <p>支持字符、拼图、场景三种验证码类型</p>
    </header>
    <main class="app__content">
      <section class="app__panel">
        <register-form @registered="handleRegistered" />
        <login-form @login-success="handleLoginSuccess" />
      </section>
      <success-view v-if="isAuthenticated" />
    </main>
    <captcha-modal
      v-if="captchaContext.visible"
      :loading="captchaContext.loading"
      :challenge="captchaContext.challenge"
      @submit="handleCaptchaSubmit"
      @close="closeCaptcha"
      @refresh="fetchCaptcha"
    />
  </div>
</template>

<script>
import LoginForm from './components/LoginForm.vue'
import RegisterForm from './components/RegisterForm.vue'
import CaptchaModal from './components/CaptchaModal.vue'
import SuccessView from './views/SuccessView.vue'
import { requestCaptcha } from './services/captcha.js'
import { login } from './services/auth.js'

export default {
  name: 'App',
  components: {
    LoginForm,
    RegisterForm,
    CaptchaModal,
    SuccessView
  },
  data () {
    return {
      isAuthenticated: false,
      pendingLoginData: null,
      captchaContext: {
        visible: false,
        loading: false,
        challenge: null
      }
    }
  },
  methods: {
    handleRegistered () {
      alert('注册成功，请登录')
    },
    handleLoginSuccess (credentials) {
      this.pendingLoginData = credentials
      this.fetchCaptcha()
    },
    async fetchCaptcha () {
      this.captchaContext.loading = true
      try {
        const challenge = await requestCaptcha({ type: 'text' })
        this.captchaContext.challenge = challenge
        this.captchaContext.visible = true
      } catch (error) {
        console.error(error)
        alert('验证码加载失败，请稍后再试')
      } finally {
        this.captchaContext.loading = false
      }
    },
    closeCaptcha () {
      this.captchaContext.visible = false
      this.captchaContext.challenge = null
      this.captchaContext.loading = false
    },
    async handleCaptchaSubmit (answer) {
      if (!this.captchaContext.challenge) return
      this.captchaContext.loading = true
      try {
        const response = await login({
          ...this.pendingLoginData,
          captcha_token: this.captchaContext.challenge.token,
          captcha_answer: answer
        })
        if (response.success) {
          this.handleLoginResult(true)
          this.pendingLoginData = null
          this.closeCaptcha()
        } else {
          alert(response.message || '登录失败')
          await this.fetchCaptcha()
        }
      } catch (error) {
        console.error(error)
        alert('登录接口调用失败')
        await this.fetchCaptcha()
      } finally {
        this.captchaContext.loading = false
      }
    },
    handleLoginResult (success) {
      this.isAuthenticated = success
    }
  },
  created () {
    this.$root.$on('login-finished', this.handleLoginResult)
  }
}
</script>

<style scoped>
.app {
  font-family: 'Helvetica Neue', Arial, sans-serif;
  padding: 2rem;
  color: #2c3e50;
  background: #f6f7fb;
  min-height: 100vh;
}

.app__header {
  text-align: center;
  margin-bottom: 2rem;
}

.app__panel {
  display: grid;
  gap: 1.5rem;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}
</style>
