🏦 零售行业信贷风控分析系统 (Retail Industry Credit Risk Analysis System)📖 项目简介 (Introduction)本项目是一个基于 Python Flask 和 MySQL 开发的全栈 Web 应用，旨在为零售行业的信贷业务提供智能化的数据管理、经营分析与风险预测解决方案。系统集成了数据可视化看板、随机森林（Random Forest）AI 预测模型以及完善的后台管理功能，帮助信贷审核人员快速评估商户资质，降低放贷风险。🚀 核心功能 (Key Features)1. 📊 综合数据仪表盘 (Smart Dashboard)实时 KPI 统计：动态展示总申请单数、待人工复核数、放款总金额（仅统计已通过订单）、高风险拒单数。动态趋势分析：通过异步接口（AJAX）实时计算各项指标的环比增长/下降趋势。数据管理：完整的 CRUD（增删改查）功能，支持分页显示、按 ID/商户名搜索。2. 📈 可视化深度分析 (Visual Analysis)ECharts 图表集成：业务增长趋势图：展示近 6 个月的申请量变化。客户画像雷达图：多维度（信用分、营收、资产）对比优质客户与风险客户。智能决策建议：系统根据统计结果自动生成运营建议与风险预警。3. 🤖 AI 智能信贷预测 (AI Prediction)独立沙箱环境：基于随机森林 (Random Forest) 算法的模拟预测模块。实时评估：输入商户核心指标（注册资本、信用分、经营年份、月均营收等），系统即时输出：风险评级（高/中/低）建议授信额度信用评分预测4. 🛡️ 系统安全与审计 (Security & Audit)角色权限管理：区分普通用户 (User) 与管理员 (Admin) 权限。操作审计日志：自动记录关键操作（登录、删除、修改），仅管理员可见。个人中心：支持用户修改个人信息及密码（文件读写持久化）。🛠️ 技术栈 (Tech Stack)模块技术选型说明后端Python, Flask轻量级 Web 框架，处理业务逻辑与路由数据库MySQL (PyMySQL)存储核心业务数据 (loan_data)数据存储JSON存储用户配置与审计日志 (users.json, audit.json)前端HTML5, Bootstrap 5响应式布局，紫色商务风格 UI可视化ECharts.js高性能数据可视化图表库算法Random Forest(模拟集成) 用于信贷风险评分模型⚙️ 本地安装与运行 (Installation)1. 克隆项目Bashgit clone https://github.com/zhaowanqiang/retail_industry.git
cd retail_industry
2. 安装依赖Bashpip install flask pymysql
3. 配置数据库确保本地安装了 MySQL，并执行以下 SQL 语句初始化数据库结构：SQLCREATE DATABASE retail_loan;
USE retail_loan;

CREATE TABLE loan_data (
    id VARCHAR(50) PRIMARY KEY,
    type VARCHAR(50),          -- 行业类型
    amount DOUBLE,             -- 注册金额
    score DOUBLE,              -- 信用评分
    years DOUBLE,              -- 经营年份
    monthly_flow DOUBLE,       -- 月均营收
    cost DOUBLE,               -- 月均成本
    traffic BIGINT,            -- 月均流量
    status VARCHAR(20),        -- 状态 (通过/拒绝/待审核)
    date VARCHAR(20)           -- 申请时间
    -- 其他字段根据需求添加
);
4. 修改配置打开 app.py，确保数据库连接配置正确：Pythonconn = pymysql.connect(
    host='localhost',
    user='root',         # 你的数据库账号
    password='YOUR_PASSWORD', # 你的数据库密码
    database='retail_loan',
    charset='utf8mb4'
)
5. 启动项目Bashpython app.py
访问浏览器：http://127.0.0.1:5000📸 系统截图 (Screenshots)核心数据列表(此处展示系统主界面，包含 CRUD 和 KPI 卡片)可视化分析看板(展示 ECharts 趋势图与雷达图)AI 预测实验室(输入参数进行风险评估的界面)📄 许可证 (License)本项目采用 MIT 许可证。仅供学习与毕业设计参考使用。Author: [zhaowanqiang]Last Updated: 2026-01-03
