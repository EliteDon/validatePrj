<template>
  <div class="app-root">
    <component
      :is="currentComponent"
      :user-info="userInfo"
      @authenticated="handleAuthenticated"
      @navigate="navigate"
    />
  </div>
</template>

<script>
import LoginView from './views/LoginView.vue'
import SuccessView from './views/SuccessView.vue'
import AdminDashboard from './views/AdminDashboard.vue'

export default {
  name: 'App',
  components: {
    LoginView,
    SuccessView,
    AdminDashboard
  },
  data () {
    return {
      currentRoute: window.location.pathname || '/',
      userInfo: null
    }
  },
  computed: {
    currentComponent () {
      if (this.currentRoute === '/admin-dashboard') {
        return 'AdminDashboard'
      }
      if (this.currentRoute === '/success') {
        return 'SuccessView'
      }
      return 'LoginView'
    }
  },
  created () {
    window.addEventListener('popstate', this.handlePopState)
    this.ensureKnownRoute()
  },
  beforeDestroy () {
    window.removeEventListener('popstate', this.handlePopState)
  },
  methods: {
    handlePopState () {
      this.currentRoute = window.location.pathname || '/'
      this.ensureKnownRoute(false)
    },
    ensureKnownRoute (replace = true) {
      const allowed = ['/', '/success', '/admin-dashboard']
      if (!allowed.includes(this.currentRoute)) {
        this.currentRoute = '/'
        if (replace) {
          window.history.replaceState({}, '', this.currentRoute)
        }
      }
    },
    navigate (route, { replace = false } = {}) {
      if (this.currentRoute === route) {
        return
      }
      this.currentRoute = route
      if (replace) {
        window.history.replaceState({}, '', route)
      } else {
        window.history.pushState({}, '', route)
      }
    },
    handleAuthenticated (response) {
      this.userInfo = { is_staff: response.is_staff || false }
      const target = response.redirect || (response.is_staff ? '/admin-dashboard' : '/success')
      this.navigate(target)
    }
  }
}
</script>

<style>
body {
  margin: 0;
}

.app-root {
  min-height: 100vh;
}
</style>
