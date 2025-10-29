<template>
  <div class="success">
    <h2>欢迎回来！</h2>
    <p>您已通过验证码验证并成功登录。</p>
  </div>
</template>

<script>
export default {
  name: 'SuccessView'
}
</script>

<style scoped>
.success {
  margin-top: 2rem;
  padding: 2rem;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
  text-align: center;
}
</style>
