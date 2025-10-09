import sqlite3
import json
from datetime import datetime


def delete_analysis_result(record_id):
    """删除指定的分析记录"""
    conn = sqlite3.connect('crop_health.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM analysis_history WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    # 创建历史记录表
    c.execute('''CREATE TABLE IF NOT EXISTS analysis_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp DATETIME,
                  image_path TEXT,  
                  crop_type TEXT,
                  health_status TEXT,
                  confidence REAL,
                  description TEXT,
                  suggestions TEXT)''')
    
    # 创建用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  farm_location TEXT,
                  created_at DATETIME)''')
    
    # 创建种植计划表
    c.execute('''CREATE TABLE IF NOT EXISTS planting_schedules
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                crop_type TEXT,
                activity TEXT,
                time_reference TEXT,
                importance TEXT,
                custom_date TEXT, 
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    # 创建天气预警设置表
    c.execute('''CREATE TABLE IF NOT EXISTS weather_settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER DEFAULT 1,
                  location TEXT,
                  latitude REAL,
                  longitude REAL,
                  alert_types TEXT,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # 创建天气预警历史表
    c.execute('''CREATE TABLE IF NOT EXISTS weather_alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  location TEXT,
                  alert_type TEXT,
                  severity TEXT,
                  description TEXT,
                  effective_time DATETIME,
                  expiration_time DATETIME,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    # 创建用户资源表（存储水滴和肥料）
    c.execute('''CREATE TABLE IF NOT EXISTS user_resources
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER DEFAULT 1,
                  water INTEGER DEFAULT 0,
                  fertilizer INTEGER DEFAULT 0,
                  last_checkin DATE,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # 创建电子作物表
    c.execute('''CREATE TABLE IF NOT EXISTS electronic_crops
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER DEFAULT 1,
                  crop_type TEXT,
                  growth_stage INTEGER DEFAULT 0,
                  water_count INTEGER DEFAULT 0,
                  fertilizer_count INTEGER DEFAULT 0,
                  planted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # 创建打卡历史表
    c.execute('''CREATE TABLE IF NOT EXISTS checkin_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER DEFAULT 1,
                  checkin_date DATE UNIQUE,
                  reward_type TEXT,
                  reward_amount INTEGER,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # 创建知识库文档表
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT,
                  content TEXT,
                  file_type TEXT,
                  file_size INTEGER,
                  upload_time DATETIME,
                  file_hash TEXT UNIQUE,
                  processed BOOLEAN DEFAULT FALSE)''')
    
    # 创建文档片段表
    c.execute('''CREATE TABLE IF NOT EXISTS document_chunks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  document_id INTEGER,
                  chunk_index INTEGER,
                  content TEXT,
                  keywords TEXT,
                  FOREIGN KEY (document_id) REFERENCES knowledge_documents (id))''')
    
    # 创建向量索引元数据表
    c.execute('''CREATE TABLE IF NOT EXISTS vector_index_metadata
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  model_name TEXT,
                  index_type TEXT,
                  dimension INTEGER,
                  total_vectors INTEGER,
                  created_time DATETIME,
                  updated_time DATETIME)''')

    conn.commit()
    conn.close()


def save_planting_schedule(crop_type, activity, time_reference, importance, custom_date=None):
    """保存种植计划到数据库"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    # 处理 custom_date 参数（日期对象转字符串）
    if custom_date and hasattr(custom_date, 'strftime'):
        custom_date_str = custom_date.strftime("%Y-%m-%d")
    else:
        custom_date_str = custom_date
    
    # 插入语句移除邮箱相关字段
    c.execute('''INSERT INTO planting_schedules 
                 (crop_type, activity, time_reference, importance, custom_date)
                 VALUES (?, ?, ?, ?, ?)''',
              (crop_type, activity, time_reference, importance, custom_date_str))
    
    
    conn.commit()
    conn.close()


def get_planting_schedules(limit=50):
    """获取种植计划"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    # 查询所有字段（对应新表结构）
    c.execute('''SELECT * FROM planting_schedules ORDER BY created_at DESC LIMIT ?''', (limit,))
    results = []
    for row in c.fetchall():
        # 新表结构索引：0-id,1-作物类型,2-活动,3-推荐时间,4-重要性,5-自定义日期,6-创建时间
        results.append({
            'id': row[0],
            'crop_type': row[1],
            'activity': row[2],
            'time_reference': row[3],
            'importance': row[4],
            'custom_date': row[5],
            'created_at': row[6]
        })
    
    conn.close()
    return results


def get_due_reminders():
    """获取到期的系统内提醒"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    today = datetime.now().date().strftime("%Y-%m-%d")
    # 只筛选：自定义日期<=今天 的计划
    c.execute('''SELECT * FROM planting_schedules 
                 WHERE custom_date <= ?''', (today,))
    
    results = []
    for row in c.fetchall():
        results.append({
            'id': row[0],
            'crop_type': row[1],
            'activity': row[2],
            'time_reference': row[3],
            'importance': row[4],
            'custom_date': row[5]
        })
    
    conn.close()
    return results


def delete_planting_schedule(schedule_id):
    """删除种植计划"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    c.execute('''DELETE FROM planting_schedules WHERE id = ?''', (schedule_id,))
    
    conn.commit()
    conn.close()


def update_planting_schedule(schedule_id, custom_date=None):
    """更新种植计划"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    # 处理日期格式
    if hasattr(custom_date, 'strftime'):
        custom_date_str = custom_date.strftime("%Y-%m-%d")
    else:
        custom_date_str = custom_date
    
    # 只更新自定义日期字段
    c.execute('''UPDATE planting_schedules 
                 SET custom_date = ?
                 WHERE id = ?''',
              (custom_date_str, schedule_id))
    
    conn.commit()
    conn.close()


def save_analysis_result(image_path, crop_type, health_status, confidence, description, suggestions):
    """保存分析结果"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    c.execute('''INSERT INTO analysis_history 
                 (timestamp, image_path, crop_type, health_status, confidence, description, suggestions)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (datetime.now(), image_path, crop_type, health_status, confidence, description, suggestions))
    
    conn.commit()
    conn.close()


def get_history(limit=10):
    """获取历史记录"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    c.execute('''SELECT * FROM analysis_history 
                 ORDER BY timestamp DESC LIMIT ?''', (limit,))
    
    results = []
    for row in c.fetchall():
        results.append({
            'id': row[0],
            'timestamp': row[1],
            'image_path': row[2],
            'crop_type': row[3],
            'health_status': row[4],
            'confidence': row[5],
            'description': row[6],
            'suggestions': row[7]
        })
    
    conn.close()
    return results


def get_health_trend(crop_type=None):
    """获取健康状态趋势"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    if crop_type:
        c.execute('''SELECT timestamp, health_status, confidence 
                     FROM analysis_history 
                     WHERE crop_type = ?
                     ORDER BY timestamp''', (crop_type,))
    else:
        c.execute('''SELECT timestamp, health_status, confidence 
                     FROM analysis_history 
                     ORDER BY timestamp''')
    
    results = []
    for row in c.fetchall():
        results.append({
            'timestamp': row[0],
            'health_status': row[1],
            'confidence': row[2]
        })
    
    conn.close()
    return results
def get_user_resources(user_id=1):
    """获取用户资源"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    c.execute('''SELECT water, fertilizer, last_checkin FROM user_resources WHERE user_id = ?''', (user_id,))
    result = c.fetchone()
    
    if result:
        resources = {
            'water': result[0],
            'fertilizer': result[1],
            'last_checkin': result[2]
        }
    else:
        # 如果用户没有资源记录，创建一条
        c.execute('''INSERT INTO user_resources (user_id, water, fertilizer) VALUES (?, 0, 0)''', (user_id,))
        conn.commit()
        resources = {
            'water': 0,
            'fertilizer': 0,
            'last_checkin': None
        }
    
    conn.close()
    return resources

def update_user_resources(user_id, water=None, fertilizer=None, last_checkin=None):
    """更新用户资源"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    update_fields = []
    params = []
    
    if water is not None:
        update_fields.append("water = ?")
        params.append(water)
    
    if fertilizer is not None:
        update_fields.append("fertilizer = ?")
        params.append(fertilizer)
    
    if last_checkin is not None:
        update_fields.append("last_checkin = ?")
        params.append(last_checkin)
    
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    
    if update_fields:
        query = f"UPDATE user_resources SET {', '.join(update_fields)} WHERE user_id = ?"
        params.append(user_id)
        c.execute(query, params)
        conn.commit()
    
    conn.close()

def get_electronic_crop(user_id=1):
    """获取用户的电子作物"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    c.execute('''SELECT id, crop_type, growth_stage, water_count, fertilizer_count, planted_at 
                 FROM electronic_crops WHERE user_id = ?''', (user_id,))
    result = c.fetchone()
    
    if result:
        crop = {
            'id': result[0],
            'crop_type': result[1],
            'growth_stage': result[2],
            'water_count': result[3],
            'fertilizer_count': result[4],
            'planted_at': result[5]
        }
    else:
        crop = None
    
    conn.close()
    return crop

def plant_electronic_crop(crop_type, user_id=1):
    """种植新的电子作物"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    # 删除现有的作物（如果有）
    c.execute('''DELETE FROM electronic_crops WHERE user_id = ?''', (user_id,))
    
    # 插入新作物
    c.execute('''INSERT INTO electronic_crops (user_id, crop_type, growth_stage, water_count, fertilizer_count)
                 VALUES (?, ?, 0, 0, 0)''', (user_id, crop_type))
    
    conn.commit()
    conn.close()

def update_electronic_crop(user_id, growth_stage=None, water_count=None, fertilizer_count=None):
    """更新电子作物状态"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    update_fields = []
    params = []
    
    if growth_stage is not None:
        update_fields.append("growth_stage = ?")
        params.append(growth_stage)
    
    if water_count is not None:
        update_fields.append("water_count = ?")
        params.append(water_count)
    
    if fertilizer_count is not None:
        update_fields.append("fertilizer_count = ?")
        params.append(fertilizer_count)
    
    update_fields.append("last_updated = CURRENT_TIMESTAMP")
    
    if update_fields:
        query = f"UPDATE electronic_crops SET {', '.join(update_fields)} WHERE user_id = ?"
        params.append(user_id)
        c.execute(query, params)
        conn.commit()
    
    conn.close()

def add_checkin_record(user_id, checkin_date, reward_type, reward_amount):
    """添加打卡记录"""
    conn = sqlite3.connect('crop_health.db')
    c = conn.cursor()
    
    try:
        c.execute('''INSERT INTO checkin_history (user_id, checkin_date, reward_type, reward_amount)
                     VALUES (?, ?, ?, ?)''', (user_id, checkin_date, reward_type, reward_amount))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        # 已经打卡过
        success = False
    
    conn.close()
    return success
