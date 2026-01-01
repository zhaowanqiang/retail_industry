import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# 1. 这里填你截图里 app.py 一模一样的 MySQL 连接地址
# 注意：一定要确认你的密码是 123456 还是别的，这里照抄你截图里的
DB_URI = "mysql+pymysql://root:123456@localhost:3306/retail_loan?charset=utf8mb4"

print(f"🔗 正在连接 MySQL 数据库...")
engine = create_engine(DB_URI)

# 2. 准备时间旅行
end_date = datetime.now()
start_date = end_date - timedelta(days=180)  # 过去半年


def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)


try:
    with engine.connect() as conn:
        # 3. 查出所有数据的 ID
        print("📊 正在读取数据...")
        result = conn.execute(text("SELECT id FROM loan_data"))
        ids = [row[0] for row in result]

        print(f"🔍 扫描到 {len(ids)} 条数据，正在修改日期...")

        # 4. 逐条修改日期
        for loan_id in ids:
            # 生成一个随机日期
            new_date = random_date(start_date, end_date).strftime('%Y-%m-%d')

            # 更新数据库 (注意 MySQL 的语法)
            conn.execute(
                text("UPDATE loan_data SET date = :date WHERE id = :id"),
                {"date": new_date, "id": loan_id}
            )

        conn.commit()
        print("-" * 30)
        print("✅ 成功！MySQL 里的数据日期已经全部打散。")
        print("🚀 现在去刷新网页，折线图应该就动起来了！")

except Exception as e:
    print(f"❌ 出错了: {e}")
    print("请检查：你的 MySQL 开启了吗？密码对不对？数据库名 retail_loan 对不对？")