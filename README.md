# Email Server

> 基于 FastAPI 构建的现代化邮件服务器系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-开源免费-orange.svg)](LICENSE)

---

## 📖 项目简介

Email Server 是一个**完全开源、免费**的邮件服务器项目，采用 Python FastAPI 框架构建，支持高并发异步处理，具备完整的邮件收发功能。

### ✨ 核心特性

- 🚀 **高性能异步架构** - 基于 FastAPI + SQLAlchemy 异步模式
- 📧 **完整邮件收发** - SMTP 服务器接收 + MX 直投发送
- 🔐 **安全认证** - JWT Token + bcrypt 密码加密
- 🔏 **DKIM 签名** - 自动为外发邮件添加 DKIM 签名
- 🎨 **现代化 UI** - 响应式 Web 管理界面
- 📦 **一键打包** - 支持 PyInstaller 打包为独立可执行文件

---

## ⚠️ 重要声明

**本项目仅供学习研究、个人非商业用途使用！**

### 🚫 禁止事项

- ❌ **禁止商业贩卖** - 不得将本项目用于任何形式的商业销售、收费服务
- ❌ **禁止恶意使用** - 不得用于发送垃圾邮件、钓鱼邮件、诈骗邮件等违法行为
- ❌ **禁止非法用途** - 不得用于传播违法信息、侵犯他人权益的活动
- ❌ **禁止删除版权声明** - 使用本项目时须保留原始版权和许可声明

### ⚖️ 免责声明

- 本软件按"现状"提供，**不提供任何明示或暗示的担保**
- 使用本软件存在数据风险、安全风险、邮件投递风险等，用户需自行承担
- **本项目开发者和贡献者不承担任何因使用本软件导致的损失或法律责任**
- 因您的使用行为导致的任何法律责任，由您自行承担

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| ORM | SQLAlchemy 2.0 (异步) |
| 数据库 | SQLite / PostgreSQL |
| 认证 | JWT (python-jose) + bcrypt |
| 模板引擎 | Jinja2 |
| SMTP 服务 | aiosmtpd (接收) + aiosmtplib (发送) |
| DNS 解析 | aiodns |
| DKIM 签名 | dkimpy + cryptography |
| 异步运行时 | uvicorn |
| 打包工具 | PyInstaller |

---

## 📁 项目结构

```
email-server/
├── app/                          # 主应用目录
│   ├── main.py                   # 应用入口
│   ├── config.py                 # 配置管理
│   ├── database.py               # 数据库连接
│   ├── api/                      # API 路由
│   │   ├── auth.py               # 认证相关 API
│   │   ├── email.py              # 邮件相关 API
│   │   ├── pages.py              # 前端页面路由
│   │   └── admin.py              # 管理员 API
│   ├── models/                   # 数据模型
│   │   ├── user.py               # 用户和邮件模型
│   │   └── config.py             # 系统配置模型
│   ├── schemas/                  # Pydantic 模型
│   │   ├── user.py               # 用户相关 Schema
│   │   └── email.py              # 邮件相关 Schema
│   ├── services/                 # 核心服务
│   │   ├── auth.py               # 认证服务
│   │   ├── smtp_server.py        # SMTP 服务器（接收邮件）
│   │   ├── dkim_signer.py        # DKIM 签名服务
│   │   ├── email_sender.py       # 邮件发送服务
│   │   └── config_service.py     # 配置服务
│   ├── templates/                # Jinja2 模板
│   │   ├── base.html             # 基础模板
│   │   ├── index.html            # 首页
│   │   ├── login.html            # 登录页
│   │   ├── register.html         # 注册页
│   │   ├── dashboard.html        # 控制面板
│   │   ├── compose.html          # 写邮件
│   │   ├── inbox.html            # 收件箱
│   │   ├── admin.html            # 管理员面板
│   │   ├── profile.html          # 个人资料
│   │   └── setup.html            # 初始化设置
│   └── static/                   # 静态资源
│       ├── css/style.css         # 样式文件
│       └── js/app.js             # JavaScript
├── dkim_private.pem              # DKIM 私钥
├── dkim_public.pem               # DKIM 公钥
├── email_server.db               # SQLite 数据库
├── requirements.txt              # Python 依赖
├── pyproject.toml                # 项目配置
├── build.bat / build.sh          # 打包脚本
└── EmailServer.spec              # PyInstaller 配置
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本
- pip 包管理器

### 安装步骤

1. **克隆项目**

```bash
git clone https://github.com/tjc6666666666666/windows_emil_post.git
cd windows_emil_post
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **启动服务**

```bash
python -m app.main
```

或使用 uvicorn：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

4. **访问 Web 界面**

打开浏览器访问 `http://localhost:8000`

### 首次使用

1. 访问首页会自动跳转到初始化设置页面
2. 阅读并同意免责声明
3. 设置管理员账户和服务器配置
4. 根据 DNS 配置指南配置域名解析

---

## 📡 API 接口

### 认证模块 `/api/auth`

| 方法 | 路径 | 功能 | 权限 |
|------|------|------|------|
| POST | `/api/auth/register` | 用户注册 | 公开 |
| POST | `/api/auth/login` | 用户登录 | 公开 |
| GET | `/api/auth/me` | 获取当前用户信息 | 登录用户 |
| POST | `/api/auth/change-password` | 修改密码 | 登录用户 |
| GET | `/api/auth/users` | 获取用户列表 | 管理员 |
| POST | `/api/auth/users` | 创建新用户 | 管理员 |
| DELETE | `/api/auth/users/{user_id}` | 删除用户 | 管理员 |

### 邮件模块 `/api/email`

