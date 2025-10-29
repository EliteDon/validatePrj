<template>
  <div class="card">
    <h2>注册</h2>
    <form @submit.prevent="handleSubmit">
      <label>
        用户名
        <input v-model.trim="form.username" required placeholder="请输入用户名" />
      </label>
      <label>
        密码
        <input v-model="form.password" required type="password" placeholder="请输入密码" />
      </label>
      <button type="submit" :disabled="loading">{{ loading ? '提交中...' : '注册' }}</button>
    </form>
  </div>
</template>

<script>
import { register } from '../services/auth.js'

export default {
  name: 'RegisterForm',
  data () {
    return {
      loading: false,
      form: {
        username: '',
        password: ''
      }
    }
  },
  methods: {
    async handleSubmit () {
      this.loading = true
      try {
        const response = await register({
          username: this.form.username,
          password: this.form.password
        })
        if (response.success) {
          this.$emit('registered', response.user)
          this.form.username = ''
          this.form.password = ''
        } else {
          alert(response.message || '注册失败')
        }
      } catch (error) {
        console.error(error)
        alert('注册接口调用失败')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.05);
}

label {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

input {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border: 1px solid #dce1f4;
}

button {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  background: #4a67ff;
  color: #fff;
  cursor: pointer;
}
</style>
