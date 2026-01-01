import pandas as pd
from sqlalchemy import create_engine
import re
import os

# 1. 数据库配置
DB_URI = "mysql+pymysql://root:123456@localhost:3306/retail_loan?charset=utf8mb4"
engine = create_engine(DB_URI)


def import_data():
    print("🚀 启动智能修复模式...")

    # 自动找文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, '..', 'data', 'raw', 'loan_data.csv')

    try:
        # 读取 CSV
        df = pd.read_csv(csv_path, encoding='utf-8')
        print(f"✅ 读取成功，共 {len(df)} 行")
        print("📄 你的原始列名:", df.columns.tolist())  # 打印出来让你看看

        # === 核心修改：模糊匹配 (Smart Mapping) ===
        # 不再去猜具体的标点符号，只要名字里带核心词，就认领！
        new_columns = {}
        for col in df.columns:
            c = str(col).strip()  # 去掉空格

            # 关键词匹配逻辑 (顺序很重要)
            if 'ID' in c:
                new_columns[col] = 'id'
            elif '金额' in c:
                new_columns[col] = 'amount'
            elif '评分' in c:
                new_columns[col] = 'score'
            elif '营收' in c:
                new_columns[col] = 'monthly_flow'
            elif '成本' in c:
                new_columns[col] = 'cost'
            elif '客流' in c:
                new_columns[col] = 'traffic'
            elif '面积' in c:
                new_columns[col] = 'area'
            elif '员工' in c:
                new_columns[col] = 'employees'
            elif '年份' in c:
                new_columns[col] = 'years'
            elif '等级' in c:
                new_columns[col] = 'city_level'
            elif '城市' in c:
                new_columns[col] = 'city'
            elif '状态' in c or '通过' in c:
                new_columns[col] = 'status'
            elif '行业' in c:
                new_columns[col] = 'type'
            elif '品类' in c or '名称' in c:
                new_columns[col] = 'name'

        print(f"🔍 智能匹配到的列: {new_columns}")
        df = df.rename(columns=new_columns)

        # === 数据清洗 ===
        # 只保留数字和小数点
        def clean_num(x):
            if isinstance(x, str): return re.sub(r'[^\d\.]', '', x)
            return x

        # 需要转数字的列
        num_cols = ['amount', 'score', 'monthly_flow', 'cost', 'traffic', 'area', 'employees', 'years']
        for col in num_cols:
            if col in df.columns:
                df[col] = df[col].apply(clean_num)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                # 如果即使模糊匹配也没找到，才填0
                print(f"⚠️ 警告: CSV里完全没找到关于 '{col}' 的列，将填充为 0")
                df[col] = 0

        # 补日期
        if 'date' not in df.columns: df['date'] = '2025-01-01'

        # 入库
        print("💾 正在写入数据库...")
        df.to_sql('loan_data', engine, if_exists='replace', index=False)

        # 验证结果
        print("-" * 30)
        print("📊 最终抽查 (金额、营收、面积 不应该为0):")
        print(df[['amount', 'monthly_flow', 'area']].head(1))
        print("-" * 30)
        print("🎉 修复完成！请刷新网页！")

    except Exception as e:
        print(f"❌ 出错: {e}")


if __name__ == '__main__':
    import_data()