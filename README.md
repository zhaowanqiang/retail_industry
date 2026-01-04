# 🏦 零售行业信贷风控分析系统 (Retail Credit Risk Analysis System)

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.1-purple.svg)
![Scikit-learn](https://img.shields.io/badge/AI-RandomForest-red.svg)

## 📖 项目简介 (Introduction)

本项目是一个基于 **Python Flask** 和 **MySQL** 开发的全栈 Web 应用，专为零售行业信贷业务设计。系统集成了**数据可视化看板**、**随机森林 (Random Forest) AI 预测模型**以及完善的**后台管理功能**。

通过该系统，信贷审核人员可以高效地管理商户申请、分析经营数据、利用 AI 辅助评估风险，并根据可视化报表做出科学决策。

---

## 🚀 核心功能 (Key Features)

### 1. 📊 综合数据仪表盘 (Smart Dashboard)
- **实时 KPI 统计**：动态展示总申请单数、待人工复核数、放款总金额（仅统计已通过订单）、高风险拒单数。
- **数据管理 (CRUD)**：
  - 支持分页查看海量商户数据。
  - 支持按商户名或 ID 进行模糊搜索。
  - **一键审批**：管理员可直接点击绿色按钮通过审核。
  - **编辑/删除**：支持对商户信息的修改与删除。
- **Excel 导出**：支持将当前筛选的数据一键导出为 `.xlsx` 报表。

### 2. 📈 可视化深度分析 (Visual Analysis)
- **ECharts 图表集成**：
  - **业务增长趋势图 (折线图)**：展示近 6 个月的申请量变化趋势。
  - **客户画像雷达图 (Radar)**：多维度（信用分、营收、资产）对比优质客户与风险客户的特征差异。
- **AI 智能决策建议**：后端算法自动分析数据，生成动态的风险预警和运营建议文案。

### 3. 🤖 AI 智能信贷预测 (AI Prediction)
- **独立预测沙箱**：一个独立的交互式界面。
- **实时评估**：输入商户核心指标（注册资本、信用分、经营年份、月均营收、成本、流量），后台调用训练好的 **Random Forest** 模型。
- **输出结果**：即时反馈风险评级（高/低）、通过概率以及建议授信额度。

### 4. 🛡️ 系统安全与权限 (Security & RBAC)
- **角色权限控制 (RBAC)**：
  - **普通用户 (User)**：仅拥有查看列表、查看详情、新增申请的权限。
  - **管理员 (Admin)**：拥有最高权限，包括审核、编辑、删除、查看审计日志。
- **审计日志 (Audit Logs)**：(管理员独有) 自动记录系统的关键操作（如登录、删除数据），保障数据安全。
- **个人中心**：支持用户修改个人资料及密码（数据持久化存储）。

---

## 🛠️ 技术栈 (Tech Stack)

| 模块 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **后端** | Python, Flask | 轻量级 Web 框架，处理业务逻辑与路由 |
| **数据库** | MySQL (PyMySQL) | 存储核心业务数据 (`loan_data`) |
| **ORM/工具** | SQLAlchemy, Pandas | 数据清洗、SQL 操作、Excel 导出 |
| **数据存储** | JSON | 存储用户配置与审计日志 (`users.json`, `system_audit.json`) |
| **前端** | HTML5, Bootstrap 5 | 响应式布局，统一的紫色商务风格 UI |
| **可视化** | ECharts.js, Chart.js | 高性能数据可视化图表库 |
| **算法** | Scikit-learn | 随机森林算法，用于信贷风险评分模型 |

---
## 📂 目录结构 (Project Structure)

```text
retail_industry/
├── app.py                 # Flask 主程序入口 (路由、逻辑)
├── data/
│   ├── model.pkl          # 训练好的 AI 模型
│   ├── users.json         # 用户账号数据
│   └── system_audit.json  # 审计日志数据
├── static/                # 静态资源 (CSS/JS/Images)
└── templates/             # HTML 页面模板
    ├── login.html         # 登录/注册页
    ├── dashboard.html     # 主仪表盘 (列表 & CRUD)
    ├── analysis.html      # 可视化分析页
    ├── prediction.html    # AI 预测页
    ├── audit_logs.html    # 审计日志页
    └── profile.html       # 个人中心页
```
---
🔑 测试账号 (Test Accounts)
## 🔑 测试账号 (Test Accounts)

| 角色 | 用户名 | 密码 | 权限描述 |
| :--- | :--- | :--- | :--- |
| **管理员** | `admin` | `123456` | 拥有所有权限 (增删改查审) |
| **普通用户** | (任意注册) | (任意) | 仅查看和新增，无权操作敏感按钮 |
---
📸 系统预览 (Screenshots)

1. 核心数据管理 (Dashboard)
2. 深度可视化分析 (Visual Analysis)
3. AI 智能预测 (AI Lab)

📄 许可证 (License)

本项目采用 MIT 许可证。仅供学习与毕业设计参考使用。

Author: [zhaowanqiang] Last Updated: 2026-01
