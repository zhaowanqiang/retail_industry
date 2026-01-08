# 零售贷款管理系统

一个基于 Flask 和机器学习的零售行业贷款申请管理系统，提供完整的贷款审批流程、数据分析和 AI 智能预测功能。

## 📋 项目简介

本系统是一个面向零售行业的贷款管理系统，支持贷款申请的录入、审核、分析和管理。系统集成了机器学习模型，能够对贷款申请进行智能预测，帮助管理员做出更准确的审批决策。

## ✨ 功能特性

### 🔐 用户认证
- **用户注册/登录**：支持用户注册和登录功能
- **权限管理**：区分管理员（admin）和普通用户（user）角色
- **个人中心**：支持密码修改和资料更新

### 📊 数据管理
- **贷款数据录入**：支持新增贷款申请记录
- **数据查询**：支持多条件筛选和搜索（状态、行业、城市、金额、信用分、日期等）
- **数据编辑**：管理员可修改贷款记录
- **数据删除**：支持单条和批量删除（仅管理员）
- **数据导出**：支持 Excel 格式导出（支持搜索条件导出和批量导出）

### ✅ 审批功能
- **单条审批**：管理员可对单条记录进行审批
- **批量审批**：支持批量审批多个贷款申请（仅管理员）
- **状态管理**：支持待审核、通过、拒绝等状态

### 📈 数据分析
- **业务增长趋势**：显示过去 6 个月的业务趋势折线图
- **行业分析**：按行业类型统计金额、数量和平均信用分（柱状图）
- **状态分布**：按审批状态显示数量和金额占比（饼图）
- **客户对比**：优质客户与风险客户的多维度雷达图对比
- **KPI 趋势**：显示总申请数、放款总额、平均信用分等关键指标及趋势变化

### 🤖 AI 智能预测
- **贷款审批预测**：基于机器学习模型预测贷款申请是否通过
- **预测概率**：显示审批通过的概率百分比
- **模型训练**：支持使用历史数据训练新的预测模型

### 🔍 系统审计
- **操作日志**：记录所有关键操作（登录、审批、删除等）
- **日志查询**：管理员可查看完整的操作审计日志
- **IP 追踪**：记录操作者的 IP 地址

## 🛠️ 技术栈

### 后端
- **Flask**：Web 框架
- **MySQL**：关系型数据库
- **SQLAlchemy**：数据库 ORM
- **Pandas**：数据处理和分析
- **NumPy**：数值计算
- **scikit-learn**：机器学习框架
- **joblib**：模型序列化

### 前端
- **HTML/CSS/JavaScript**：前端基础技术
- **Chart.js**：数据可视化图表库

### 其他工具
- **PyMySQL**：MySQL 数据库连接驱动
- **openpyxl**：Excel 文件处理

## 📁 项目结构

```
retail_industry/
├── app.py                    # Flask 主应用文件
├── audit_utils.py            # 审计日志工具模块
├── fix_mysql_date.py         # 数据库日期修复脚本
├── data/
│   ├── model.pkl            # 训练好的机器学习模型
│   ├── raw/
│   │   └── loan_data.csv    # 原始 CSV 数据文件
│   ├── retail.db            # SQLite 数据库（如使用）
│   └── users.json           # 用户数据文件
├── src/
│   ├── train_model.py       # 模型训练脚本
│   ├── import_db.py         # CSV 数据导入脚本
│   └── fix_db.py            # 数据库结构修复脚本
├── templates/               # HTML 模板目录
│   ├── login.html           # 登录页面
│   ├── dashboard.html       # 数据仪表板
│   ├── analysis.html        # 数据分析页面
│   ├── prediction.html      # AI 预测页面
│   ├── profile.html         # 个人中心页面
│   └── audit_logs.html      # 审计日志页面
├── system_audit.json        # 系统审计日志文件
└── README.md                # 项目说明文档
```

## 📦 环境要求

- Python 3.7+
- MySQL 5.7+ 或 MySQL 8.0+
- pip（Python 包管理器）

## 🚀 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd retail_industry
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install flask pandas numpy scikit-learn joblib pymysql sqlalchemy openpyxl
```

或使用 requirements.txt（如果存在）：

```bash
pip install -r requirements.txt
```

### 4. 配置数据库

#### 4.1 创建 MySQL 数据库

```sql
CREATE DATABASE retail_loan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 4.2 修改数据库配置

编辑 `app.py` 文件，修改数据库连接信息：

```python
DB_URI = "mysql+pymysql://root:你的密码@localhost:3306/retail_loan?charset=utf8mb4"
```

同时需要修改以下文件中的数据库配置（如果存在）：
- `src/import_db.py`
- `src/fix_db.py`
- `fix_mysql_date.py`

### 5. 导入数据

#### 方式一：从 CSV 导入（推荐）

```bash
cd src
python import_db.py
```

#### 方式二：手动创建表结构

如果 CSV 导入失败，可以运行修复脚本来创建必要的字段：

```bash
cd src
python fix_db.py
```

### 6. 训练机器学习模型

```bash
cd src
python train_model.py
```

训练完成后，模型文件将保存在 `data/model.pkl`。

### 7. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## ⚙️ 配置说明

### 默认管理员账户

系统默认管理员用户名为 `admin`，首次使用需要先注册该账户。

### 数据库字段说明

