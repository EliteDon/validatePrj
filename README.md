# 验证码生成与识别系统

本项目实现了一个基于 **Django 5 + Vue 2** 的验证码生成与识别系统，覆盖注册、登录、验证码管理、日志统计等核心功能模块，支持字符、拼图和场景选择三种验证码形式。

## 目录结构

```
├── backend               # Django 后端源代码
│   ├── captcha_backend    # 项目配置
│   ├── accounts           # 用户注册、登录与权限模块
│   ├── captcha_api        # 验证码生成、校验接口
│   └── activity           # 日志、验证码类型、场景图片管理
├── frontend              # Vue 2 前端应用
│   ├── src
│   │   ├── components     # 登录/注册、验证码弹窗组件
│   │   ├── services       # Axios 封装与接口调用
│   │   └── views          # 登录成功页等页面
│   └── vite.config.js     # Vite 配置
└── README.md
```

## 功能概览

- **验证码类型**：字符验证码（Pillow 生成）、滑块拼图验证码、场景选择验证码。管理员可通过接口增删改验证码类型。
- **用户认证**：注册接口进行密码复杂度校验并写入数据库，登录时要求先完成验证码校验才允许认证。
- **日志记录**：每次验证码验证结果都会写入 `captcha_logs`，便于后台统计分析。
- **安全措施**：验证码有效期 60 秒、登录/注册接口添加速率限制、密码采用 Django 加盐哈希存储。
- **前端交互**：登录页面触发验证码弹窗，验证通过后自动调用登录接口，支持多种验证码类型的展示与提交。

## 本地部署指南

### 1. 环境准备

| 组件 | 推荐版本 | 备注 |
| ---- | -------- | ---- |
| Python | 3.10.x | 建议使用 `pyenv` 或 `conda` 管理版本 |
| Node.js | ≥ 16 | Vue 2 + Vite 需要 Node 16/18 均可 |
| SQL Server | 2019+ | 可选，未安装时默认使用 SQLite |

- Windows 需提前安装 [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) 以编译 `pyodbc`。
- Linux 安装 SQL Server 驱动可参考微软官方文档（ODBC Driver 18）。
- 如果仅做功能体验，可跳过 SQL Server，系统会自动落到 SQLite 文件数据库。

### 2. 克隆项目

```bash
git clone <your_fork_or_repo_url>
cd validatePrj
```

### 3. 配置后端

1. **创建虚拟环境并安装依赖**

   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate        # Windows PowerShell 使用 .venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **（可选）配置 SQL Server 连接**

   - 复制 `.env.example`（若无可新建 `.env` 文件）并写入：

     ```ini
     DB_ENGINE=mssql
     DB_HOST=localhost
     DB_NAME=captcha_system
     DB_USER=sa
     DB_PASSWORD=root
     DB_PORT=1433
     ```

   - 安装 SQL Server 依赖：`pip install mssql-django pyodbc`。
   - 如果保持默认 SQLite，可忽略本步骤。

3. **初始化数据库**

   ```bash
   python manage.py migrate
   python manage.py loaddata seed_data.json   # 如果存在示例数据
   python manage.py createsuperuser           # 创建后台管理员
   ```

4. **运行开发服务器**

   ```bash
   python manage.py runserver
   ```

   默认地址为 <http://127.0.0.1:8000>，API 前缀为 `/api`。

> 如果需要同时在终端查看日志与验证码生成情况，可在另一个终端执行 `tail -f backend/logs/dev.log`（若启用日志文件输出）。

### 4. 配置前端

1. 在新的终端窗口返回项目根目录：

   ```bash
   cd ../frontend
   npm install
   ```

2. 启动前端开发服务器：

   ```bash
   npm run dev
   ```

3. 打开终端输出的本地地址（通常为 <http://127.0.0.1:5173>）。Vite 已将 `/api` 请求代理到 `http://127.0.0.1:8000`。

### 5. 功能验证

1. 打开浏览器访问前端地址，注册一个新账号。
2. 登录时会自动弹出验证码弹窗，根据提示完成验证码验证。
3. 成功登录后跳转到 Success 页。
4. 使用 `python manage.py runserver` 的终端观察后端日志，确认 `captcha_logs` 中产生记录。
5. 访问 <http://127.0.0.1:8000/admin> 使用之前创建的超级用户账号登录后台，管理验证码类型或查看日志。

### 6. 常见问题

- **`pyodbc` 编译失败**：确认已安装 ODBC 驱动与编译工具；Windows 用户建议使用官方提供的 `ODBC Driver 18` 安装包。
- **SQL Server 无法连接**：检查防火墙与端口 1433 是否开放，确认 SQL Server 允许混合身份验证模式。
- **跨域问题**：开发模式下由 Vite 代理处理；若自定义端口，请同步修改 `frontend/vite.config.js` 中的代理目标。
- **验证码图片路径错误**：确保 `backend/activity/models.py` 指向的图片目录存在，可运行 `python manage.py collectstatic` 或手动创建示例图片。

## 接口说明

- `POST /api/auth/register`：注册用户，参数 `username`、`password`。
- `POST /api/auth/login`：登录验证，参数 `username`、`password`、`captcha_token`、`captcha_answer`。
- `POST /api/captcha/request`：获取验证码挑战，支持 `text` / `slider` / `scene` 类型。
- `POST /api/captcha/verify`：校验验证码并写入日志。
- `GET /api/captcha/available`：获取验证码类型列表。
- `POST /api/captcha/types`：管理员新增/更新验证码类型。
- `DELETE /api/captcha/types/<id>`：管理员删除验证码类型。
- `GET /api/activity/logs`：管理员查看最近日志。
- `GET /api/activity/stats`：管理员查看统计数据。

## SQL Server 连接说明

默认使用 SQLite 数据库，生产环境可通过设置 `DB_ENGINE=mssql` 启用 SQL Server（驱动默认 `ODBC Driver 18 for SQL Server`）。请确保安装 `mssql-django`、`pyodbc` 等驱动依赖。

## 许可证

本项目采用 MIT License，详见源码头部声明。
