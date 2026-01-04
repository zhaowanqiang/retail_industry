# 🏦 零售行业信贷风控分析系统 (Retail Industry Credit Risk Analysis System)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)](https://www.mysql.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.1-purple.svg)](https://getbootstrap.com/)

## 📖 项目简介 (Introduction)

本项目是一个基于 **Python Flask** 和 **MySQL** 开发的全栈 Web 应用，旨在为零售行业的信贷业务提供智能化的**数据管理、经营分析与风险预测**解决方案。

系统集成了数据可视化看板、随机森林（Random Forest）AI 预测模型以及完善的后台管理功能，帮助信贷审核人员快速评估商户资质，降低放贷风险。

## 🚀 核心功能 (Key Features)

### 1. 📊 综合数据仪表盘 (Smart Dashboard)
- **实时 KPI 统计**：动态展示总申请单数、待人工复核数、放款总金额（仅统计已通过订单）、高风险拒单数。
- **动态趋势分析**：通过异步接口（AJAX）实时计算各项指标的环比增长/下降趋势。
- **数据管理**：完整的 CRUD（增删改查）功能，支持分页显示、按 ID/商户名搜索。

### 2. 📈 可视化深度分析 (Visual Analysis)
- **ECharts 图表集成**：
  - **业务增长趋势图**：展示近 6 个月的申请量变化。
  - **客户画像雷达图**：多维度（信用分、营收、资产）对比优质客户与风险客户。
- **智能决策建议**：系统根据统计结果自动生成运营建议与风险预警。

### 3. 🤖 AI 智能信贷预测 (AI Prediction)
- **独立沙箱环境**：基于**随机森林 (Random Forest)** 算法的模拟预测模块。
- **实时评估**：输入商户核心指标（注册资本、信用分、经营年份、月均营收等），系统即时输出：
  - **风险评级**（高/中/低）
  - **建议授信额度**
  - **信用评分预测**

### 4. 🛡️ 系统安全与审计 (Security & Audit)
- **角色权限管理**：区分普通用户 (User) 与管理员 (Admin) 权限。
- **操作审计日志**：自动记录关键操作（登录、删除、修改），仅管理员可见。
- **个人中心**：支持用户修改个人信息及密码（文件读写持久化）。

## 🛠️ 技术栈 (Tech Stack)

| 模块 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **后端** | Python, Flask | 轻量级 Web 框架，处理业务逻辑与路由 |
| **数据库** | MySQL (PyMySQL) | 存储核心业务数据 (`loan_data`) |
| **数据存储** | JSON | 存储用户配置与审计日志 (`users.json`, `audit.json`) |
| **前端** | HTML5, Bootstrap 5 | 响应式布局，紫色商务风格 UI |
| **可视化** | ECharts.js | 高性能数据可视化图表库 |
| **算法** | Random Forest | (模拟集成) 用于信贷风险评分模型 |

## ⚙️ 本地安装与运行 (Installation)

### 1. 克隆项目
```bash
git clone https://github.com/zhaowanqiang/retail_industry.git
cd retail_industry
