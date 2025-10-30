<template>
  <div class="admin-dashboard">
    <header class="dashboard-header">
      <div>
        <h1>管理员后台</h1>
        <p>管理验证码类型并查看用户登录记录</p>
      </div>
      <button class="link" @click="$emit('navigate', '/', { replace: true })">返回登录</button>
    </header>

    <nav class="dashboard-tabs">
      <button
        type="button"
        :class="{ active: activeTab === 'types' }"
        @click="activeTab = 'types'"
      >
        验证码管理
      </button>
      <button
        type="button"
        :class="{ active: activeTab === 'records' }"
        @click="activeTab = 'records'"
      >
        登录记录
      </button>
    </nav>

    <section v-if="activeTab === 'types'" class="panel">
      <header class="panel-header">
        <h2>验证码类型</h2>
        <button type="button" @click="resetTypeForm">新增类型</button>
      </header>
      <div class="panel-body">
        <form class="type-form" @submit.prevent="submitType">
          <div class="form-grid">
            <label>
              类型
              <select v-model="typeForm.type_name" required>
                <option v-for="option in typeOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </label>
            <label>
              描述
              <input v-model="typeForm.description" placeholder="用于前端展示的说明" />
            </label>
            <label>
              图片路径
              <input v-model="typeForm.image_path" placeholder="(可选) 图片资源地址" />
            </label>
          </div>
          <label>
            配置(JSON)
            <textarea v-model="typeForm.configText" rows="4" placeholder='例如 { "length": 5 }'></textarea>
          </label>
          <div class="form-actions">
            <button type="submit" :disabled="savingType">
              {{ typeForm.id ? '更新类型' : '添加类型' }}
            </button>
            <label class="default-checkbox">
              <input type="checkbox" v-model="typeForm.is_default" />
              设为默认验证码
            </label>
          </div>
        </form>

        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>类型</th>
                <th>描述</th>
                <th>默认</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in captchaTypes" :key="item.id">
                <td>{{ typeLabel(item.type_name) }}</td>
                <td>{{ item.description || '—' }}</td>
                <td>{{ item.is_default ? '是' : '否' }}</td>
                <td class="actions-cell">
                  <button type="button" @click="editType(item)">编辑</button>
                  <button type="button" @click="setDefault(item)" :disabled="item.is_default">设为默认</button>
                  <button type="button" class="danger" @click="removeType(item)">删除</button>
                </td>
              </tr>
              <tr v-if="!captchaTypes.length">
                <td colspan="4" class="empty">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <section v-else class="panel">
      <header class="panel-header">
        <h2>登录记录</h2>
        <button type="button" @click="exportCsv">导出 CSV</button>
      </header>
      <div class="panel-body">
        <form class="filter-form" @submit.prevent="loadLoginRecords(1)">
          <label>
            起始时间
            <input type="datetime-local" v-model="filters.start" />
          </label>
          <label>
            结束时间
            <input type="datetime-local" v-model="filters.end" />
          </label>
          <label>
            状态
            <select v-model="filters.success">
              <option value="">全部</option>
              <option value="true">成功</option>
              <option value="false">失败</option>
            </select>
          </label>
          <button type="submit">筛选</button>
        </form>

        <div class="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>用户名</th>
                <th>时间</th>
                <th style="width: 160px">登录 IP</th>
                <th>设备信息</th>
                <th>结果</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="record in loginRecords" :key="record.id">
                <td>{{ record.username || record.user || '—' }}</td>
                <td>{{ formatDate(record.login_time) }}</td>
                <td>{{ record.ip_address || '—' }}</td>
                <td>{{ record.user_agent || '—' }}</td>
                <td>
                  <span :class="{ success: record.success, failed: !record.success }">
                    {{ record.success ? '成功' : '失败' }}
                  </span>
                </td>
              </tr>
              <tr v-if="!loginRecords.length">
                <td colspan="5" class="empty">暂无记录</td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer class="pagination">
          <button type="button" @click="changePage(-1)" :disabled="pagination.page <= 1">上一页</button>
          <span>第 {{ pagination.page }} / {{ totalPages }} 页</span>
          <button type="button" @click="changePage(1)" :disabled="pagination.page >= totalPages">下一页</button>
        </footer>
      </div>
    </section>
  </div>