主要数据表 `loan_data` 包含以下字段：
- `id`：贷款申请编号（自动生成）
- `name`：商户名称
- `amount`：申请金额（万元）
- `score`：企业信用评分
- `type`：行业类型
- `status`：审批状态（待审核/通过/拒绝）
- `date`：申请日期
- `monthly_flow`：月均营收（万元）
- `cost`：月均成本（万元）
- `traffic`：月均客流量（人）
- `city`：所在城市
- `city_level`：城市等级
- `years`：经营年份
- `employees`：员工数
- `area`：经营面积（平方米）

### 数据文件路径

- 原始数据：`data/raw/loan_data.csv`
- 模型文件：`data/model.pkl`
- 用户数据：`data/users.json`
- 审计日志：`system_audit.json`

## 📖 使用说明

### 用户登录

1. 访问 `http://localhost:5000`
2. 首次使用需要注册账户
3. 选择身份：`admin`（管理员）或 `user`（普通用户）
4. 使用注册的用户名和密码登录

### 数据管理

- **新增贷款**：在仪表板页面点击"新增贷款"按钮
- **搜索数据**：使用顶部搜索框进行关键字搜索
- **筛选数据**：使用筛选条件（状态、行业、城市、金额范围等）
- **编辑数据**：管理员可点击"编辑"按钮修改记录
- **删除数据**：管理员可单条删除或批量删除（需先勾选）

### 数据分析

访问 `/analysis` 页面查看：
- 业务增长趋势图
- 行业统计分析
- 审批状态分布
- 客户质量对比

### AI 预测

访问 `/prediction` 页面：
1. 输入贷款申请的 6 个关键指标
2. 点击"开始预测"
3. 查看预测结果和通过概率

### 数据导出

在仪表板页面：
- 输入搜索条件后点击"导出"可导出筛选结果
- 勾选多条记录后点击"批量导出"可导出选中记录

### 审计日志

管理员可访问 `/logs` 页面查看所有操作日志。

## 🔧 脚本工具

### 数据导入脚本

```bash
python src/import_db.py
```

功能：从 `data/raw/loan_data.csv` 读取数据并导入到 MySQL 数据库。

### 数据库修复脚本

```bash
python src/fix_db.py
```

功能：检查并修复数据库表结构，添加缺失的字段。

### 日期修复脚本

```bash
python fix_mysql_date.py
```

功能：为数据库中的记录随机分配过去 6 个月内的日期，用于演示趋势图功能。

### 模型训练脚本

```bash
python src/train_model.py
```

功能：使用历史数据训练随机森林分类模型，用于贷款审批预测。

## 🔒 权限说明

### 管理员（admin）
- ✅ 查看所有数据
- ✅ 编辑贷款记录
- ✅ 删除贷款记录
- ✅ 批量审批
- ✅ 批量删除
- ✅ 查看审计日志

### 普通用户（user）
- ✅ 查看所有数据
- ✅ 新增贷款申请
- ✅ 导出数据
- ❌ 编辑/删除数据
- ❌ 审批操作
- ❌ 查看审计日志

## 📊 模型说明

系统使用 **随机森林（Random Forest）** 算法进行贷款审批预测。

### 特征变量
1. 申请金额（amount）
2. 信用评分（score）
3. 经营年份（years）
4. 月均营收（monthly_flow）
5. 月均成本（cost）
6. 月均客流量（traffic）

### 目标变量
- 1：通过审批
- 0：拒绝审批

### 模型训练
模型使用历史贷款数据进行训练，训练集和测试集按 8:2 划分。训练完成后会显示模型准确率。

## ⚠️ 注意事项

1. **数据库配置**：请确保 MySQL 服务已启动，且数据库连接信息正确
2. **模型文件**：首次运行前需要先训练模型，否则预测功能不可用
3. **数据格式**：CSV 导入时，系统会尝试自动匹配列名，建议列名包含关键词（如"金额"、"评分"等）
4. **权限控制**：管理员账户默认用户名为 `admin`，但需要先注册
5. **日志文件**：审计日志保存在 `system_audit.json`，建议定期备份

## 🐛 常见问题

### Q: 导入数据时提示列名不匹配
A: 检查 CSV 文件的列名是否包含关键词（如"金额"、"评分"、"城市"等），或手动运行 `src/fix_db.py` 修复数据库结构。

### Q: 模型预测功能无法使用
A: 确保已运行 `src/train_model.py` 训练模型，且 `data/model.pkl` 文件存在。

### Q: 图表显示无数据
A: 检查数据库中是否有数据，或运行 `fix_mysql_date.py` 为数据分配日期。

### Q: 登录后提示权限不足
A: 确保使用正确的身份登录（admin 需要选择"管理员"身份）。

## 📝 开发说明

### 添加新功能

1. 在 `app.py` 中添加路由和处理逻辑
2. 在 `templates/` 目录下创建或修改 HTML 模板
3. 如需数据库操作，使用 SQLAlchemy 进行查询和更新
4. 重要操作需要调用 `audit_utils.write_log()` 记录日志

### 扩展机器学习模型

1. 修改 `src/train_model.py` 中的特征选择
2. 调整模型参数（如 n_estimators）
3. 重新训练模型并替换 `data/model.pkl`

## 📄 许可证

本项目仅供学习和参考使用。

## 👥 贡献

欢迎提交 Issue 和 Pull Request 来改进本项目。

## 📞 联系方式

如有问题或建议，请通过 GitHub Issues 联系。

---

**最后更新**：2025年1月
