from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
import io
import random
import json
import os
import pandas as pd
import joblib   # 用于加载 AI 模型
import numpy as np # 用于处理数组
import pymysql
from sqlalchemy import create_engine, text
from flask import redirect, url_for
from datetime import datetime

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


# 修改 app.py 里的 get_dashboard_data 函数
def get_dashboard_data(page=1, per_page=10, search_query=''):
    try:
        # 1. 构造 SQL
        sql = "SELECT * FROM loan_data WHERE 1=1"

        if search_query:
            search_query = str(search_query).strip()
            sql += f" AND (name LIKE '%%{search_query}%%' OR id LIKE '%%{search_query}%%')"

        # 2. 读取数据库
        df = pd.read_sql(sql, db_engine)

        # =======================================================
        # ▼▼▼ 修复核心：更聪明的空值填充 ▼▼▼
        # =======================================================

        # A. 先处理【数字列】：把空值变成 0，确保全是数字，不会报错
        numeric_cols = ['amount', 'score', 'monthly_flow', 'cost', 'traffic', 'years', 'employees', 'area']
        for col in numeric_cols:
            if col in df.columns:
                # errors='coerce' 会把读不出来的脏数据变成 NaN，然后 fillna(0) 变成 0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # B. 再处理【其他列】（比如商户名、ID）：把空值变成空文字
        df = df.fillna('')

        # C. 补充日期列（如果缺的话）
        if 'date' not in df.columns:
            df['date'] = '2025-01-01'

        # =======================================================

        # 3. 分页逻辑
        total_count = len(df)
        total_pages = (total_count + per_page - 1) // per_page

        if page < 1: page = 1
        if page > total_pages and total_pages > 0: page = total_pages

        start = (page - 1) * per_page
        end = start + per_page
        df_page = df.iloc[start:end]

        # 4. 统计指标
        stats = {
            "total_count": total_count,
            "review_count": 0,
            "pass_amount": 0,
            "reject_count": 0,
            "avg_score": 0
        }

        if not df.empty:
            if 'status' in df.columns:
                stats["review_count"] = len(df[df['status'].astype(str).str.contains('复核', na=False)])
                stats["reject_count"] = len(df[df['status'].astype(str).str.contains('拒绝|未通过', na=False)])

            if 'amount' in df.columns and 'status' in df.columns:
                # 现在 amount 肯定是数字了，求和绝对不会报错
                valid_pass = df[df['status'].astype(str).str.contains('通过', na=False)]
                stats["pass_amount"] = int(valid_pass['amount'].sum())

            if 'score' in df.columns:
                stats["avg_score"] = int(df['score'].mean())

        return df_page.to_dict(orient='records'), stats, total_pages

    except Exception as e:
        # 这里建议打印详细错误，方便调试
        print(f"❌ 数据库读取出错: {e}")
        return [], {}, 1


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
    role = request.form.get('role')
    action = request.form.get('action')

    users = get_users()

    if action == 'register':
        for u in users:
            if u['username'] == username:
                flash('用户名已存在')
                return redirect(url_for('index'))
        users.append({"username": username, "password": password, "role": role})
        save_users(users)
        flash('注册成功')
        return redirect(url_for('index'))

    elif action == 'login':
        for u in users:
            # 找到匹配的用户
            if u['username'] == username and u['password'] == password:

                # ▼▼▼ 修改开始：把身份信息存进 session ▼▼▼
                session['user_name'] = u['username']

                # 1. 如果用户名是 admin，直接给管理员权限 (为了方便你测试)
                if u['username'] == 'admin':
                    session['role'] = 'admin'
                else:
                    # 2. 否则，读取当初注册时存的 role，如果没有就默认是 user
                    session['role'] = u.get('role', 'user')

                print(f"✅ 登录成功: {username}, 身份: {session['role']}")
                return redirect('/dashboard')
                # ▲▲▲ 修改结束 ▲▲▲

        flash('用户名或密码错误')
        return redirect('/index')  # 或者 '/login'


# === 新增路由：数据可视化分析 ===
@app.route('/analysis')
def analysis():
    # 1. 还是先读取数据 (复用之前的逻辑，建议把读取逻辑封装，但为了简单这里再写一遍)
    if not os.path.exists(DATA_PATH):
        return "数据文件不存在"

    try:
        df = pd.read_csv(DATA_PATH, encoding='utf-8')
    except:
        try:
            df = pd.read_csv(DATA_PATH, encoding='gbk')
        except:
            return "数据读取失败"

    # 清理列名 (和之前一样，确保能取到数据)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        '零售品类': 'name', '餐饮品类': 'name', '行业名称': 'type',
        '企业信用评分': 'score', '所在城市': 'city'
    })

    # === 2. 准备图表数据 ===

    # (A) 图表1：行业分布 (统计每个行业有多少条数据)
    # 结果格式：[{'name': '餐饮', 'value': 100}, {'name': '零售', 'value': 50}...]
    type_counts = df['type'].value_counts()
    industry_data = [{'name': idx, 'value': int(val)} for idx, val in type_counts.items()]

    # (B) 图表2：信用分区间分布
    # 我们把分数分成几档: <600, 600-700, 700-800, >800
    # 先确保是数字
    if 'score' in df.columns:
        df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0)
        bins = [0, 600, 700, 800, 10000]
        labels = ['600分以下', '600-700分', '700-800分', '800分以上']
        # cut函数自动分箱
        score_groups = pd.cut(df['score'], bins=bins, labels=labels).value_counts().sort_index()
        score_x = score_groups.index.tolist()
        score_y = score_groups.values.tolist()
    else:
        score_x = []
        score_y = []

    # (C) 图表3：城市申请量 TOP 10
    if 'city' in df.columns:
        city_counts = df['city'].value_counts().head(10) # 只取前10个城市
        city_names = city_counts.index.tolist()
        city_vals = city_counts.values.tolist()
    else:
        city_names = []
        city_vals = []

    # 3. 渲染页面，把数据传过去
    return render_template('analysis.html',
                           industry_data=industry_data,
                           score_x=score_x,
                           score_y=score_y,
                           city_names=city_names,
                           city_counts=city_vals)


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


if __name__ == '__main__':
    app.run(debug=True, port=5000)