</template>

<script>
import {
  fetchCaptchaTypes,
  createCaptchaType,
  updateCaptchaType,
  deleteCaptchaType,
  fetchLoginRecords
} from '../services/admin.js'

const TYPE_OPTIONS = [
  { value: 'text', label: '字符验证码' },
  { value: 'slider', label: '滑块验证码' },
  { value: 'puzzle', label: '拼图验证码' },
  { value: 'image_select', label: '图片选图验证码' },
  { value: 'email', label: '邮箱验证码' },
  { value: 'sms', label: '短信验证码' },
  { value: 'audio', label: '语音验证码' }
]

export default {
  name: 'AdminDashboard',
  props: {
    userInfo: {
      type: Object,
      default: () => ({})
    }
  },
  data () {
    return {
      activeTab: 'types',
      captchaTypes: [],
      loadingTypes: false,
      savingType: false,
      typeForm: {
        id: null,
        type_name: 'text',
        description: '',
        configText: '',
        image_path: '',
        is_default: false
      },
      typeOptions: TYPE_OPTIONS,
      loginRecords: [],
      pagination: {
        page: 1,
        pageSize: 10,
        total: 0
      },
      filters: {
        start: '',
        end: '',
        success: ''
      },
      loadingRecords: false
    }
  },
  computed: {
    totalPages () {
      if (this.pagination.pageSize <= 0) return 1
      return Math.max(1, Math.ceil(this.pagination.total / this.pagination.pageSize))
    }
  },
  created () {
    this.loadCaptchaTypes()
    this.loadLoginRecords()
  },
  methods: {
    async loadCaptchaTypes () {
      this.loadingTypes = true
      try {
        const response = await fetchCaptchaTypes()
        this.captchaTypes = Array.isArray(response) ? response : []
      } catch (error) {
        console.error(error)
        alert('获取验证码类型失败')
      } finally {
        this.loadingTypes = false
      }
    },
    typeLabel (type) {
      const option = this.typeOptions.find(item => item.value === type)
      return option ? option.label : type
    },
    editType (item) {
      this.typeForm = {
        id: item.id,
        type_name: item.type_name,
        description: item.description,
        configText: JSON.stringify(item.config_json || {}, null, 2),
        image_path: item.image_path || '',
        is_default: item.is_default
      }
    },
    resetTypeForm () {
      this.typeForm = {
        id: null,
        type_name: 'text',
        description: '',
        configText: '',
        image_path: '',
        is_default: false
      }
    },
    parseConfig () {
      if (!this.typeForm.configText.trim()) {
        return {}
      }
      try {
        return JSON.parse(this.typeForm.configText)
      } catch (error) {
        alert('配置必须是有效的 JSON 格式')
        throw error
      }
    },
    async submitType () {
      this.savingType = true
      try {
        const payload = {
          type_name: this.typeForm.type_name,
          description: this.typeForm.description,
          config_json: this.parseConfig(),
          image_path: this.typeForm.image_path,
          is_default: this.typeForm.is_default
        }
        if (this.typeForm.id) {
          await updateCaptchaType(this.typeForm.id, payload)
        } else {
          await createCaptchaType(payload)
        }
        await this.loadCaptchaTypes()
        this.resetTypeForm()
      } catch (error) {
        console.error(error)
      } finally {
        this.savingType = false
      }
    },
    async setDefault (item) {
      try {
        await updateCaptchaType(item.id, {
          type_name: item.type_name,
          description: item.description,
          config_json: item.config_json || {},
          image_path: item.image_path,
          is_default: true
        })
        await this.loadCaptchaTypes()
      } catch (error) {
        console.error(error)
        alert('设置默认验证码失败')
      }
    },
    async removeType (item) {
      if (!confirm(`确定要删除 ${this.typeLabel(item.type_name)} 吗？`)) {
        return
      }
      try {
        await deleteCaptchaType(item.id)
        await this.loadCaptchaTypes()
      } catch (error) {
        console.error(error)
        alert('删除失败')
      }
    },
    async loadLoginRecords (page = this.pagination.page) {
      this.loadingRecords = true
      try {
        const params = {
          page,
          page_size: this.pagination.pageSize
        }
        if (this.filters.start) params.start = this.filters.start
        if (this.filters.end) params.end = this.filters.end
        if (this.filters.success) params.success = this.filters.success
        const response = await fetchLoginRecords(params)
        this.loginRecords = response.results || []
        this.pagination.total = response.count || 0
        this.pagination.page = page
      } catch (error) {
        console.error(error)
        alert('获取登录记录失败')
      } finally {
        this.loadingRecords = false
      }
    },
    changePage (delta) {
      const target = this.pagination.page + delta
      if (target < 1 || target > this.totalPages) return
      this.loadLoginRecords(target)
    },
    exportCsv () {
      const params = new URLSearchParams()
      if (this.filters.start) params.append('start', this.filters.start)
      if (this.filters.end) params.append('end', this.filters.end)
      if (this.filters.success) params.append('success', this.filters.success)
      params.append('export', 'csv')
      params.append('page_size', String(this.pagination.pageSize))
      const query = params.toString()
      const url = `/api/admin/login-records/?${query}`
      window.open(url, '_blank')
    },
    formatDate (value) {
      if (!value) return '—'
      try {
        return new Date(value).toLocaleString()
      } catch (error) {
        return value
      }
    }
  }
}
</script>

