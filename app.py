# -*- coding: UTF-8 -*-
# api/index.py - GitHub Contributions API for hexo-filter-gitcalendar

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # 允许所有跨域请求

def list_split(items, n):
    """将列表按每 n 个元素分割成子列表"""
    return [items[i:i + n] for i in range(0, len(items), n)]

def getdata(name):
    try:
        # 从第三方 API 获取数据（扁平数组）
        url = f"https://github-contributions-api.jogruber.de/v4/{name}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        days = data.get("contributions", [])  # 扁平数组，每个元素包含 date 和 count

        # 手动计算总贡献数（确保是整数）
        total = sum(day.get("count", 0) for day in days)

        # 按7天分割成周
        weekly = list_split(days, 7)

        # 补足到至少53周（前面补空周，日期递减）
        while len(weekly) < 53:
            # 获取当前第一周的日期
            first_week_start = datetime.strptime(weekly[0][0]["date"], "%Y-%m-%d")
            # 计算前一周的日期范围
            prev_week_start = first_week_start - timedelta(weeks=1)
            new_week = []
            for i in range(7):
                date = prev_week_start + timedelta(days=i)
                new_week.append({"date": date.strftime("%Y-%m-%d"), "count": 0})
            weekly.insert(0, new_week)

        # 确保最后一周有7天（后面补空，日期递增）
        last_week = weekly[-1]
        if len(last_week) < 7:
            last_date = datetime.strptime(last_week[-1]["date"], "%Y-%m-%d")
            for i in range(1, 7 - len(last_week) + 1):
                new_date = last_date + timedelta(days=i)
                last_week.append({"date": new_date.strftime("%Y-%m-%d"), "count": 0})

        # 只取前53周（防止超出）
        return {
            "total": total,
            "contributions": weekly[:53]
        }
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return jsonify({
        "message": "GitHub Calendar API",
        "usage": [
            "/?username  - 例如 /?Sunrisepeak",
            "/api?username=<name>  - 同上",
            "/<username>  - 路径参数"
        ]
    })

@app.route('/api', strict_slashes=False)
@app.route('/', strict_slashes=False)
def get_calendar():
    username = request.args.get('username')
    if not username:
        qs = request.query_string.decode('utf-8')
        if qs and '=' not in qs:
            username = qs
    if not username:
        return jsonify({"error": "Missing username"}), 400
    return jsonify(getdata(username))

@app.route('/<username>', strict_slashes=False)
def get_calendar_by_path(username):
    return jsonify(getdata(username))

app = app