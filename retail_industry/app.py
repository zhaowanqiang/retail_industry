from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session, jsonify
import io
import random
import json
import os
import pandas as pd
import joblib   # 用于加载 AI 模型
import numpy as np  # 用于处理数组
import pymysql
from sqlalchemy import create_engine, text
from flask import redirect, url_for
from datetime import datetime
from datetime import datetime, timedelta
import numpy as np  # 如果用到了数值计算

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
def get_dashboard_data(page=1, per_page=10, search_query=''):
    # 1. 计算分页偏移量
    offset = (page - 1) * per_page

    # 2. 准备搜索条件
    where_clause = ""
    if search_query:
        where_clause = f" WHERE id LIKE '%%{search_query}%%' OR name LIKE '%%{search_query}%%'"

    # 3. 获取当前页数据 (用于显示表格)
    sql_data = f"SELECT * FROM loan_data {where_clause} ORDER BY id DESC LIMIT {per_page} OFFSET {offset}"
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

    # 2. 获取用户身份 (权限控制的核心)
    # 从 session 里拿 role，拿不到就默认为 'user' (普通用户)
    current_role = session.get('role', 'user')
    # 从 session 里拿名字，拿不到就显示 '未登录'
    current_user_name = session.get('user_name', '未登录')

    data, stats, total_pages = get_dashboard_data(page=page, search_query=query)

    # 2. 这样 data=data 才能把真正的数据传过去
    return render_template('dashboard.html',
                           data=data,  # 如果 HTML 要 data，给它！
                           rows=data,  # ▼ 新增：如果 HTML 要 rows，也给它！
                           stats=stats,
                           current_page=page,
                           total_pages=total_pages,
                           search_query=query,
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

        return jsonify({
            'trend': {'labels': trend_labels, 'data': trend_data},
            'radar': {'good': good_stats, 'bad': bad_stats},

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
                proba = model.predict_proba(input_data)[0][1]  # 获取“通过”的概率 (0.x)

                result = {
                    "is_pass": int(pred),  # 1是通过，0是拒绝
                    "probability": round(proba * 100, 1)  # 变成百分数，保留1位小数
                }
            else:
                flash("模型未加载，无法预测，请检查后台日志")
        except Exception as e:
            flash(f"输入数据有误: {e}")

    return render_template('prediction.html', result=result)


# 导出 Excel 的功能
@app.route('/export')
def export_data():
    try:
        # 1. 获取搜索词（这样用户搜什么，就导什么，体验很好）
        query = request.args.get('q', '')

        # 2. 构造 SQL 语句 (和 Dashboard 逻辑一样)
        sql = "SELECT * FROM loan_data WHERE 1=1"
        if query:
            query = str(query).strip()
            sql += f" AND (name LIKE '%%{query}%%' OR id LIKE '%%{query}%%')"

        # 3. 读数据
        df = pd.read_sql(sql, db_engine)

        # 4. 简单清洗 (把数字列的空值填为0，防止 Excel 里看着难受)
        numeric_cols = ['amount', 'score', 'monthly_flow', 'cost', 'traffic']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 5. 写入内存中的 Excel (不存硬盘，直接发给用户)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='贷款数据')

        # 指针回到文件开头，准备读取
        output.seek(0)

        # 6. 发送文件给浏览器下载
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'贷款数据报表_{pd.Timestamp.now().strftime("%Y%m%d")}.xlsx'
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


if __name__ == '__main__':
    app.run(debug=True, port=5000)