<style scoped>
.admin-dashboard {
  min-height: 100vh;
  padding: 2rem;
  background: #f5f7fb;
  color: #2c3e50;
  font-family: 'Helvetica Neue', Arial, sans-serif;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.dashboard-header h1 {
  margin: 0;
}

.dashboard-header .link {
  border: none;
  background: transparent;
  color: #4a67ff;
  cursor: pointer;
}

.dashboard-tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.dashboard-tabs button {
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 999px;
  cursor: pointer;
  background: #e2e6f8;
  color: #2c3e50;
}

.dashboard-tabs button.active {
  background: #4a67ff;
  color: #fff;
}

.panel {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #eef1f8;
}

.panel-header button {
  border: none;
  background: #4a67ff;
  color: #fff;
  padding: 0.6rem 1rem;
  border-radius: 6px;
  cursor: pointer;
}

.panel-body {
  padding: 1.5rem;
}

.type-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.type-form label {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.type-form input,
.type-form select,
.type-form textarea {
  padding: 0.7rem 0.9rem;
  border: 1px solid #dce1f4;
  border-radius: 8px;
  font-size: 0.95rem;
}

.form-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.form-actions button {
  border: none;
  background: #52bb7d;
  color: #fff;
  padding: 0.7rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
}

.default-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.table-wrapper {
  overflow-x: auto;
}

.table-wrapper table {
  width: 100%;
  border-collapse: collapse;
}

.table-wrapper th,
.table-wrapper td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #eef1f8;
  text-align: left;
}

.actions-cell {
  display: flex;
  gap: 0.5rem;
}

.actions-cell button {
  border: none;
  background: #e2e6f8;
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
}

.actions-cell button.danger {
  background: #ff6464;
  color: #fff;
}

.empty {
  text-align: center;
  color: #97a0c3;
}

.filter-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.filter-form label {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-form input,
.filter-form select {
  padding: 0.65rem 0.9rem;
  border: 1px solid #dce1f4;
  border-radius: 8px;
}

.filter-form button {
  border: none;
  background: #4a67ff;
  color: #fff;
  padding: 0.7rem 1.2rem;
  border-radius: 8px;
  cursor: pointer;
}

.pagination {
  margin-top: 1rem;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 1rem;
}

.pagination button {
  border: none;
  background: #e2e6f8;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
}

.pagination button[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
}

.success {
  color: #2ecc71;
}

.failed {
  color: #ff6464;
}
</style>