| 方法 | 路径 | 功能 | 权限 |
|------|------|------|------|
| POST | `/api/email/send` | 发送邮件 | 登录用户 |
| GET | `/api/email/sent` | 获取已发送邮件列表 | 登录用户 |
| GET | `/api/email/inbox` | 获取收件箱邮件列表 | 登录用户 |
| GET | `/api/email/inbox/{email_id}` | 获取邮件详情 | 登录用户 |

### 管理员模块 `/api/admin`

| 方法 | 路径 | 功能 | 权限 |
|------|------|------|------|
| GET | `/api/admin/config` | 获取系统配置 | 管理员 |
| PUT | `/api/admin/config` | 更新系统配置 | 管理员 |
| GET | `/api/admin/check-init` | 检查系统是否已初始化 | 公开 |
| GET | `/api/admin/dns-config` | 获取 DNS 配置信息 | 管理员 |

### API 文档

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

---

## 🗄️ 数据库模型

### User 表 (用户表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String(50) | 用户名，唯一 |
| password_hash | String(255) | 密码哈希 |
| is_active | Boolean | 是否激活 |
| is_admin | Boolean | 是否管理员 |
| created_at | DateTime | 创建时间 |

**邮箱地址**: 由 `username@MAIL_DOMAIN` 动态生成

### Email 表 (邮件表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| sender_id | Integer | 发送者 ID |
| recipient_id | Integer | 接收者 ID |
| from_addr | String(255) | 发件人地址 |
| to_addr | String(255) | 收件人地址 |
| subject | String(500) | 邮件主题 |
| body | Text | 纯文本正文 |
| html_body | Text | HTML 正文 |
| status | Enum | 邮件状态 |
| created_at | DateTime | 创建时间 |

**邮件状态**: `DRAFT` | `SENT` | `RECEIVED` | `FAILED`

### SystemConfig 表 (系统配置表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| config_key | String(100) | 配置键，唯一 |
| config_value | Text | 配置值 |
| description | String(255) | 配置描述 |
| updated_at | DateTime | 更新时间 |

---

## ⚙️ 配置项

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `SECRET_KEY` | - | 应用密钥 |
| `JWT_SECRET_KEY` | - | JWT 密钥 |
| `MAIL_DOMAIN` | `453627.xyz` | 邮件域名 |
| `SMTP_BIND` | `0.0.0.0` | SMTP 绑定地址 |
| `SMTP_PORT` | `25` | SMTP 端口 |
| `SMTP_HELO_HOSTNAME` | `mail.453627.xyz` | HELO 主机名 |
| `DATABASE_URL` | `sqlite+aiosqlite:///./email_server.db` | 数据库连接 URL |

---

## 🌐 DNS 配置指南

为确保邮件正常收发，需要配置以下 DNS 记录：

### 1. MX 记录

```
类型: MX
主机: @
值: mail.yourdomain.com
优先级: 10
```

### 2. DKIM 记录

```
类型: TXT
主机: default._domainkey
值: v=DKIM1; k=rsa; p=[公钥内容]
```

> 公钥内容可在初始化完成后从管理界面获取

### 3. DMARC 记录

```
类型: TXT
主机: _dmarc
值: v=DMARC1; p=quarantine; rua=mailto:admin@yourdomain.com
```

### 4. SPF 记录

```
类型: TXT
主机: @
值: v=spf1 ip4:您的服务器IP -all
```

### 5. A 记录

```
类型: A
主机: mail
值: 您的服务器IP
```

### 6. PTR 记录 (反向解析)

> 需要联系您的服务器提供商配置，将 IP 指向您的邮件域名

---

## 📦 打包部署

### 使用 PyInstaller 打包

**Windows:**

```bash
build.bat
```

**Linux/macOS:**

```bash
chmod +x build.sh
./build.sh
```

打包后的可执行文件位于 `dist/` 目录。

---

## 🖥️ 功能截图

### 首页

展示项目特性和快速入口。

### 初始化设置

首次使用时的配置向导，包含完整的免责声明和 DNS 配置指南。

### 控制面板

显示系统统计信息、快捷操作和最近邮件。

### 写邮件

简洁的邮件编写界面。

### 收件箱

查看接收的邮件列表和详情。

### 管理员面板

用户管理、系统配置、注册开关控制。

---

## 🔧 常见问题

### Q: 发送的邮件被标记为垃圾邮件？

A: 请确保：
- 正确配置了 DKIM、SPF、DMARC 记录
- 服务器有正确的 PTR 反向解析记录
- 服务器 IP 没有被列入黑名单

### Q: 无法接收外部邮件？

A: 请检查：
- 服务器 25 端口是否开放
- MX 记录是否正确配置
- 防火墙是否允许入站连接

### Q: 如何修改邮件域名？

A: 登录管理员账户，在管理面板中修改系统配置。

---

## 📝 开发计划

- [ ] 支持邮件附件
- [ ] 支持邮件文件夹管理
- [ ] 支持 IMAP 协议
- [ ] 邮件模板功能
- [ ] 邮件队列管理
- [ ] 多语言支持

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用开源许可证，**仅供学习研究、个人非商业用途使用**。

**禁止商业贩卖！禁止用于任何违法用途！**

---

## 📮 联系方式

- 项目地址: [GitHub](https://github.com/tjc6666666666666/windows_emil_post)
- 问题反馈: [Issues](https://github.com/tjc6666666666666/windows_emil_post/issues)

---

<div align="center">

**如果这个项目对您有帮助，请给一个 ⭐ Star 支持一下！**

Made with ❤️ by tjc6666666666666

</div>
