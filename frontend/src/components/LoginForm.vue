<template>
  <div class="card">
    <h2>登录</h2>
    <form @submit.prevent="handleSubmit">
      <label>
        用户名
        <input v-model.trim="form.username" required placeholder="请输入用户名" />
      </label>
      <label>
        密码
        <input v-model="form.password" required type="password" placeholder="请输入密码" />
      </label>
      <button type="submit">下一步</button>
    </form>
  </div>
</template>

<script>
export default {
  name: 'LoginForm',
  data () {
    return {
      form: {
        username: '',
        password: ''
      }
    }
  },
  methods: {
    handleSubmit () {
      this.$emit('login-success', {
        username: this.form.username,
        password: this.form.password
      })
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
  background: #52bb7d;
  color: #fff;
  cursor: pointer;
}
</style>
