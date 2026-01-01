from sqlalchemy import create_engine, text

# 1. 数据库配置
DB_URI = "mysql+pymysql://root:123456@localhost:3306/retail_loan?charset=utf8mb4"
engine = create_engine(DB_URI)


def fix_database_v2():
    print("🔧 正在全面检查并修复数据库结构...")

    # 这里列出了代码里用到的所有字段，如果数据库缺了哪个，就自动补上
    # 格式: (字段名, 字段类型)
    columns_to_check = [
        ("traffic", "INT DEFAULT 0"),  # 客流量
        ("monthly_flow", "DECIMAL(10,2) DEFAULT 0"),  # 月均营收
        ("cost", "DECIMAL(10,2) DEFAULT 0"),  # 成本
        ("employees", "INT DEFAULT 5"),  # 员工数
        ("area", "DECIMAL(10,2) DEFAULT 50"),  # 面积
        ("city", "VARCHAR(50) DEFAULT '未知'"),  # 城市
        ("city_level", "VARCHAR(20) DEFAULT '一线'"),  # 城市等级
        ("date", "VARCHAR(20) DEFAULT '2025-01-01'")  # 日期
    ]

    with engine.connect() as conn:
        for col_name, col_type in columns_to_check:
            try:
                # 尝试添加列
                sql = f"ALTER TABLE loan_data ADD COLUMN {col_name} {col_type};"
                conn.execute(text(sql))
                print(f"✅ 成功补全列: {col_name}")
            except Exception as e:
                # 如果报错包含 "Duplicate column"，说明列已经有了，不用管
                if "Duplicate column" in str(e) or "1060" in str(e):
                    print(f"🆗 列已存在，无需添加: {col_name}")
                else:
                    print(f"❌ 添加 {col_name} 失败: {e}")

        conn.commit()

    print("\n🎉 修复完成！现在可以去新增数据了。")


if __name__ == '__main__':
    fix_database_v2()