import json
import os
import datetime

# 日志存储在单独的文件，互不干扰
LOG_FILE = 'system_audit.json'


# --- 功能1：写入一条操作日志 ---
def write_log(user, action, target, ip="127.0.0.1"):
    """
    user: 操作人 (如 admin)
    action: 动作 (如 删除订单、登录系统)
    target: 操作对象 (如 订单ID: 998811)
    ip: IP地址
    """
    # 1. 读取旧日志
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []

    # 2. 构造新日志
    new_log = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
        "target": target,
        "ip": ip,
        "status": "成功"
    }

    # 3. 插入到最前面 (最新的在上面)
    logs.insert(0, new_log)

    # 4. 保存
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)


# --- 功能2：读取所有日志 ---
def read_logs():
    if not os.path.exists(LOG_FILE):
        # 如果没有日志文件，自动生成几条假数据演示用
        dummy_data = [
            {"time": "2026-01-02 10:00:00", "user": "admin", "action": "系统初始化", "target": "-", "ip": "127.0.0.1",
             "status": "成功"},
            {"time": "2026-01-02 09:30:00", "user": "test_user", "action": "尝试登录", "target": "-",
             "ip": "192.168.1.5", "status": "失败"}
        ]
        return dummy_data

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)