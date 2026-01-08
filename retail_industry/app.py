from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
import io
import random
import json
import os
import pandas as pd
import joblib  # 用于加载 AI 模型
import numpy as np  # 用于处理数组
import pymysql
from sqlalchemy import create_engine, text
from flask import redirect, url_for
from datetime import datetime
from datetime import datetime, timedelta
import numpy as np  # 如果用到了数值计算
from audit_utils import read_logs, write_log

app = Flask(__name__)
app.secret_key = "123456"  # 随便写个密码
DB_URI = "mysql+pymysql://root:123456@localhost:3306/retail_loan?charset=utf8mb4"
db_engine = create_engine(DB_URI)
app.secret_key = 'your_secret_key'

DATA_PATH = 'data/raw/loan_data.csv'
USER_DATA_FILE = 'data/users.json'

# ▼▼▼▼▼▼ 新增：加载 AI 模型 ▼▼▼▼▼▼
MODEL_PATH = 'data/model.pkl'
model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        print("AI 模型加载成功！")
    except:
        print("警告：模型文件存在但加载失败。")
else:
    print("警告：未找到模型文件，请先运行 src/train_model.py")


# --- 用户功能 (保持不变) ---
def get_users():
    if not os.path.exists('data'): os.makedirs('data')
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f: json.dump([], f)
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def save_users(users):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


# ========================================================
# ▼▼▼ 完整修复版：统计准确，金额正常 (直接替换原函数) ▼▼▼
# ========================================================
def get_dashboard_data(page=1, per_page=10, search_query='', sort_column='id', sort_order='DESC', 
                       status_filter='', type_filter='', score_min='', score_max='', 
                       amount_min='', amount_max='', date_from='', date_to='', city_filter=''):
    # 1. 计算分页偏移量
    offset = (page - 1) * per_page

    # 2. 准备搜索条件（多条件筛选）
    conditions = []
    
    # 文本搜索（商户名/ID）
    if search_query:
        conditions.append(f"(id LIKE '%%{search_query}%%' OR name LIKE '%%{search_query}%%')")
    
    # 状态筛选
    if status_filter:
        conditions.append(f"status LIKE '%%{status_filter}%%'")
    
    # 行业类型筛选
    if type_filter:
        conditions.append(f"type = '{type_filter}'")
    
    # 城市筛选
    if city_filter:
        conditions.append(f"city = '{city_filter}'")
    
    # 信用分范围筛选
    if score_min:
        try:
            score_min_val = float(score_min)
            conditions.append(f"score >= {score_min_val}")
        except:
            pass
    if score_max:
        try:
            score_max_val = float(score_max)
            conditions.append(f"score <= {score_max_val}")
        except:
            pass
    
    # 金额范围筛选
    if amount_min:
        try:
            amount_min_val = float(amount_min)
            conditions.append(f"amount >= {amount_min_val}")
        except:
            pass
    if amount_max:
        try:
            amount_max_val = float(amount_max)
            conditions.append(f"amount <= {amount_max_val}")
        except:
            pass
    
    # 日期范围筛选
    if date_from:
        conditions.append(f"date >= '{date_from}'")
    if date_to:
        conditions.append(f"date <= '{date_to}'")
    
    # 组合WHERE子句
    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    # 3. 验证和准备排序参数（防止SQL注入）
    allowed_columns = ['id', 'name', 'type', 'amount', 'score', 'monthly_flow', 'date', 'status', 'city', 'traffic', 'cost']
    if sort_column not in allowed_columns:
        sort_column = 'id'
    
    if sort_order.upper() not in ['ASC', 'DESC']:
        sort_order = 'DESC'
    
    # 4. 获取当前页数据 (用于显示表格，支持排序)
    sql_data = f"SELECT * FROM loan_data {where_clause} ORDER BY {sort_column} {sort_order} LIMIT {per_page} OFFSET {offset}"
    df = pd.read_sql(sql_data, db_engine)

    # --- 数据清洗 (防止空值报错) ---
    numeric_cols = ['amount', 'score', 'monthly_flow', 'cost', 'traffic', 'years', 'employees', 'area']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df = df.fillna('')
    if 'date' not in df.columns:
        df['date'] = datetime.now().strftime('%Y-%m-%d')

    data = df.to_dict(orient='records')

    # 4. 计算总页数
    sql_total = f"SELECT COUNT(*) FROM loan_data {where_clause}"
    total_records = pd.read_sql(sql_total, db_engine).iloc[0, 0]
    total_pages = (total_records + per_page - 1) // per_page

    # 5. ★★★ 统计指标 (这里修复了核心逻辑) ★★★

    # (1) review_count (待人工复核)
    # 逻辑：只要状态里包含 '待'、'审核'、'Pending' 的都算进去，防止漏掉
    sql_review = """
        SELECT COUNT(*) FROM loan_data 
        WHERE status LIKE '%%审核%%' 
           OR status LIKE '%%待%%' 
           OR status = 'Pending'
    """
    review_count = pd.read_sql(sql_review, db_engine).iloc[0, 0]

    # (2) pass_amount (放款总额)
    # 逻辑：只统计状态包含 '通过' 的金额
    # ★关键修正：去掉了 / 10000，恢复原始大小
    try:
        sql_amount = "SELECT SUM(amount) FROM loan_data WHERE status LIKE '%%通过%%'"
        raw_amount = pd.read_sql(sql_amount, db_engine).iloc[0, 0]
        pass_amount = int(raw_amount) if raw_amount else 0
    except:
        pass_amount = 0

    # (3) reject_count (高风险/拒绝)
    # 逻辑：分数低于600 或者 状态包含 '拒绝'
    sql_reject = "SELECT COUNT(*) FROM loan_data WHERE score < 600 OR status LIKE '%%拒绝%%'"
    reject_count = pd.read_sql(sql_reject, db_engine).iloc[0, 0]

    # (4) avg_score (平均分)
    try:
        raw_score = pd.read_sql("SELECT AVG(score) FROM loan_data", db_engine).iloc[0, 0]
        avg_score = int(raw_score) if raw_score else 0
    except:
        avg_score = 0

    # (5) total_count (总单数)
    total_count = pd.read_sql("SELECT COUNT(*) FROM loan_data", db_engine).iloc[0, 0]

    # 6. 打包返回 (Key 必须与前端 HTML 对应)
    stats = {
        'total_count': total_count,
        'review_count': review_count,  # ✅ 对应前端 {{ stats.review_count }}
        'pass_amount': pass_amount,  # ✅ 对应前端 {{ stats.pass_amount }}
        'reject_count': reject_count,
        'avg_score': avg_score
    }

    return data, stats, total_pages


