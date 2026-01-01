import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# 1. 设置文件路径
DATA_PATH = '../data/raw/loan_data.csv'  # 注意：这里是相对路径
MODEL_PATH = '../data/model.pkl'  # 模型保存路径


def train():
    print("正在读取数据...")
    # 读取数据 (处理各种编码)
    try:
        df = pd.read_csv(DATA_PATH, encoding='utf-8')
    except:
        df = pd.read_csv(DATA_PATH, encoding='gbk')

    # 2. 数据清洗 (和 app.py 里的逻辑保持一致，确保列名对齐)
    # 我们只选取 6 个核心数值特征进行训练，这样最稳健
    df = df.rename(columns={
        '注册金额 (万元)': 'amount', '注册金额（万元）': 'amount',
        '企业信用评分': 'score',
        '经营年份': 'years',
        '月均营收 (万元)': 'monthly_flow', '月均营收（万元）': 'monthly_flow',
        '月均成本 (万元)': 'cost', '月均成本（万元）': 'cost',
        '月均客流量 (人)': 'traffic', '月均客流量（人）': 'traffic',
        '是否通过贷款': 'status', '审批状态': 'status'
    })

    # 提取特征列 (X) 和 目标列 (y)
    feature_cols = ['amount', 'score', 'years', 'monthly_flow', 'cost', 'traffic']

    # 确保这些列都是数字，如果不是，填0
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0  # 如果缺列，补0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    X = df[feature_cols]

    # 处理目标列：把 "通过" 变成 1，其他变成 0
    df['status'] = df['status'].astype(str)
    y = df['status'].apply(lambda x: 1 if '通过' in x else 0)

    print(f"数据准备完毕，共 {len(df)} 条数据。正在训练 AI 模型...")

    # 3. 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. 使用随机森林算法 (Random Forest)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 5. 评估模型
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"模型训练完成！准确率: {acc * 100:.2f}%")

    # 6. 保存模型文件
    joblib.dump(model, MODEL_PATH)
    print(f"模型已保存至: {MODEL_PATH}")


if __name__ == '__main__':
    train()