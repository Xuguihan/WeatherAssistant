import sqlite3
import os
from datetime import datetime

DB_NAME = "weatherInfo.db"

# 功能函数
def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # 设置像字典一样访问数据
    return conn

def init_db():
    """初始化数据库表（如果不存在则创建）"""
    conn = get_db_connection()
    cursor = conn.cursor() #游标，数据库操作者

    # 创建城市表(cities)：存储 城市名 和 对应的 Location ID
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_name TEXT UNIQUE NOT NULL,
            location_id TEXT NOT NULL
        )
    ''')

    # 创建天气表(weather_data)：存储 城市ID、日期、天气数据、更新时间
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_id TEXT UNIQUE NOT NULL,
            date TEXT NOT NULL,
            weather_json TEXT,
            updated_at TEXT,
            FOREIGN KEY (city_id) REFERENCES cities (location_id)
        )
    ''')
    conn.commit()
    conn.close()

# --- 城市相关的数据库操作 ---

def get_city_from_db(city_name)->str:
    """根据城市名查找数据库,返回location_id"""
    conn = get_db_connection()
    row = conn.execute('SELECT location_id FROM cities WHERE city_name = ?', (city_name,)).fetchone()
    conn.close()
    if row:
        return row["location_id"]
    return None

def add_city_to_db(city_name, location_id):
    """将新的城市名及其ID存入数据库"""
    conn = get_db_connection()
    try:
        conn.execute('''
        INSERT INTO cities (city_name, location_id) VALUES (?, ?)
        ''', (city_name, location_id))
        conn.commit()
    except sqlite3.IntegrityError:
        # 如果城市已存在（并发情况），忽略错误
        pass
    finally:
        conn.close()

# --- 天气相关的数据库操作 ---

def get_weather_from_db(city_id, target_date):
    """
    根据城市ID和目标日期查找天气
    返回天气JSON字符串
    """
    conn = get_db_connection()
    # 查找当天的数据
    row = conn.execute('''
        SELECT weather_json FROM weather_data 
        WHERE city_id = ? AND date = ?
    ''', (city_id, target_date)).fetchone()
    conn.close()
    
    if row:
        return row['weather_json']
    return None

def update_weather_in_db(city_id,date_str,weather_json):
    """更新或插入天气数据"""
    conn = get_db_connection()
    now = datetime.now().isoformat()
    conn.execute('''
        INSERT INTO weather_data (city_id, date, weather_json, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (city_id) DO UPDATE SET
            date=excluded.date,
            weather_json=excluded.weather_json,
            updated_at=excluded.updated_at
    ''', (city_id, date_str, weather_json, now))
    conn.commit()
    conn.close()