# --- 路由配置 ---
@app.route('/', methods=['GET'])
def index():
    return render_template('login.html')


# 修改 app.py 里的 dashboard 路由
@app.route('/dashboard')
def dashboard():
    # 1. 获取前端传来的参数
    page = request.args.get('page', 1, type=int)  # 页码，默认第1页
    query = request.args.get('q', '')
    sort_column = request.args.get('sort', 'id')  # 排序字段，默认按ID
    sort_order = request.args.get('order', 'DESC')  # 排序方向，默认降序
    
    # 筛选参数
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')
    score_min = request.args.get('score_min', '')
    score_max = request.args.get('score_max', '')
    amount_min = request.args.get('amount_min', '')
    amount_max = request.args.get('amount_max', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    city_filter = request.args.get('city', '')

    # 2. 获取用户身份 (权限控制的核心)
    # 从 session 里拿 role，拿不到就默认为 'user' (普通用户)
    current_role = session.get('role', 'user')
    # 从 session 里拿名字，拿不到就显示 '未登录'
    current_user_name = session.get('user_name', '未登录')

    data, stats, total_pages = get_dashboard_data(
        page=page, 
        search_query=query, 
        sort_column=sort_column, 
        sort_order=sort_order,
        status_filter=status_filter,
        type_filter=type_filter,
        score_min=score_min,
        score_max=score_max,
        amount_min=amount_min,
        amount_max=amount_max,
        date_from=date_from,
        date_to=date_to,
        city_filter=city_filter
    )

    # 3. 获取筛选选项数据（用于下拉框）
    try:
        # 获取所有行业类型
        types_df = pd.read_sql("SELECT DISTINCT type FROM loan_data WHERE type IS NOT NULL AND type != '' ORDER BY type", db_engine)
        type_options = types_df['type'].tolist() if not types_df.empty else []
        
        # 获取所有城市
        cities_df = pd.read_sql("SELECT DISTINCT city FROM loan_data WHERE city IS NOT NULL AND city != '' ORDER BY city", db_engine)
        city_options = cities_df['city'].tolist() if not cities_df.empty else []
        
        # 获取所有状态
        status_df = pd.read_sql("SELECT DISTINCT status FROM loan_data WHERE status IS NOT NULL AND status != '' ORDER BY status", db_engine)
        status_options = status_df['status'].tolist() if not status_df.empty else []
    except:
        type_options = []
        city_options = []
        status_options = []
    
    # 4. 这样 data=data 才能把真正的数据传过去
    return render_template('dashboard.html',
                           data=data,  # 如果 HTML 要 data，给它！
                           rows=data,  # ▼ 新增：如果 HTML 要 rows，也给它！
                           stats=stats,
                           current_page=page,
                           total_pages=total_pages,
                           search_query=query,
                           sort_column=sort_column,
                           sort_order=sort_order,
                           status_filter=status_filter,
                           type_filter=type_filter,
                           score_min=score_min,
                           score_max=score_max,
                           amount_min=amount_min,
                           amount_max=amount_max,
                           date_from=date_from,
                           date_to=date_to,
                           city_filter=city_filter,
                           type_options=type_options,
                           city_options=city_options,
                           status_options=status_options,
                           role=current_role,
                           user_name=current_user_name)


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    # ★★★ 1. 这里要读取确认密码框的值 ★★★
    confirm_password = request.form.get('confirm_password')

    input_role = request.form.get('role')
    action = request.form.get('action')

    users = get_users()

    # ============================
    #      注册逻辑 (Register)
    # ============================
    if action == 'register':
        # 1. 检查用户名是否已存在
        for u in users:
            if u['username'] == username:
                flash('该用户名已被注册，请更换', 'danger')
                return render_template('login.html')

        # ★★★ 2. 核心修复：检查两次密码是否一致 ★★★
        # 如果 密码 不等于 确认密码，直接报错并停止
        if password != confirm_password:
            flash('❌ 注册失败：两次输入的密码不一致！', 'danger')
            return render_template('login.html')

        # 3. 强制赋予 'user' 身份并保存
        users.append({"username": username, "password": password, "role": "user"})
        save_users(users)

        flash('✅ 注册成功，请直接登录', 'success')
        return render_template('login.html')

    # ============================
    #      登录逻辑 (Login)
    # ============================
    elif action == 'login':
        for u in users:
            if u['username'] == username and u['password'] == password:

                # 获取真实身份 (admin账号强制为admin，其他人读数据库)
                if u['username'] == 'admin':
                    real_role = 'admin'
                else:
                    real_role = u.get('role', 'user')

                # 身份校验 (防止普通用户选管理员登录)
                if input_role != real_role:
                    print(f"⚠️ 身份不匹配拦截: {username} 试图以 {input_role} 登录")
                    continue  # 跳过，视为登录失败

                # 登录成功
                session['user_name'] = u['username']
                session['role'] = real_role
                write_log(username, "登录系统", "用户身份验证通过", request.remote_addr)
                return redirect('/dashboard')

        # 循环结束没找到匹配的，报错
        flash('❌ 登录失败：用户名/密码错误 或 身份选择不正确', 'danger')
        return render_template('login.html')


# 1. 页面路由：只负责显示网页框架
@app.route('/analysis')
def analysis_page():
    # 安全检查：未登录就踢回登录页
    if 'user_name' not in session:
        return redirect(url_for('login'))

    # 这里的 active_page='analysis' 是为了让导航栏高亮
    return render_template('analysis.html', active_page='analysis')


@app.route('/api/analysis-data')
def get_analysis_data():
    try:
        # 1. 直接读取 MySQL 里的最新数据
        sql = "SELECT * FROM loan_data"
        df = pd.read_sql(sql, db_engine)

        # --- 数据清洗 (防止空值报错) ---
        cols_to_fix = ['score', 'monthly_flow', 'assets', 'amount']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # ===================================
        # ★ 图表 1：业务增长趋势 (Trend)
        # ===================================
        today = datetime.now()
        trend_labels = []
        trend_data = []

        # 倒推过去 6 个月
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=i * 30)
            month_str = month_date.strftime('%Y-%m')  # 例如 "2025-08"
            trend_labels.append(month_str)

            if 'date' in df.columns:
                # 统计当月单量
                count = len(df[df['date'].astype(str).str.contains(month_str)])
                trend_data.append(count)
            else:
                trend_data.append(0)

        # ===================================
        # ★ 图表 2：雷达图数据 (Radar)
        # ===================================
        # A. 优质客户 (状态包含'通过')
        good_df = df[df['status'].astype(str).str.contains('通过')]
        if not good_df.empty:
            good_stats = [
                round(good_df['score'].mean(), 1),  # 信用分
                round(good_df['monthly_flow'].mean(), 1),  # 流水
                round(good_df.get('assets', pd.Series([0])).mean(), 1)  # 资产
            ]
        else:
            good_stats = [0, 0, 0]

        # B. 风险客户 (状态包含'拒绝'或'未通过')
        bad_df = df[df['status'].astype(str).str.contains('拒绝|未通过', regex=True)]
        if not bad_df.empty:
            bad_stats = [
                round(bad_df['score'].mean(), 1),
                round(bad_df['monthly_flow'].mean(), 1),
                round(bad_df.get('assets', pd.Series([0])).mean(), 1)
            ]
        else:
            bad_stats = [0, 0, 0]

        # ===================================
        # ★★★ 新增：AI 智能洞察计算 (Insight) ★★★
        # ===================================

        # 1. 计算通过用户的平均信用分
        avg_pass_score = int(good_df['score'].mean()) if not good_df.empty else 0

        # 2. 计算“拒单率最高”的行业
        # 逻辑：在被拒绝的人里，统计哪个行业(type)出现的次数最多
        risky_industry = "暂无数据"
        if 'type' in df.columns and not bad_df.empty:
            risky_industry = bad_df['type'].value_counts().idxmax()

        # 3. 总分析条数
        total_count = len(df)

        # ===================================
        # ★ 图表 3：柱状图数据 (Bar Chart) - 按行业类型分组统计（金额+数量+平均分）
        # ===================================
        bar_labels = []
        bar_amount_data = []
        bar_count_data = []
        bar_score_data = []

        if 'type' in df.columns:
            # 按行业类型分组统计
            type_stats = df.groupby('type').agg({
                'amount': 'sum',  # 放款总额
                'id': 'count',  # 申请数量
                'score': 'mean'  # 平均信用分
            }).sort_values('amount', ascending=False).head(6)  # 取前6个行业

            bar_labels = type_stats.index.tolist()
            bar_amount_data = [int(x) for x in type_stats['amount'].values.tolist()]
            bar_count_data = type_stats['id'].values.tolist()
            bar_score_data = [round(x, 1) for x in type_stats['score'].values.tolist()]
        else:
            bar_labels = ['零售行业', '其他行业']
            bar_amount_data = [0, 0]
            bar_count_data = [0, 0]
            bar_score_data = [0, 0]

        # ===================================
        # ★ 图表 4：饼图数据 (Pie Chart) - 按状态分布（数量+金额占比）
        # ===================================
        pie_labels = []
        pie_count_data = []
        pie_amount_data = []

        if 'status' in df.columns:
            # 统计各状态的数量
            status_counts = df['status'].value_counts()
            pie_labels = status_counts.index.tolist()
            pie_count_data = status_counts.values.tolist()

            # 统计各状态的金额
            if 'amount' in df.columns:
                status_amounts = df.groupby('status')['amount'].sum()
                # 按照pie_labels的顺序提取金额
                pie_amount_data = [int(status_amounts.get(label, 0)) for label in pie_labels]
            else:
                pie_amount_data = [0] * len(pie_labels)
        else:
            pie_labels = ['通过', '待审核', '拒绝']
            pie_count_data = [0, 0, 0]
            pie_amount_data = [0, 0, 0]

        return jsonify({
            'trend': {'labels': trend_labels, 'data': trend_data},
            'radar': {'good': good_stats, 'bad': bad_stats},
            # ▼ 改进：柱状图数据（分组数据）
            'bar': {
                'labels': bar_labels,
                'amounts': bar_amount_data,  # 放款金额
                'counts': bar_count_data,  # 申请数量
                'scores': bar_score_data  # 平均信用分
            },
            # ▼ 改进：饼图数据（数量+金额）
            'pie': {
                'labels': pie_labels,
                'counts': pie_count_data,  # 各状态的数量
                'amounts': pie_amount_data  # 各状态的金额
            },

            # ▼ 把算好的结论传给前端
            'insight': {
                'total_checked': total_count,
                'avg_score': avg_pass_score,
                'risky_industry': risky_industry
            }
        })

    except Exception as e:
        print(f"可视化数据报错: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/prediction', methods=['GET', 'POST'])  # AI预测模型
def prediction():
    result = None
    if request.method == 'POST':
        # 1. 获取表单数据
        try:
            # 获取用户输入的 6 个指标
            amount = float(request.form.get('amount', 0))
            score = float(request.form.get('score', 0))
            years = float(request.form.get('years', 0))
            monthly_flow = float(request.form.get('monthly_flow', 0))
            cost = float(request.form.get('cost', 0))
            traffic = float(request.form.get('traffic', 0))

            # 2. 构造模型需要的数组 (顺序必须和训练时一样!)
            # 格式是二维数组： [[特征1, 特征2, ...]]
            input_data = np.array([[amount, score, years, monthly_flow, cost, traffic]])

            # 3. 进行预测
            if model:
                pred = model.predict(input_data)[0]  # 结果是 0 或 1
                proba = model.predict_proba(input_data)[0][1]  # 获取"通过"的概率 (0.x)
                
                # 获取特征重要性
                feature_names = ['注册金额', '企业信用评分', '经营年份', '月均营收', '月均成本', '月均客流量']
                feature_importance = {}
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                    for i, name in enumerate(feature_names):
                        feature_importance[name] = round(float(importances[i]) * 100, 2)
                
                # 计算额外指标
                profit_margin = round((monthly_flow - cost) / monthly_flow * 100, 2) if monthly_flow > 0 else 0
                profit_per_customer = round((monthly_flow - cost) / traffic, 2) if traffic > 0 else 0
                
                result = {
                    "is_pass": int(pred),  # 1是通过，0是拒绝
                    "probability": round(proba * 100, 1),  # 变成百分数，保留1位小数
                    "feature_importance": feature_importance,  # 特征重要性
                    "profit_margin": profit_margin,  # 利润率
                    "profit_per_customer": profit_per_customer,  # 单客利润
                    "input_data": {
                        "amount": amount,
                        "score": score,
                        "years": years,
                        "monthly_flow": monthly_flow,
                        "cost": cost,
                        "traffic": traffic
                    }
                }
            else:
                flash("模型未加载，无法预测，请检查后台日志")
        except Exception as e:
            flash(f"输入数据有误: {e}")

    return render_template('prediction.html', result=result)


@app.route('/api/prediction', methods=['POST'])  # AJAX API接口
def api_prediction():
    """AJAX接口，返回JSON格式的预测结果"""
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        score = float(data.get('score', 0))
        years = float(data.get('years', 0))
        monthly_flow = float(data.get('monthly_flow', 0))
        cost = float(data.get('cost', 0))
        traffic = float(data.get('traffic', 0))

        input_data = np.array([[amount, score, years, monthly_flow, cost, traffic]])

        if not model:
            return jsonify({"error": "模型未加载"}), 500

        pred = model.predict(input_data)[0]
        proba = model.predict_proba(input_data)[0][1]
        
        # 获取特征重要性
        feature_names = ['注册金额', '企业信用评分', '经营年份', '月均营收', '月均成本', '月均客流量']
        feature_importance = []
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            for i, name in enumerate(feature_names):
                feature_importance.append({
                    "name": name,
                    "importance": round(float(importances[i]) * 100, 2)
                })
        
        # 计算额外指标
        profit_margin = round((monthly_flow - cost) / monthly_flow * 100, 2) if monthly_flow > 0 else 0
        profit_per_customer = round((monthly_flow - cost) / traffic, 2) if traffic > 0 else 0
        
        # 生成优化建议
        suggestions = []
        if pred == 0:  # 被拒绝的情况
            if score < 600:
                suggestions.append("建议提升企业信用评分至600分以上")
            if profit_margin < 20:
                suggestions.append(f"当前利润率{profit_margin}%较低，建议优化成本结构或提升营收")
            if years < 3:
                suggestions.append("经营年限较短，建议提供更多经营历史证明")
            if monthly_flow < cost:
                suggestions.append("月均营收低于成本，存在经营风险，需改善盈利模式")
            if traffic < 1000:
                suggestions.append("客流量偏低，建议加强营销推广")
        
        return jsonify({
            "success": True,
            "result": {
                "is_pass": int(pred),
                "probability": round(proba * 100, 1),
                "feature_importance": feature_importance,
                "profit_margin": profit_margin,
                "profit_per_customer": profit_per_customer,
                "suggestions": suggestions,
                "risk_level": "低风险" if proba > 0.7 else ("中风险" if proba > 0.4 else "高风险")
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# 导出 Excel 的功能
@app.route('/export')
def export_data():
    try:
        # 1. 获取搜索词或批量ID（支持批量导出）
        query = request.args.get('q', '')
        ids_param = request.args.get('ids', '')  # 批量导出：ids=id1,id2,id3

        # 2. 构造 SQL 语句
        sql = "SELECT * FROM loan_data WHERE 1=1"

        # 优先使用批量ID导出
        if ids_param:
            ids_list = ids_param.split(',')
            # 过滤空值并构建IN子句
            ids_list = [id.strip() for id in ids_list if id.strip()]
            if ids_list:
                placeholders = ','.join([f"'{id}'" for id in ids_list])
                sql += f" AND id IN ({placeholders})"
        elif query:
            query = str(query).strip()
            sql += f" AND (name LIKE '%%{query}%%' OR id LIKE '%%{query}%%')"

        # 3. 读数据
        df = pd.read_sql(sql, db_engine)

        # 4. 简单清洗 (把数字列的空值填为0，防止 Excel 里看着难受)
        numeric_cols = ['amount', 'score', 'monthly_flow', 'cost', 'traffic']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 4. 检查是否有数据
        if df.empty:
            return "没有可导出的数据", 400

        # 5. 写入内存中的 Excel (不存硬盘，直接发给用户)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='贷款数据')

        # 指针回到文件开头，准备读取
        output.seek(0)

        # 6. 根据导出类型生成文件名
        if ids_param:
            filename = f'批量导出数据_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        else:
            filename = f'贷款数据报表_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx'

        # 7. 发送文件给浏览器下载
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"导出失败: {e}")
        return f"导出出错: {e}"


# 删除功能
@app.route('/delete/<id>', methods=['POST'])
def delete_loan(id):
    if session.get('role') != 'admin':
        return "❌ 权限不足：只有管理员可以删除数据！"
    try:
        # 连接数据库
        with db_engine.connect() as conn:
            # 执行 SQL 删除语句 (使用 :id 占位符防止注入攻击，虽然是内网项目也要养成好习惯)
            conn.execute(text("DELETE FROM loan_data WHERE id = :id"), {"id": id})
            conn.commit()  # 提交修改，一定要有这句，否则删不掉

        print(f"已删除 ID: {id}")
    except Exception as e:
        print(f"删除失败: {e}")

    # 删完之后，刷新当前页面
    return redirect('/dashboard')


# ==========================================
# ▼▼▼ 批量操作功能 API ▼▼▼
# ==========================================

# 批量审批
@app.route('/api/batch-approve', methods=['POST'])
def batch_approve():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': '权限不足：只有管理员可以进行批量审批操作！'}), 403

    try:
        data = request.get_json()
        ids = data.get('ids', [])

        if not ids or len(ids) == 0:
            return jsonify({'success': False, 'error': '未选择任何记录'}), 400

        # 批量更新状态为"通过"
        approved_count = 0
        with db_engine.connect() as conn:
            for id in ids:
                try:
                    conn.execute(text("UPDATE loan_data SET status = '通过' WHERE id = :id"), {"id": id})
                    approved_count += 1
                except Exception as e:
                    print(f"审批 ID {id} 失败: {e}")
                    continue
            conn.commit()

        # 记录操作日志
        if approved_count > 0:
            write_log(session.get('user_name', 'admin'),
                      f"批量审批",
                      f"成功审批 {approved_count} 条记录",
                      request.remote_addr)

        return jsonify({
            'success': True,
            'approved_count': approved_count,
            'total_count': len(ids)
        })

    except Exception as e:
        print(f"批量审批失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# 批量删除
@app.route('/api/batch-delete', methods=['POST'])
def batch_delete():
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': '权限不足：只有管理员可以进行批量删除操作！'}), 403

    try:
        data = request.get_json()
        ids = data.get('ids', [])

        if not ids or len(ids) == 0:
            return jsonify({'success': False, 'error': '未选择任何记录'}), 400

        # 批量删除
        deleted_count = 0
        with db_engine.connect() as conn:
            for id in ids:
                try:
                    conn.execute(text("DELETE FROM loan_data WHERE id = :id"), {"id": id})
                    deleted_count += 1
                except Exception as e:
                    print(f"删除 ID {id} 失败: {e}")
                    continue
            conn.commit()

        # 记录操作日志
        if deleted_count > 0:
            write_log(session.get('user_name', 'admin'),
                      f"批量删除",
                      f"成功删除 {deleted_count} 条记录",
                      request.remote_addr)

        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'total_count': len(ids)
        })

    except Exception as e:
        print(f"批量删除失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/add', methods=['POST'])
def add_loan():
    try:
        # 1. 获取所有字段
        name = request.form.get('name')
        amount = request.form.get('amount')
        score = request.form.get('score')
        type_ = request.form.get('type')
        monthly_flow = request.form.get('monthly_flow') or 0
        city = request.form.get('city') or '未知'
        # ▼ 新增获取这俩字段
        traffic = request.form.get('traffic') or 0
        cost = request.form.get('cost') or 0

        # 2. 生成 ID
        current_date = datetime.now().strftime('%Y%m%d')
        random_suffix = random.randint(1000, 9999)
        new_id = f"RETL-{current_date}-{random_suffix}"

        # 3. SQL 插入语句 (不再写死 0 了！)
        # 注意 VALUES 里的 :traffic 和 :cost
        sql = """
            INSERT INTO loan_data 
            (id, name, amount, score, type, status, date, monthly_flow, city, traffic, cost, city_level, years, employees, area)
            VALUES 
            (:id, :name, :amount, :score, :type, '待审核', CURDATE(), :monthly_flow, :city, :traffic, :cost, '一线', 1, 5, 50)
        """

        # 4. 执行写入
        with db_engine.connect() as conn:
            conn.execute(text(sql), {
                "id": new_id,
                "name": name,
                "amount": amount,
                "score": score,
                "type": type_,
                "monthly_flow": monthly_flow,
                "city": city,
                "traffic": traffic,  # ▼ 传进去
                "cost": cost  # ▼ 传进去
            })
            conn.commit()

        print(f"✅ 新增成功: {name}")

    except Exception as e:
        print(f"❌ 新增失败: {e}")

    return redirect('/dashboard')


# 新增：编辑/更新数据功能
@app.route('/update', methods=['POST'])
def update_loan():
    if session.get('role') != 'admin':
        return "❌ 权限不足：只有管理员可以修改数据！"
    try:
        # 1. 获取 ID (这是关键，告诉数据库我们要改哪一条)
        id = request.form.get('id')

        # 2. 获取其他要修改的字段
        name = request.form.get('name')
        amount = request.form.get('amount')
        score = request.form.get('score')
        type_ = request.form.get('type')
        monthly_flow = request.form.get('monthly_flow') or 0
        cost = request.form.get('cost') or 0
        traffic = request.form.get('traffic') or 0
        city = request.form.get('city')

        # 3. 编写 SQL 更新语句 (UPDATE ... SET ...)
        sql = """
            UPDATE loan_data 
            SET name=:name, amount=:amount, score=:score, type=:type, 
                monthly_flow=:monthly_flow, cost=:cost, traffic=:traffic, city=:city
            WHERE id=:id
        """

        # 4. 执行更新
        with db_engine.connect() as conn:
            conn.execute(text(sql), {
                "id": id,
                "name": name,
                "amount": amount,
                "score": score,
                "type": type_,
                "monthly_flow": monthly_flow,
                "cost": cost,
                "traffic": traffic,
                "city": city
            })
            conn.commit()

        print(f"✅ 数据更新成功: {id}")

    except Exception as e:
        print(f"❌ 更新失败: {e}")

    # 修改完跳回原来的页面
    return redirect('/dashboard')


@app.route('/approve/<id>')
def approve_loan(id):
    # ★★★ 核心修改：权限检查 ★★★
    # 如果当前登录的不是 admin，直接拦截并踢回首页
    if session.get('user_name') != 'admin':
        flash('❌ 权限不足：只有管理员可以进行审核操作！', 'danger')
        return redirect(url_for('dashboard'))

    # --- 原有逻辑保持不变 ---
    try:
        with db_engine.connect() as conn:
            conn.execute(text("UPDATE loan_data SET status = '通过' WHERE id = :id"), {"id": id})
            conn.commit()
        flash('审批成功！已标记为通过状态', 'success')

    except Exception as e:
        print(f"审批失败: {e}")
        flash('审批出错，请重试', 'danger')

    return redirect(url_for('dashboard'))


@app.route('/logs')
def show_logs():
    # 1. 权限拦截：只有 admin 能看日志
    if session.get('role') != 'admin':
        flash('❌ 权限不足：只有管理员可以查看审计日志', 'danger')
        return redirect('/dashboard')

    # 2. 从 audit_utils.py 读取数据
    logs_data = read_logs()

    # 3. 渲染页面
    return render_template('audit_logs.html', logs=logs_data)


# ==========================================
# ▼▼▼ 个人中心 (真实修改数据库版) ▼▼▼
# ==========================================
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_name' not in session:
        return redirect(url_for('login'))

    # 1. 定义数据库文件路径 (和你的登录逻辑保持一致)
    DATA_FILE = 'data/users.json'

    if request.method == 'POST':
        new_pass = request.form.get('new_password')
        confirm_pass = request.form.get('confirm_password')
        new_email = request.form.get('email')

        # --- 读取现有数据 ---
        users = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                users = json.load(f)

        # --- 寻找当前用户并修改 ---
        current_user = session['user_name']
        user_found = False

        for u in users:
            if u['username'] == current_user:
                user_found = True

                # A. 修改邮箱 (如果有填)
                if new_email:
                    u['email'] = new_email

                    # B. 修改密码 (如果有填)
                if new_pass:
                    if new_pass != confirm_pass:
                        flash('❌ 修改失败：两次输入的密码不一致', 'danger')
                        return render_template('profile.html', user_name=current_user, role=session.get('role'))
                    else:
                        u['password'] = new_pass
                        flash('✅ 密码已修改！下次登录请使用新密码', 'success')

                # C. 如果只改了邮箱没改密码
                if new_email and not new_pass:
                    flash('✅ 个人资料已更新', 'success')

                break  # 找到了就停止循环

        if not user_found:
            flash('❌ 系统错误：未找到当前用户数据', 'danger')

        # --- ★★★ 关键一步：写入保存到文件 ★★★ ---
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)

    return render_template('profile.html',
                           user_name=session.get('user_name'),
                           role=session.get('role'))


# =========================================================
# ▼▼▼ 最终修正版：只有“通过”的单子才算进放款总额 ▼▼▼
# =========================================================
@app.route('/api/kpi_trends')
def kpi_trends():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        database='retail_loan',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        today = datetime.now().date()
        last_week_start = today - timedelta(days=7)
        
        with conn.cursor() as cursor:
            # 1. 查总申请单数 (当前和上周对比)
            cursor.execute("SELECT COUNT(*) as c FROM loan_data")
            total_count = cursor.fetchone()['c']
            
            # 计算7天前的总数（用于对比）
            cursor.execute("SELECT COUNT(*) as c FROM loan_data WHERE date < %s", (last_week_start,))
            last_week_count = cursor.fetchone()['c']
            # 计算增长率：相对于7天前的数据
            count_change = ((total_count - last_week_count) / last_week_count * 100) if last_week_count > 0 else 0
            count_trend_dir = 'up' if count_change > 0 else ('down' if count_change < 0 else 'flat')
            count_trend_val = f"{abs(count_change):.1f}%"

            # 2. 查放款总额 (当前和上周对比)
            cursor.execute("SELECT SUM(amount) as m FROM loan_data WHERE status = '通过'")
            res_amount = cursor.fetchone()['m']
            total_amount = float(res_amount) if res_amount else 0
            
            cursor.execute("SELECT SUM(amount) as m FROM loan_data WHERE status = '通过' AND date < %s", (last_week_start,))
            res_last_amount = cursor.fetchone()['m']
            last_week_amount = float(res_last_amount) if res_last_amount else 0
            amount_change = ((total_amount - last_week_amount) / last_week_amount * 100) if last_week_amount > 0 else 0
            amount_trend_dir = 'up' if amount_change > 0 else ('down' if amount_change < 0 else 'flat')
            amount_trend_val = f"{abs(amount_change):.1f}%"

            # 3. 查平均信用分 (当前和上周对比)
            cursor.execute("SELECT AVG(score) as s FROM loan_data")
            res_score = cursor.fetchone()['s']
            avg_score = float(res_score) if res_score else 0
            
            cursor.execute("SELECT AVG(score) as s FROM loan_data WHERE date < %s", (last_week_start,))
            res_last_score = cursor.fetchone()['s']
            last_week_score = float(res_last_score) if res_last_score else 0
            score_change = ((avg_score - last_week_score) / last_week_score * 100) if last_week_score > 0 else 0
            score_trend_dir = 'up' if score_change > 0 else ('down' if score_change < 0 else 'flat')
            score_trend_val = f"{abs(score_change):.1f}%"

            # 4. 查"待人工复核" (当前和上周对比)
            cursor.execute("SELECT COUNT(*) as w FROM loan_data WHERE status = '待审核'")
            wait_review_count = cursor.fetchone()['w']
            
            cursor.execute("SELECT COUNT(*) as w FROM loan_data WHERE status = '待审核' AND date < %s", (last_week_start,))
            last_week_review = cursor.fetchone()['w']
            review_change = ((wait_review_count - last_week_review) / last_week_review * 100) if last_week_review > 0 else 0
            review_trend_dir = 'up' if review_change > 0 else ('down' if review_change < 0 else 'flat')
            review_trend_val = f"{abs(review_change):.1f}%"
            
            # 5. 获取最近7天的数据用于趋势图
            cursor.execute("""
                SELECT DATE(date) as day, COUNT(*) as count 
                FROM loan_data 
                WHERE date >= %s 
                GROUP BY DATE(date) 
                ORDER BY day
            """, (last_week_start,))
            daily_counts = cursor.fetchall()
            
            cursor.execute("""
                SELECT DATE(date) as day, SUM(amount) as amount 
                FROM loan_data 
                WHERE date >= %s AND status = '通过'
                GROUP BY DATE(date) 
                ORDER BY day
            """, (last_week_start,))
            daily_amounts = cursor.fetchall()

    finally:
        conn.close()

    # 处理趋势数据（填充缺失的日期）
    count_data = [0] * 7
    amount_data = [0] * 7
    for i in range(7):
        day = last_week_start + timedelta(days=i)
        day_str = day.strftime('%Y-%m-%d')
        # 查找对应日期的数据
        for item in daily_counts:
            if item['day'].strftime('%Y-%m-%d') == day_str:
                count_data[i] = item['count']
                break
        for item in daily_amounts:
            if item['day'].strftime('%Y-%m-%d') == day_str:
                amount_data[i] = float(item['amount']) if item['amount'] else 0
                break

    return jsonify({
        'total_count': total_count,
        'count_trend': {'val': count_trend_val, 'dir': count_trend_dir},
        'count_sparkline': count_data,

        'wait_review': wait_review_count,
        'review_trend': {'val': review_trend_val, 'dir': review_trend_dir},

        'total_amount': int(total_amount),
        'amount_trend': {'val': amount_trend_val, 'dir': amount_trend_dir},
        'amount_sparkline': amount_data,

        'avg_score': int(avg_score),
        'score_trend': {'val': score_trend_val, 'dir': score_trend_dir}
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)