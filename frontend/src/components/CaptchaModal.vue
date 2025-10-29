<template>
  <div class="modal">
    <div class="modal__content">
      <header class="modal__header">
        <h3>请完成验证码验证</h3>
        <button class="modal__close" @click="$emit('close')">×</button>
      </header>
      <section class="modal__body" v-if="challenge">
        <div v-if="challenge.type === 'text'" class="captcha-block">
          <img v-if="challenge.data.image" :src="challenge.data.image" alt="验证码" />
          <input v-model="answer" placeholder="请输入图片中的字符" />
        </div>
        <div v-else-if="challenge.type === 'slider'" class="captcha-block">
          <p>拖动滑块使拼图对齐</p>
          <div class="slider">
            <img :src="challenge.data.background" alt="背景" />
            <img v-if="challenge.data.piece" :src="challenge.data.piece" alt="拼图块" class="slider__piece" />
            <input type="range" min="0" max="200" v-model="answer" />
          </div>
        </div>
        <div v-else-if="challenge.type === 'scene'" class="captcha-block">
          <p>请选择所有 {{ challenge.data.category }} 图片</p>
          <div class="grid">
            <label v-for="image in challenge.data.images" :key="image.id">
              <input type="checkbox" :value="image.id" v-model="sceneSelection" />
              <span>{{ image.file_path }}</span>
            </label>
          </div>
        </div>
        <div v-else>
          <p>未知的验证码类型</p>
        </div>
      </section>
      <footer class="modal__footer">
        <button type="button" @click="$emit('refresh')">刷新</button>
        <button type="button" class="primary" :disabled="loading" @click="submit">{{ loading ? '提交中...' : '提交' }}</button>
      </footer>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CaptchaModal',
  props: {
    challenge: {
      type: Object,
      default: null
    },
    loading: Boolean
  },
  data () {
    return {
      answer: '',
      sceneSelection: []
    }
  },
  watch: {
    challenge: {
      handler (value) {
        this.answer = ''
        this.sceneSelection = []
        if (value && value.type === 'slider') {
          this.answer = 0
        }
      },
      immediate: true
    }
  },
  methods: {
    submit () {
      let resolved = this.answer
      if (this.challenge?.type === 'slider') {
        resolved = Number(this.answer)
      } else if (this.challenge?.type === 'scene') {
        resolved = this.sceneSelection
      }
      this.$emit('submit', resolved)
    }
  }
}
</script>

<style scoped>
.modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal__content {
  width: 420px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.2);
}

.modal__header,
.modal__footer {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f4f6fb;
}

.modal__body {
  padding: 1.5rem;
}

.modal__close {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  cursor: pointer;
}

.captcha-block {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: center;
}

.slider img {
  max-width: 100%;
  border-radius: 8px;
}

.slider__piece {
  margin-top: 0.5rem;
}

.grid {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(3, 1fr);
  width: 100%;
}

.grid label {
  border: 1px solid #dde3f4;
  border-radius: 8px;
  padding: 0.5rem;
  text-align: center;
  cursor: pointer;
}

.modal__footer button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.modal__footer .primary {
  background: #4a67ff;
  color: white;
}
</style>
