import sqlite3
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import date, datetime, timedelta
import os
from PIL import Image
import tempfile
import requests
import json
from database import (add_checkin_record, delete_analysis_result, delete_planting_schedule, 
                     get_due_reminders, get_electronic_crop, get_planting_schedules, get_user_resources, init_db, plant_electronic_crop, 
                     save_analysis_result, get_history, get_health_trend, 
                     save_planting_schedule, update_electronic_crop, update_planting_schedule, update_user_resources)
from silican_api import SilicanAPI
from rag_qa_system_simple import SimpleRAGQASystem as RAGQASystem
from io import BytesIO
import time
import base64

# 初始化数据库
init_db()

# 应用配置
st.set_page_config(
    page_title="农作物健康管理系统",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 全局样式 */
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9f5e9 100%);
    }
    
    .main-header {
        font-size: 3rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 700;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.1);
        padding: 1rem;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .sub-header {
        font-size: 1.8rem;
        color: #3CB371;
        border-bottom: 2px solid #3CB371;
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .card {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.08);
        margin-bottom: 1.5rem;
        border-left: 5px solid #4CAF50;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8fff8 0%, #e8f5e8 100%);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.06);
        border: 1px solid #d4edda;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #4CAF50 0%, #3e8e41 100%);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 10px rgba(0, 0, 0, 0.15);
        background: linear-gradient(135deg, #3e8e41 0%, #2d6a2f 100%);
    }
    
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin-bottom: 1rem;
        box-shadow: 0 3px 6px rgba(0,0,0,0.05);
    }
    
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin-bottom: 1rem;
        box-shadow: 0 3px 6px rgba(0,0,0,0.05);
    }
    
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #17a2b8;
        margin-bottom: 1rem;
        box-shadow: 0 3px 6px rgba(0,0,0,0.05);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f0fff0 0%, #e0f2e0 100%);
        box-shadow: 2px 0 10px rgba(0,0,0,0.1);
    }
    
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #3CB371, transparent);
        margin: 1.5rem 0;
        opacity: 0.7;
    }
    
    
    .feature-icon {
        font-size: 1.5rem;
        margin-right: 0.5rem;
        vertical-align: middle;
        color: #2E8B57;
    }
    
    .crop-card {
        transition: all 0.3s ease;
        border-radius: 12px;
        overflow: hidden;
    }
    
    .crop-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.12);
    }
    
    /* 表单元素样式 */
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #ced4da;
    }
    
    .stSelectbox>div>div>select {
        border-radius: 8px;
    }
    
    .stDateInput>div>div>input {
        border-radius: 8px;
    }
    
    /* 标签样式 */
    .stRadio > div {
        flex-direction: column;
        align-items: stretch;
    }
    
    .stRadio > div > label {
        background: rgba(255, 255, 255, 0.9);
        padding: 0.75rem 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
        border: 1px solid #e9ecef;
        transition: all 0.2s;
    }
    
    .stRadio > div > label:hover {
        background: rgba(76, 175, 80, 0.1);
        border-color: #4CAF50;
    }
    
    .stRadio > div > label[data-testid="stRadioLabel"] > div:first-child {
        font-weight: 500;
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div {
        background-color: #4CAF50;
    }
    
    /* 文件上传样式 */
    .stFileUploader > div {
        border-radius: 10px;
        border: 2px dashed #4CAF50;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.7);
    }
    
    /* 表格样式 */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    }
    
    /* 标签页样式 */
    .stTabs > div > div > button {
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1rem;
    }
    
    /* 扩展器样式 */
    .streamlit-expanderHeader {
        font-weight: 600;
        background: rgba(255, 255, 255, 0.8);
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    
    /* 视频播放器样式 */
    .stVideo {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    
    /* 摄像头组件样式 */
    .stCameraInput {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
        border: 3px solid #4CAF50;
    }
    
    
    /* 摄像头提示信息样式 */
    .camera-info {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        border: 2px solid #2196F3;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 4px 8px rgba(33, 150, 243, 0.2);
    }
    
    .camera-info h4 {
        color: #1976D2;
        margin: 0 0 0.5rem 0;
        font-weight: 600;
    }
    
    .camera-info p {
        color: #424242;
        margin: 0;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

if 'history' not in st.session_state:
    st.session_state.history = get_history()

# 初始化种植计划相关会话状态
if 'extracted_events' not in st.session_state:
    st.session_state.extracted_events = []
if 'planting_advice' not in st.session_state:
    st.session_state.planting_advice = ""
if 'selected_crop_for_advice' not in st.session_state:
    st.session_state.selected_crop_for_advice = None

# 初始化天气相关会话状态
if 'weather_location' not in st.session_state:
    st.session_state.weather_location = "北京"
if 'selected_crops' not in st.session_state:
    st.session_state.selected_crops = ["全部作物"]
if 'alert_types' not in st.session_state:
    st.session_state.alert_types = ["暴雨", "大风", "寒潮"]
if 'current_weather' not in st.session_state:
    st.session_state.current_weather = None
if 'weather_alerts' not in st.session_state:
    st.session_state.weather_alerts = []
if 'weather_forecast' not in st.session_state:
    st.session_state.weather_forecast = None

# 侧边栏
with st.sidebar:
    st.markdown('<h1 style="color: #2E8B57; text-align: center; padding: 1rem; background: rgba(255, 255, 255, 0.8); border-radius: 15px; margin-bottom: 1.5rem;">🌱 农作物健康管理系统</h1>', unsafe_allow_html=True)
    
    # API密钥输入
    st.markdown("### 🔑 API设置")
    api_key = st.text_input("硅基流动API密钥", type="password", value=st.session_state.api_key, 
                           help="请输入您的硅基流动API密钥以启用所有功能")
    if api_key:
        st.session_state.api_key = api_key
        st.markdown('<div class="success-box">API密钥已设置</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="warning-box">请输入API密钥以使用分析功能</div>', unsafe_allow_html=True)
    
    # 导航
    st.markdown("### 📍 导航")
    nav_options = {
        "图片分析": "📷",
        "视频分析": "🎥", 
        "农业问答助手": "❓",
        "历史记录": "📊",
        "健康趋势": "📈",
        "种植计划": "📅",
        "天气预警": "🌦️",
        "电子农场": "🌾"
    }
    
    page = st.radio(
        "选择功能",
        options=list(nav_options.keys()),
        format_func=lambda x: f"{nav_options[x]} {x}",
        label_visibility="collapsed"
    )
    
    
    # 使用说明
    st.markdown("---")
    with st.expander("📖 使用说明", expanded=False):
        st.markdown("""
        1. 在侧边栏输入硅基流动API密钥
        2. 上传农作物图片或视频
        3. 查看分析结果和建议
        4. 在历史记录中查看过往分析
        5. 在健康趋势中查看作物状态变化
        6. 在种植计划中管理农事日程与系统提醒
        7. 在天气预警中获取实时天气信息
        8. 在电子农场中模拟作物生长环境
        """)

# 天气API类
class WeatherAPI:
    def __init__(self, api_key=None):
        self.api_key = api_key or "f8d0f287ee4b4e44b9775a6e85150270"  #作者寄语：省着点用
        self.base_url = "https://p36hewymda.re.qweatherapi.com/v7"
        self.geo_url = "https://p36hewymda.re.qweatherapi.com/geo/v2"
    
    def get_city_location_id(self, city_name):
        """通过城市名称获取和风天气的位置ID"""
        try:
            url = f"{self.geo_url}/city/lookup"
            params = {
                "location": city_name,
                "key": self.api_key,
                "number": 1
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == "200" and data.get("location"):
                return data["location"][0]["id"], data["location"][0]["name"]
            else:
                st.error(f"获取城市位置ID失败: {data.get('code') if data else '无响应'}")
                return None, None
        except Exception as e:
            st.error(f"获取城市位置ID失败: {str(e)}")
            return None, None
    
    def get_current_weather(self, city_name):
        """通过城市名称获取当前天气"""
        location_id, location_name = self.get_city_location_id(city_name)
        if location_id is None:
            return None
            
        try:
            url = f"{self.base_url}/weather/now"
            params = {
                "location": location_id,
                "key": self.api_key,
                "lang": "zh",
                "unit": "m"
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and data.get("code") == "200":
                # 转换和风天气格式为通用格式
                weather_data = {
                    'main': {
                        'temp': float(data['now']['temp']),
                        'humidity': float(data['now']['humidity']),
                        'feelsLike': float(data['now']['feelsLike'])
                    },
                    'wind': {
                        'speed': float(data['now']['windSpeed']),
                        'dir': data['now']['windDir'],
                        'scale': data['now']['windScale']
                    },
                    'weather': [{
                        'description': data['now']['text']
                    }],
                    'location_name': location_name,
                    'update_time': data.get('updateTime')
                }
                return weather_data
            else:
                st.error(f"获取当前天气失败: {data.get('code') if data else '无响应'}")
                return None
        except Exception as e:
            st.error(f"获取天气数据失败: {str(e)}")
            return None
    
    def get_weather_forecast(self, city_name):
        """通过城市名称获取天气预报"""
        location_id, location_name = self.get_city_location_id(city_name)
        if location_id is None:
            return None
            
        try:
            url = f"{self.base_url}/weather/3d"
            params = {
                "location": location_id,
                "key": self.api_key,
                "lang": "zh",
                "unit": "m"
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and data.get("code") == "200":
                return {
                    'daily': data['daily'],
                    'location_name': location_name
                }
            else:
                st.error(f"获取天气预报失败: {data.get('code') if data else '无响应'}")
                return None
        except Exception as e:
            st.error(f"获取天气预报失败: {str(e)}")
            return None
    
    def get_weather_alerts(self, city_name):
        """通过城市名称获取天气预警信息"""
        location_id, location_name = self.get_city_location_id(city_name)
        if location_id is None:
            return []
            
        try:
            url = f"{self.base_url}/warning/now"
            params = {
                "location": location_id,
                "key": self.api_key,
                "lang": "zh"
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data and data.get("code") == "200" and data.get("warning"):
                alerts = []
                for warning in data['warning']:
                    # 转换和风天气预警格式为通用格式
                    alert = {
                        'event': warning['typeName'],
                        'description': warning['text'],
                        'start': warning['startTime'],
                        'end': warning['endTime'],
                        'sender_name': warning['sender']
                    }
                    alerts.append(alert)
                return alerts
            else:
                return []
        except Exception as e:
            st.error(f"获取天气预警失败: {str(e)}")
            return []

# 系统内提醒检查函数
def check_reminders():
    """检查到期提醒并在侧边栏显示"""
    due_reminders = get_due_reminders()
    if due_reminders:
        reminder_count = len(due_reminders)
        st.sidebar.markdown(f'<div class="warning-box">⚠️ 有 {reminder_count} 个农事活动已到期</div>', unsafe_allow_html=True)
        # 展开显示详情
        with st.sidebar.expander("查看到期活动"):
            for idx, reminder in enumerate(due_reminders, 1):
                st.write(f"{idx}. **{reminder['crop_type']}** - {reminder['activity']}")
                st.write(f"   计划日期：{reminder['custom_date'] or '未设置'}")
                st.markdown("---")
    else:
        st.sidebar.markdown('<div class="success-box">✅ 暂无到期的农事提醒</div>', unsafe_allow_html=True)

# 检查天气预警
def check_weather_alerts():
    """检查天气预警"""
    if hasattr(st.session_state, 'weather_location'):
        weather_api = WeatherAPI()
        alerts = weather_api.get_weather_alerts(st.session_state.weather_location)
        
        if alerts:
            # 在侧边栏显示预警通知
            alert_count = len(alerts)
            st.sidebar.markdown(f'<div class="warning-box">⚠️ 有 {alert_count} 个天气预警</div>', unsafe_allow_html=True)
            
            # 展开显示详情
            with st.sidebar.expander("查看天气预警"):
                for idx, alert in enumerate(alerts, 1):
                    alert_type = alert.get('event', '未知预警')
                    # 只显示用户关注的预警类型
                    if alert_type not in st.session_state.alert_types:
                        continue
                    st.write(f"{idx}. **{alert_type}**预警")
                    st.write(f"   描述: {alert.get('description', '无详细描述')[:50]}...")
                    st.markdown("---")

# 在侧边栏适当位置调用
check_reminders()
check_weather_alerts()

# 主内容区域
if page == "图片分析":
    st.markdown('<div class="main-header">📷 农作物健康度分析（图片）</div>', unsafe_allow_html=True)
    
    # 图片输入方式选择
    input_method = st.radio(
        "选择图片输入方式",
        ["📁 上传图片文件", "📷 使用摄像头拍照", "📹 连接外部摄像头"],
        horizontal=True
    )
    
    uploaded_file = None
    
    if input_method == "📁 上传图片文件":
        uploaded_file = st.file_uploader("上传农作物图片", type=['jpg', 'jpeg', 'png'], 
                                        help="支持JPG、JPEG、PNG格式的图片")
    
    elif input_method == "📷 使用摄像头拍照":
        st.markdown("""
        <div class="camera-info">
            <h4>📷 摄像头拍照功能</h4>
            <p>请确保您的设备有摄像头，并允许浏览器访问摄像头权限</p>
        </div>
        """, unsafe_allow_html=True)
        
        
        # 拍照提示
        with st.expander("📋 拍照提示", expanded=False):
            st.markdown("""
            **拍照建议：**
            - 确保光线充足，避免阴影
            - 将农作物放在画面中央
            - 保持稳定，避免模糊
            - 尽量拍摄清晰的叶片和茎干
            - 避免背景过于复杂
            """)
        
        # 摄像头拍照组件
        try:
            picture = st.camera_input("拍摄农作物图片", key="camera_picture")
            
            if picture is not None:
                # 将摄像头拍摄的图片转换为PIL Image
                image = Image.open(picture)
                
                # 显示拍摄的图片
                st.image(image, caption="拍摄的农作物图片", use_column_width=True)
                
                # 将PIL Image转换为BytesIO对象，模拟文件上传
                img_buffer = BytesIO()
                image.save(img_buffer, format='JPEG')
                img_buffer.seek(0)
                
                # 创建一个类似文件上传的对象
                class CameraImage:
                    def __init__(self, image_buffer, filename="camera_capture.jpg"):
                        self.image_buffer = image_buffer
                        self.name = filename
                        self.type = "image/jpeg"
                    
                    def getvalue(self):
                        return self.image_buffer.getvalue()
                    
                    def read(self):
                        """添加read方法以兼容PIL.Image.open()"""
                        return self.image_buffer.getvalue()
                
                uploaded_file = CameraImage(img_buffer)
                
                # 显示拍照成功提示
                st.success("✅ 图片拍摄成功！您可以点击下方「分析图片」按钮进行分析")
                
        except Exception as e:
            st.error(f"摄像头访问失败：{str(e)}")
            st.markdown("""
            **可能的解决方案：**
            1. 检查浏览器是否允许访问摄像头
            2. 确保没有其他应用正在使用摄像头
            3. 尝试刷新页面重新授权
            4. 检查摄像头驱动是否正常
            """)
    
    elif input_method == "📹 连接外部摄像头":
        st.markdown("""
        <div class="camera-info">
            <h4>📹 外部摄像头连接</h4>
            <p>连接网络摄像头或USB摄像头进行实时监控和拍照</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 外部摄像头配置
        with st.expander("🔧 摄像头配置", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                cam_type = st.selectbox("摄像头类型", ["USB摄像头", "网络摄像头(IP)", "RTSP流"], 
                                      help="选择您要连接的外部摄像头类型")
                
                if cam_type == "USB摄像头":
                    cam_device = st.number_input("设备编号", min_value=0, max_value=10, value=0,
                                               help="USB摄像头的设备编号，通常为0")
                    cam_resolution = st.selectbox("分辨率", ["640x480", "1280x720", "1920x1080"], index=1)
                    
                elif cam_type == "网络摄像头(IP)":
                    cam_ip = st.text_input("摄像头IP地址", value="192.168.1.100", 
                                          help="请输入网络摄像头的IP地址")
                    cam_port = st.number_input("端口号", min_value=1, max_value=65535, value=8080,
                                             help="HTTP端口，通常为8080或80")
                    cam_path = st.text_input("视频路径", value="/video", 
                                           help="视频流的路径，如/video或/videostream.cgi")
                    
                elif cam_type == "RTSP流":
                    rtsp_url = st.text_input("RTSP地址", value="rtsp://192.168.1.100:554/stream",
                                           help="完整的RTSP流地址")
            
            with col2:
                cam_fps = st.slider("帧率", min_value=1, max_value=30, value=15,
                                  help="摄像头帧率设置")
                cam_quality = st.selectbox("图像质量", ["低", "中", "高"], index=1,
                                         help="图像压缩质量")
                
                # 连接状态显示
                if 'camera_connected' not in st.session_state:
                    st.session_state.camera_connected = False
                
                if st.session_state.camera_connected:
                    st.success("✅ 摄像头已连接")
                else:
                    st.warning("⚠️ 摄像头未连接")
        
        # 连接按钮
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔗 连接摄像头", key="connect_external_cam"):
                with st.spinner("正在连接摄像头..."):
                    try:
                        # 模拟摄像头连接过程
                        import time
                        time.sleep(1)
                        st.session_state.camera_connected = True
                        st.success("摄像头连接成功！")
                    except Exception as e:
                        st.error(f"连接失败：{str(e)}")
        
        with col2:
            if st.button("❌ 断开连接", key="disconnect_external_cam"):
                st.session_state.camera_connected = False
                st.info("摄像头已断开")
        
        # 实时监控和拍照
        if st.session_state.camera_connected:
            st.markdown("### 📸 实时监控")
            
            # 模拟摄像头画面
            placeholder = st.empty()
            
            # 拍照控制
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📷 拍照", key="capture_external"):
                    # 模拟拍照过程
                    with st.spinner("正在拍照..."):
                        import time
                        time.sleep(0.5)
                        
                        # 创建模拟图片
                        import numpy as np
                        from PIL import Image
                        
                        # 生成一个模拟的农作物图片
                        img_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                        # 添加一些绿色区域模拟农作物
                        img_array[100:300, 200:400] = [34, 139, 34]  # 绿色
                        img_array[150:250, 250:350] = [0, 100, 0]    # 深绿色
                        
                        captured_image = Image.fromarray(img_array)
                        
                        # 显示拍摄的图片
                        st.image(captured_image, caption="外部摄像头拍摄的图片", use_column_width=True)
                        
                        # 转换为文件上传格式
                        img_buffer = BytesIO()
                        captured_image.save(img_buffer, format='JPEG')
                        img_buffer.seek(0)
                        
                        class ExternalCameraImage:
                            def __init__(self, image_buffer, filename="external_camera_capture.jpg"):
                                self.image_buffer = image_buffer
                                self.name = filename
                                self.type = "image/jpeg"
                            
                            def getvalue(self):
                                return self.image_buffer.getvalue()
                            
                            def read(self):
                                """添加read方法以兼容PIL.Image.open()"""
                                return self.image_buffer.getvalue()
                        
                        uploaded_file = ExternalCameraImage(img_buffer)
                        st.success("✅ 外部摄像头拍照成功！")
            
            with col2:
                if st.button("🔄 刷新画面", key="refresh_external"):
                    st.rerun()
            
            with col3:
                if st.button("⚙️ 调整设置", key="adjust_external"):
                    st.info("摄像头设置已调整")
            
            # 显示连接信息
            st.info(f"📹 已连接到: {cam_type} | 分辨率: {cam_resolution if cam_type == 'USB摄像头' else '自动'} | 帧率: {cam_fps}fps")
        else:
            st.info("请先连接外部摄像头")
    
    if uploaded_file is not None:
        # 显示上传的图片
        col1, col2 = st.columns([1, 2])
        with col1:
            image = Image.open(uploaded_file)
            st.image(image, caption="上传的农作物图片", use_column_width=True)
        
        # 临时保存图片
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            image.save(tmp_file.name)
            image_path = tmp_file.name
        
        # 分析按钮
        if st.button("分析图片", type="primary") and st.session_state.api_key:
            with st.spinner("分析中..."):
                try:
                    # 初始化API
                    api = SilicanAPI(st.session_state.api_key)
                    
                    # 分析图片
                    result = api.detect_crop_health(image_path)
                    
                    # 检查是否有API错误
                    if "API调用超时" in str(result) or "网络连接失败" in str(result) or "调用失败" in str(result):
                        st.error("⚠️ API调用出现问题，请检查网络连接后重试")
                        st.info("如果问题持续存在，请尝试：\n1. 检查网络连接\n2. 稍后重试\n3. 联系技术支持")
                        st.stop()
                    
                    # 显示结果
                    st.markdown('<div class="sub-header">分析结果</div>', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("作物类型", result["crop_type"])
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        if result["health_status"] == "健康":
                            st.metric("健康状态", "健康", delta="良好", delta_color="normal")
                        else:
                            st.metric("健康状态", "不健康", delta="需关注", delta_color="inverse")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                        st.metric("置信度", f"{result['confidence']*100:.1f}%")
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.subheader("详细描述")
                    st.info(result["description"])
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.subheader("建议措施")
                    st.success(result["suggestions"])
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # 保存到数据库
                    save_analysis_result(
                        image_path=uploaded_file.name,
                        crop_type=result["crop_type"],
                        health_status=result["health_status"],
                        confidence=result["confidence"],
                        description=result["description"],
                        suggestions=result["suggestions"]
                    )
                    
                    # 更新历史记录
                    st.session_state.history = get_history()
                    
                except Exception as e:
                    st.error(f"图片分析失败: {str(e)}")
                    st.info("请检查网络连接或稍后重试")
        
        # 清理临时文件
        os.unlink(image_path)
    
    elif not st.session_state.api_key:
        st.markdown('<div class="warning-box">请先在侧边栏输入API密钥</div>', unsafe_allow_html=True)


elif page == "视频分析":
    st.markdown('<div class="main-header">🎥 农作物健康度分析（视频）</div>', unsafe_allow_html=True)
    
    # 视频输入方式选择
    input_method = st.radio(
        "选择视频输入方式",
        ["📁 上传视频文件", "📹 连接外部摄像头"],
        horizontal=True
    )
    
    uploaded_file = None
    
    if input_method == "📁 上传视频文件":
        uploaded_file = st.file_uploader("上传农作物视频", type=['mp4', 'avi', 'mov', 'mkv'],
                                        help="支持MP4、AVI、MOV、MKV格式的视频")
    
    
    elif input_method == "📹 连接外部摄像头":
        st.markdown("""
        <div class="camera-info">
            <h4>📹 外部摄像头连接</h4>
            <p>连接网络摄像头或USB摄像头进行实时监控和录制</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 外部摄像头配置
        with st.expander("🔧 摄像头配置", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                cam_type = st.selectbox("摄像头类型", ["USB摄像头", "网络摄像头(IP)", "RTSP流"], 
                                      help="选择您要连接的外部摄像头类型", key="video_cam_type")
                
                if cam_type == "USB摄像头":
                    cam_device = st.number_input("设备编号", min_value=0, max_value=10, value=0,
                                               help="USB摄像头的设备编号，通常为0", key="video_cam_device")
                    cam_resolution = st.selectbox("分辨率", ["640x480", "1280x720", "1920x1080"], index=1,
                                                key="video_cam_resolution")
                    
                elif cam_type == "网络摄像头(IP)":
                    cam_ip = st.text_input("摄像头IP地址", value="192.168.1.100", 
                                          help="请输入网络摄像头的IP地址", key="video_cam_ip")
                    cam_port = st.number_input("端口号", min_value=1, max_value=65535, value=8080,
                                             help="HTTP端口，通常为8080或80", key="video_cam_port")
                    cam_path = st.text_input("视频路径", value="/video", 
                                           help="视频流的路径，如/video或/videostream.cgi", key="video_cam_path")
                    
                elif cam_type == "RTSP流":
                    rtsp_url = st.text_input("RTSP地址", value="rtsp://192.168.1.100:554/stream",
                                           help="完整的RTSP流地址", key="video_rtsp_url")
            
            with col2:
                cam_fps = st.slider("帧率", min_value=1, max_value=30, value=15,
                                  help="摄像头帧率设置", key="video_cam_fps")
                cam_quality = st.selectbox("视频质量", ["低", "中", "高"], index=1,
                                         help="视频压缩质量", key="video_cam_quality")
                
                # 录制设置
                record_duration = st.slider("录制时长（秒）", min_value=5, max_value=60, value=10,
                                          help="选择录制视频的时长", key="video_record_duration")
                
                # 连接状态显示
                if 'video_camera_connected' not in st.session_state:
                    st.session_state.video_camera_connected = False
                
                if st.session_state.video_camera_connected:
                    st.success("✅ 摄像头已连接")
                else:
                    st.warning("⚠️ 摄像头未连接")
        
        # 连接按钮
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🔗 连接摄像头", key="connect_video_external_cam"):
                with st.spinner("正在连接摄像头..."):
                    try:
                        # 模拟摄像头连接过程
                        import time
                        time.sleep(1)
                        st.session_state.video_camera_connected = True
                        st.success("摄像头连接成功！")
                    except Exception as e:
                        st.error(f"连接失败：{str(e)}")
        
        with col2:
            if st.button("❌ 断开连接", key="disconnect_video_external_cam"):
                st.session_state.video_camera_connected = False
                st.info("摄像头已断开")
        
        # 实时监控和录制
        if st.session_state.video_camera_connected:
            st.markdown("### 📹 实时监控")
            
            # 模拟摄像头画面
            placeholder = st.empty()
            
            # 录制控制
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("🎬 开始录制", key="start_record_external"):
                    # 模拟录制过程
                    with st.spinner(f"正在录制 {record_duration} 秒..."):
                        import time
                        time.sleep(2)  # 模拟录制时间
                        
                        # 创建模拟视频数据
                        import numpy as np
                        from PIL import Image
                        import io
                        
                        # 生成模拟视频帧
                        frames = []
                        for i in range(record_duration * 2):  # 假设2fps
                            img_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                            # 添加一些绿色区域模拟农作物
                            img_array[100:300, 200:400] = [34, 139, 34]  # 绿色
                            img_array[150:250, 250:350] = [0, 100, 0]    # 深绿色
                            
                            # 添加一些变化模拟视频
                            if i % 10 == 0:
                                img_array[120:280, 220:380] = [50, 150, 50]  # 变化的绿色
                            
                            frames.append(Image.fromarray(img_array))
                        
                        # 创建模拟视频文件
                        video_buffer = io.BytesIO()
                        # 这里简化处理，实际应该使用OpenCV或类似库创建真实视频
                        video_data = b"fake_video_data_for_external_camera"
                        
                        class ExternalCameraVideo:
                            def __init__(self, video_buffer, filename="external_camera_recording.mp4"):
                                self.video_buffer = video_buffer
                                self.name = filename
                                self.type = "video/mp4"
                            
                            def getvalue(self):
                                return video_data
                            
                            def read(self):
                                """添加read方法以兼容视频处理"""
                                return video_data
                        
                        uploaded_file = ExternalCameraVideo(video_buffer)
                        st.success(f"✅ 外部摄像头录制成功！录制时长: {record_duration}秒")
            
            with col2:
                if st.button("⏹️ 停止录制", key="stop_record_external"):
                    st.info("录制已停止")
            
            with col3:
                if st.button("🔄 刷新画面", key="refresh_video_external"):
                    st.rerun()
            
            with col4:
                if st.button("⚙️ 调整设置", key="adjust_video_external"):
                    st.info("摄像头设置已调整")
            
            # 显示连接信息
            st.info(f"📹 已连接到: {cam_type} | 分辨率: {cam_resolution if cam_type == 'USB摄像头' else '自动'} | 帧率: {cam_fps}fps | 录制时长: {record_duration}秒")
        else:
            st.info("请先连接外部摄像头")
    
    if uploaded_file is not None:
        # 显示上传的视频
        st.video(uploaded_file)
        
        # 分析选项
        col1, col2 = st.columns(2)
        with col1:
            sample_rate = st.slider("采样频率(秒)", min_value=1, max_value=10, value=3, 
                                   help="从视频中每隔多少秒提取一帧进行分析")
        with col2:
            max_frames = st.slider("最大分析帧数", min_value=1, max_value=20, value=5,
                                  help="最多分析多少帧视频")
        
        # 分析按钮
        if st.button("分析视频", type="primary") and st.session_state.api_key:
            with st.spinner("视频分析中，这可能需要一些时间..."):
                try:
                    # 初始化API
                    api = SilicanAPI(st.session_state.api_key)
                    
                    # 临时保存视频
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        video_path = tmp_file.name
                    
                    cap = None
                    # 提取视频帧
                    import cv2
                    cap = cv2.VideoCapture(video_path)
                    if not cap.isOpened():
                        st.error("无法打开视频文件")
                        st.stop()
                    
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_interval = int(sample_rate * fps)
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    
                    # 计算预期的最大分析帧数
                    expected_frames = min(max_frames, total_frames // frame_interval)
                    if expected_frames == 0:
                        expected_frames = 1  # 确保至少有一帧
                    
                    # 存储分析结果
                    all_results = []
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    frames_analyzed = 0
                    frame_count = 0
                    
                    while cap.isOpened() and frames_analyzed < max_frames:
                        ret, frame = cap.read()
                        if not ret:
                            break
                            
                        # 按间隔采样
                        if frame_count % frame_interval == 0:
                            # 临时保存帧图像
                            frame_path = f"temp_frame_{frames_analyzed}.jpg"
                            cv2.imwrite(frame_path, frame)
                            
                            # 分析当前帧
                            status_text.text(f"分析第 {frames_analyzed + 1}/{expected_frames} 帧...")
                            result = api.detect_crop_health(frame_path)
                            all_results.append(result)
                            
                            # 更新进度
                            frames_analyzed += 1
                            progress_value = min(frames_analyzed / expected_frames, 1.0)
                            progress_bar.progress(progress_value)
                            
                            # 删除临时帧文件
                            try:
                                os.unlink(frame_path)
                            except PermissionError:
                                pass
                            
                        frame_count += 1
                    
                    # 汇总分析结果
                    if all_results:
                        avg_confidence = sum(r['confidence'] for r in all_results) / len(all_results)
                        crop_types = [r['crop_type'] for r in all_results]
                        main_crop_type = max(set(crop_types), key=crop_types.count)
                        health_statuses = [r['health_status'] for r in all_results]
                        overall_health = "健康" if all(status == "健康" for status in health_statuses) else "不健康"
                        all_suggestions = "\n".join([f"- {r['suggestions']}" for r in all_results[:3]])
                        
                        # 显示汇总结果
                        st.markdown('<div class="sub-header">视频分析汇总结果</div>', unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.metric("主要作物类型", main_crop_type)
                            st.markdown('</div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.metric("整体健康状态", overall_health)
                            st.markdown('</div>', unsafe_allow_html=True)
                        with col3:
                            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                            st.metric("平均置信度", f"{avg_confidence*100:.1f}%")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # 显示详细结果
                        st.markdown('<div class="sub-header">各帧分析详情</div>', unsafe_allow_html=True)
                        for i, result in enumerate(all_results):
                            with st.expander(f"第{i+1}帧 - {result['crop_type']} - {result['health_status']}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**作物类型:** {result['crop_type']}")
                                    st.write(f"**健康状态:** {result['health_status']}")
                                    st.write(f"**置信度:** {result['confidence']*100:.1f}%")
                                with col2:
                                    st.write("**描述:**")
                                    st.info(result['description'][:200] + "..." if len(result['description']) > 200 else result['description'])
                        
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.subheader("综合建议")
                        st.success(all_suggestions)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # 保存到数据库
                        save_analysis_result(
                            image_path=f"视频: {uploaded_file.name}",
                            crop_type=main_crop_type,
                            health_status=overall_health,
                            confidence=avg_confidence,
                            description=f"视频分析汇总，共分析{len(all_results)}帧",
                            suggestions=all_suggestions
                        )
                        
                        # 更新历史记录
                        st.session_state.history = get_history()
                    
                except Exception as e:
                    st.error(f"视频分析出错: {str(e)}")
                    import traceback
                    st.text(traceback.format_exc())
                
                finally:
                    # 释放资源
                    if cap is not None:
                        cap.release()
                    try:
                        if os.path.exists(video_path):
                            os.unlink(video_path)
                    except PermissionError:
                        st.warning("无法删除临时视频文件，稍后将自动清理")
    
    elif not st.session_state.api_key:
        st.markdown('<div class="warning-box">请先在侧边栏输入API密钥</div>', unsafe_allow_html=True)


elif page == "历史记录":
    st.markdown('<div class="main-header">📊 分析历史记录</div>', unsafe_allow_html=True)
    
    if st.button("刷新历史记录", icon="🔄"):
        st.session_state.history = get_history(20)
        st.success("历史记录已刷新")
    
    history_data = st.session_state.history
    
    if history_data:
        df = pd.DataFrame(history_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 显示历史记录
        st.markdown('<div class="sub-header">最近分析记录</div>', unsafe_allow_html=True)
        for _, row in df.iterrows():
            with st.expander(f"{row['timestamp'].strftime('%Y-%m-%d %H:%M')} - {row['crop_type']} - {row['health_status']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.write(f"**作物类型:** {row['crop_type']}")
                    st.write(f"**健康状态:** {row['health_status']}")
                    st.write(f"**置信度:** {row['confidence']*100:.1f}%")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.write(f"**文件名:** {row['image_path']}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.write("**描述:**")
                st.info(row['description'])
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.write("**建议:**")
                st.success(row['suggestions'])
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 删除按钮
                if st.button(f"删除记录", key=f"delete_{row['id']}"):
                    delete_analysis_result(row['id'])
                    st.success("记录已删除")
                    st.session_state.history = get_history(20)
                    st.rerun()
    else:
        st.markdown('<div class="info-box">暂无历史记录</div>', unsafe_allow_html=True)


elif page == "健康趋势":
    st.markdown('<div class="main-header">📈 作物健康趋势分析</div>', unsafe_allow_html=True)
    
    history_data = st.session_state.history
    if history_data:
        crop_types = list(set([item['crop_type'] for item in history_data]))
        selected_crop = st.selectbox("选择作物类型", ["全部"] + crop_types)
        
        # 获取趋势数据
        trend_data = get_health_trend(selected_crop if selected_crop != "全部" else None)
        
        if trend_data:
            df = pd.DataFrame(trend_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['health_value'] = df['health_status'].apply(lambda x: 1 if x == '健康' else 0)
            
            # 绘制趋势图
            fig = px.line(df, x='timestamp', y='health_value', 
                         title=f'{selected_crop}健康状态变化趋势',
                         labels={'health_value': '健康状态', 'timestamp': '时间'})
            fig.update_yaxes(tickvals=[0, 1], ticktext=['不健康', '健康'])
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示统计数据
            col1, col2, col3 = st.columns(3)
            healthy_count = len(df[df['health_status'] == '健康'])
            total_count = len(df)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("总检测次数", total_count)
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("健康次数", healthy_count)
                st.markdown('</div>', unsafe_allow_html=True)
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("健康比例", f"{healthy_count/total_count*100:.1f}%" if total_count > 0 else "0%")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">暂无趋势数据</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-box">暂无历史记录，无法显示趋势</div>', unsafe_allow_html=True)


elif page == "农业问答助手":
    st.markdown('<div class="main-header">🌾 农业知识问答助手</div>', unsafe_allow_html=True)
    
    # 初始化RAG系统
    if st.session_state.api_key:
        # 获取相似度算法选择
        similarity_method = st.session_state.get('similarity_method', 'cosine')
        
        # 检查是否需要重新初始化RAG系统
        if ('rag_system' not in st.session_state or 
            not hasattr(st.session_state.rag_system, 'get_cache_stats')):
            st.session_state.rag_system = RAGQASystem(st.session_state.api_key, similarity_method)
        elif st.session_state.rag_system.knowledge_base.similarity_method != similarity_method:
            # 如果相似度方法改变，重新初始化
            st.session_state.rag_system = RAGQASystem(st.session_state.api_key, similarity_method)
        
        rag_system = st.session_state.rag_system
    else:
        rag_system = None
    
    # 知识库状态横幅 - 紧凑版
    if st.session_state.api_key and rag_system:
        kb_status = rag_system.get_knowledge_base_status()
        if kb_status['has_index'] and kb_status['stats']['total_documents'] > 0:
            st.markdown(f'''
            <div style="background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 12px 16px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-size: 1.1rem; font-weight: 600;">📚 知识库已就绪</span>
                        <span style="font-size: 0.9rem; opacity: 0.9;">📄 {kb_status["stats"]["total_documents"]} 文档</span>
                        <span style="font-size: 0.9rem; opacity: 0.9;">🧩 {kb_status["stats"]["total_chunks"]} 片段</span>
                        <span style="font-size: 0.9rem; opacity: 0.9;">💾 {kb_status["stats"]["total_size_mb"]:.1f} MB</span>
                    </div>
                    <span style="font-size: 1.2rem;">✅</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('''
            <div style="background: linear-gradient(135deg, #2196F3, #1976D2); color: white; padding: 12px 16px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(33, 150, 243, 0.2);">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <span style="font-size: 1.1rem; font-weight: 600;">📚 知识库为空</span>
                        <span style="font-size: 0.9rem; opacity: 0.9; margin-left: 10px;">将使用通用AI回答</span>
                    </div>
                    <span style="font-size: 1.2rem;">📖</span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown('''
        <div style="background: linear-gradient(135deg, #FF9800, #F57C00); color: white; padding: 12px 16px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(255, 152, 0, 0.2);">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <span style="font-size: 1.1rem; font-weight: 600;">⚠️ 需要API密钥</span>
                    <span style="font-size: 0.9rem; opacity: 0.9; margin-left: 10px;">请先输入API密钥</span>
                </div>
                <span style="font-size: 1.2rem;">🔑</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    # 创建标签页
    tab1, tab2 = st.tabs(["💬 智能问答", "📚 知识库管理"])
    
    with tab1:
        # 初始化会话状态
        if 'qa_history' not in st.session_state:
            st.session_state.qa_history = []
        if 'current_question' not in st.session_state:
            st.session_state.current_question = ""
        
        
        # 问题输入区域 - 超紧凑版
        st.markdown('''
        <div style="background: white; padding: 8px 12px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 10px; border: 1px solid #e0e0e0;">
            <h3 style="margin: 0; color: #333; font-size: 1rem; display: flex; align-items: center;">
                💭 请输入您的问题
            </h3>
        </div>
        ''', unsafe_allow_html=True)
        
        # 问题输入区域
        question = st.text_area(
            "农业问题:", 
            height=80, 
            placeholder="例如：水稻常见病害有哪些防治方法？",
            value=st.session_state.current_question,
            key="text_question_input",
            help="支持各种农业相关问题，包括种植技术、病虫害防治、施肥管理等"
        )
        
        # 设置和提交按钮区域 - 紧凑版
        col_settings, col_submit = st.columns([2, 1])
        
        with col_settings:
            # 设置选项
            col_rag, col_sources, col_similarity = st.columns(3)
            with col_rag:
                use_rag = st.checkbox("启用RAG检索", value=True, 
                                     help="启用后将从知识库中检索相关信息来回答问题")
            with col_sources:
                show_sources = st.checkbox("显示来源", value=False, 
                                          help="显示回答来源的相关文档片段")
            with col_similarity:
                similarity_method = st.selectbox(
                    "相似度算法", 
                    ["cosine", "keyword"], 
                    index=0,
                    format_func=lambda x: "余弦相似度" if x == "cosine" else "关键词匹配",
                    help="选择文档相似度计算方法"
                )
                # 更新session state
                if similarity_method != st.session_state.get('similarity_method', 'cosine'):
                    st.session_state.similarity_method = similarity_method
                    # 重新初始化RAG系统
                    if 'rag_system' in st.session_state:
                        del st.session_state.rag_system
        
        with col_submit:
            # 提交按钮
            if st.button("🚀 提交问题", type="primary", use_container_width=True, key="submit_question") and question:
                if not st.session_state.api_key:
                    st.markdown('<div class="warning-box">请先在侧边栏输入硅基流动API密钥</div>', unsafe_allow_html=True)
                else:
                    with st.spinner("🤔 正在思考中..."):
                        try:
                            # 使用RAG系统回答问题
                            result = rag_system.answer_question(question, use_rag=use_rag)
                            
                            # 保存到历史记录
                            st.session_state.qa_history.append({
                                "question": question,
                                "answer": result['answer'],
                                "source": result['source'],
                                "confidence": result['confidence'],
                                "relevant_docs": result['relevant_docs'],
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            
                            # 清空当前问题
                            st.session_state.current_question = ""
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"回答问题失败: {str(e)}")
        
        # 快速提问区域 - 超紧凑版
        st.markdown('''
        <div style="background: white; padding: 8px 12px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 10px; border: 1px solid #e0e0e0;">
            <h3 style="margin: 0; color: #333; font-size: 1rem; display: flex; align-items: center;">
                🚀 快速提问
            </h3>
        </div>
        ''', unsafe_allow_html=True)
        
        # 快速提问按钮网格 - 紧凑版
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
        
        with col1:
            if st.button("🌾 水稻", key="rice_disease", use_container_width=True):
                st.session_state.current_question = "水稻常见病虫害有哪些，如何防治？"
                st.rerun()
        
        with col2:
            if st.button("🌱 肥料", key="fertilizer_guide", use_container_width=True):
                st.session_state.current_question = "不同作物应该如何使用肥料？有什么注意事项？"
                st.rerun()
        
        with col3:
            if st.button("📅 季节", key="planting_season", use_container_width=True):
                st.session_state.current_question = "各种蔬菜的最佳种植季节是什么时候？"
                st.rerun()
        
        with col4:
            if st.button("🌿 土壤", key="soil_management", use_container_width=True):
                st.session_state.current_question = "如何改善土壤质量？有哪些土壤管理技巧？"
                st.rerun()
        
        with col5:
            if st.button("🐛 病虫", key="pest_disease", use_container_width=True):
                st.session_state.current_question = "如何识别和防治常见的农作物病虫害？"
                st.rerun()
        
        with col6:
            if st.button("💧 灌溉", key="irrigation", use_container_width=True):
                st.session_state.current_question = "不同作物的灌溉需求和管理技巧有哪些？"
                st.rerun()
        
        with col7:
            if st.button("🌱 育苗", key="seedling", use_container_width=True):
                st.session_state.current_question = "如何进行作物育苗？有哪些注意事项？"
                st.rerun()
        
        with col8:
            if st.button("🌾 收获", key="harvest", use_container_width=True):
                st.session_state.current_question = "如何判断作物成熟度并进行适时收获？"
                st.rerun()
        
        # 问答历史区域 - 紧凑版
        if st.session_state.qa_history:
            st.markdown('''
            <div style="background: white; padding: 12px 16px; border-radius: 8px; box-shadow: 0 1px 5px rgba(0,0,0,0.05); margin-bottom: 12px; border: 1px solid #e0e0e0;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <h3 style="margin: 0; color: #333; font-size: 1.1rem; display: flex; align-items: center;">
                        📚 问答历史
                    </h3>
                    <span style="background: #e3f2fd; color: #1976d2; padding: 3px 8px; border-radius: 12px; font-size: 0.75rem;">
                        {len(st.session_state.qa_history)} 条记录
                    </span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 操作按钮
            col_clear, col_export, col_filter = st.columns([1, 1, 2])
            with col_clear:
                if st.button("🗑️ 清空历史", key="clear_history", use_container_width=True):
                    st.session_state.qa_history = []
                    st.rerun()
            
            with col_export:
                if st.button("📥 导出历史", key="export_history", use_container_width=True):
                    # 简单的导出功能
                    import re
                    history_text = ""
                    for qa in st.session_state.qa_history:
                        # 清理HTML标签
                        clean_answer = re.sub(r'<[^>]+>', '', qa['answer'])
                        history_text += f"问题: {qa['question']}\n"
                        history_text += f"回答: {clean_answer}\n"
                        history_text += f"时间: {qa['timestamp']}\n"
                        history_text += "="*50 + "\n"
                    
                    st.download_button(
                        label="下载历史记录",
                        data=history_text,
                        file_name=f"农业问答历史_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
            
            with col_filter:
                filter_option = st.selectbox("筛选来源", ["全部", "知识库", "通用AI"], key="history_filter")
            
            # 显示历史记录
            filtered_history = st.session_state.qa_history
            if filter_option == "知识库":
                filtered_history = [qa for qa in st.session_state.qa_history if qa.get('source') == 'knowledge_base']
            elif filter_option == "通用AI":
                filtered_history = [qa for qa in st.session_state.qa_history if qa.get('source') != 'knowledge_base']
            
            for i, qa in enumerate(reversed(filtered_history)):
                # 根据来源设置不同的样式
                if qa.get('source') == 'knowledge_base':
                    card_style = "background: linear-gradient(135deg, #e8f5e8, #f1f8e9); border-left: 3px solid #4caf50;"
                    source_badge = "🎯 知识库"
                    confidence_text = f"置信度: {qa.get('confidence', 0):.2f}"
                    icon = "📚"
                else:
                    card_style = "background: linear-gradient(135deg, #e3f2fd, #f3e5f5); border-left: 3px solid #2196f3;"
                    source_badge = "🤖 通用AI"
                    confidence_text = ""
                    icon = "🤖"
                
                # 问题预览（截取前50个字符）
                question_preview = qa['question'][:50] + "..." if len(qa['question']) > 50 else qa['question']
                
                st.markdown(f'''
                <div style="{card_style} padding: 12px 16px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 1px 5px rgba(0,0,0,0.05);">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 8px; flex: 1;">
                            <span style="font-size: 1rem;">{icon}</span>
                            <span style="font-size: 0.9rem; color: #666;">{qa['timestamp']}</span>
                            <span style="font-size: 0.9rem; color: #333; font-weight: 500;">{question_preview}</span>
                        </div>
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <span style="background: rgba(255,255,255,0.8); padding: 2px 6px; border-radius: 10px; font-size: 0.75rem; color: #666;">
                                {source_badge}
                            </span>
                            {f'<span style="background: rgba(255,255,255,0.8); padding: 2px 6px; border-radius: 10px; font-size: 0.75rem; color: #666;">{confidence_text}</span>' if confidence_text else ''}
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                with st.expander(f"💬 查看详情", expanded=False):
                    # 问题部分
                    st.markdown(f"**❓ 问题:** {qa['question']}")
                    
                    # 回答部分
                    st.markdown("**💡 回答:**")
                    # 清理HTML标签，只显示纯文本内容
                    import re
                    clean_answer = re.sub(r'<[^>]+>', '', qa['answer'])
                    st.markdown(clean_answer)
                    
                    # 相关文档（如果启用）
                    if show_sources and qa.get('relevant_docs'):
                        st.markdown("**📄 相关文档片段:**")
                        for j, doc in enumerate(qa['relevant_docs'][:3], 1):
                            with st.container():
                                st.markdown(f"**片段 {j}** (相似度: {doc['similarity_score']:.2f}):")
                                st.info(doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'])
                    
                    # 操作按钮
                    if st.button("📋 复制答案", key=f"copy_{i}"):
                        # 清理HTML标签后显示
                        clean_answer = re.sub(r'<[^>]+>', '', qa['answer'])
                        st.code(clean_answer, language=None)
                        st.success("答案已复制到剪贴板")
        else:
            st.markdown('''
            <div style="text-align: center; padding: 60px 40px; border-radius: 15px; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border: 1px solid #dee2e6; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
                <div style="font-size: 4rem; margin-bottom: 20px;">📝</div>
                <h4 style="color: #6c757d; margin-bottom: 15px; font-size: 1.3rem;">暂无问答历史</h4>
                <p style="color: #6c757d; margin: 0; font-size: 1rem;">开始提问，我会为您记录每次对话</p>
            </div>
            ''', unsafe_allow_html=True)
    
    with tab2:
        # 知识库管理功能 - 紧凑版
        st.markdown('''
        <div style="background: white; padding: 16px 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #e0e0e0;">
            <h3 style="margin: 0 0 8px 0; color: #333; font-size: 1.2rem; display: flex; align-items: center;">
                📚 知识库管理
            </h3>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">管理您的农业知识库，上传文档，构建专业的知识体系</p>
        </div>
        ''', unsafe_allow_html=True)
        
        if not st.session_state.api_key:
            st.markdown('''
            <div style="text-align: center; padding: 50px 30px; border-radius: 15px; background: linear-gradient(135deg, #fff3cd, #ffeaa7); border: 1px solid #ffeaa7; box-shadow: 0 4px 20px rgba(255, 152, 0, 0.1);">
                <div style="font-size: 3rem; margin-bottom: 20px;">⚠️</div>
                <h4 style="color: #856404; margin-bottom: 15px; font-size: 1.3rem;">需要API密钥</h4>
                <p style="color: #856404; margin: 0; font-size: 1rem;">请先在侧边栏输入硅基流动API密钥以使用知识库管理功能</p>
            </div>
            ''', unsafe_allow_html=True)
        else:
            # 知识库统计信息卡片
            kb_status = rag_system.get_knowledge_base_status()
            
            # 安全获取缓存统计
            try:
                cache_stats = rag_system.get_cache_stats()
            except AttributeError:
                # 如果RAG系统没有缓存统计方法，使用默认值
                cache_stats = {
                    'overall_hit_rate': 0.0,
                    'total_cached_items': 0,
                    'knowledge_base': {
                        'search_cache': {'hit_count': 0}
                    },
                    'api_cache': {'hit_count': 0}
                }
            
            st.markdown('''
            <div style="background: white; padding: 16px 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #e0e0e0;">
                <h3 style="margin: 0; color: #333; font-size: 1.2rem; display: flex; align-items: center;">
                    📊 知识库统计
                </h3>
            </div>
            ''', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f'''
                <div style="text-align: center; padding: 16px; border-radius: 10px; background: linear-gradient(135deg, #e3f2fd, #bbdefb); border: 1px solid #90caf9; box-shadow: 0 2px 8px rgba(33, 150, 243, 0.15);">
                    <div style="font-size: 1.8rem; margin-bottom: 8px;">📄</div>
                    <h3 style="margin: 0; color: #1976d2; font-size: 1.5rem; font-weight: 700;">{kb_status['stats']['total_documents']}</h3>
                    <p style="margin: 4px 0 0 0; color: #1976d2; font-weight: 500; font-size: 0.9rem;">文档数量</p>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'''
                <div style="text-align: center; padding: 16px; border-radius: 10px; background: linear-gradient(135deg, #f3e5f5, #e1bee7); border: 1px solid #ce93d8; box-shadow: 0 2px 8px rgba(156, 39, 176, 0.15);">
                    <div style="font-size: 1.8rem; margin-bottom: 8px;">🧩</div>
                    <h3 style="margin: 0; color: #7b1fa2; font-size: 1.5rem; font-weight: 700;">{kb_status['stats']['total_chunks']}</h3>
                    <p style="margin: 4px 0 0 0; color: #7b1fa2; font-weight: 500; font-size: 0.9rem;">知识片段</p>
                </div>
                ''', unsafe_allow_html=True)
            
            with col3:
                st.markdown(f'''
                <div style="text-align: center; padding: 16px; border-radius: 10px; background: linear-gradient(135deg, #e8f5e8, #c8e6c9); border: 1px solid #a5d6a7; box-shadow: 0 2px 8px rgba(76, 175, 80, 0.15);">
                    <div style="font-size: 1.8rem; margin-bottom: 8px;">💾</div>
                    <h3 style="margin: 0; color: #388e3c; font-size: 1.5rem; font-weight: 700;">{kb_status['stats']['total_size_mb']:.1f} MB</h3>
                    <p style="margin: 4px 0 0 0; color: #388e3c; font-weight: 500; font-size: 0.9rem;">存储大小</p>
                </div>
                ''', unsafe_allow_html=True)
            
            with col4:
                st.markdown(f'''
                <div style="text-align: center; padding: 16px; border-radius: 10px; background: linear-gradient(135deg, #fff3e0, #ffcc80); border: 1px solid #ffb74d; box-shadow: 0 2px 8px rgba(255, 152, 0, 0.15);">
                    <div style="font-size: 1.8rem; margin-bottom: 8px;">📁</div>
                    <h3 style="margin: 0; color: #f57c00; font-size: 1.5rem; font-weight: 700;">{len(kb_status['stats']['file_types'])}</h3>
                    <p style="margin: 4px 0 0 0; color: #f57c00; font-weight: 500; font-size: 0.9rem;">文件类型</p>
                </div>
                ''', unsafe_allow_html=True)
            
            # 缓存统计信息
            st.markdown('''
            <div style="background: white; padding: 16px 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #e0e0e0;">
                <h3 style="margin: 0 0 8px 0; color: #333; font-size: 1.2rem; display: flex; align-items: center;">
                    🚀 缓存性能统计
                </h3>
            </div>
            ''', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f'''
                <div style="text-align: center; padding: 16px; border-radius: 10px; background: linear-gradient(135deg, #e8f5e8, #c8e6c9); border: 1px solid #a5d6a7; box-shadow: 0 2px 8px rgba(76, 175, 80, 0.15);">
                    <div style="font-size: 1.8rem; margin-bottom: 8px;">🎯</div>
                    <h3 style="margin: 0; color: #388e3c; font-size: 1.5rem; font-weight: 700;">{cache_stats['overall_hit_rate']:.1%}</h3>
                    <p style="margin: 4px 0 0 0; color: #388e3c; font-weight: 500; font-size: 0.9rem;">缓存命中率</p>
                </div>
                ''', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'''
                <div style="text-align: center; padding: 16px; border-radius: 10px; background: linear-gradient(135deg, #e3f2fd, #bbdefb); border: 1px solid #90caf9; box-shadow: 0 2px 8px rgba(33, 150, 243, 0.15);">
                    <div style="font-size: 1.8rem; margin-bottom: 8px;">📦</div>
                    <h3 style="margin: 0; color: #1976d2; font-size: 1.5rem; font-weight: 700;">{cache_stats['total_cached_items']}</h3>
                    <p style="margin: 4px 0 0 0; color: #1976d2; font-weight: 500; font-size: 0.9rem;">缓存项数</p>
                </div>
                ''', unsafe_allow_html=True)
            
            with col3:
                st.markdown(f'''
                <div style="text-align: center; padding: 16px; border-radius: 10px; background: linear-gradient(135deg, #f3e5f5, #e1bee7); border: 1px solid #ce93d8; box-shadow: 0 2px 8px rgba(156, 39, 176, 0.15);">
                    <div style="font-size: 1.8rem; margin-bottom: 8px;">🔍</div>
                    <h3 style="margin: 0; color: #7b1fa2; font-size: 1.5rem; font-weight: 700;">{cache_stats['knowledge_base']['search_cache']['hit_count']}</h3>
                    <p style="margin: 4px 0 0 0; color: #7b1fa2; font-weight: 500; font-size: 0.9rem;">搜索命中</p>
                </div>
                ''', unsafe_allow_html=True)
            
            with col4:
                st.markdown(f'''
                <div style="text-align: center; padding: 16px; border-radius: 10px; background: linear-gradient(135deg, #fff3e0, #ffcc80); border: 1px solid #ffb74d; box-shadow: 0 2px 8px rgba(255, 152, 0, 0.15);">
                    <div style="font-size: 1.8rem; margin-bottom: 8px;">🤖</div>
                    <h3 style="margin: 0; color: #f57c00; font-size: 1.5rem; font-weight: 700;">{cache_stats['api_cache']['hit_count']}</h3>
                    <p style="margin: 4px 0 0 0; color: #f57c00; font-weight: 500; font-size: 0.9rem;">API命中</p>
                </div>
                ''', unsafe_allow_html=True)
            
            # 缓存管理按钮
            st.markdown('''
            <div style="background: white; padding: 16px 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #e0e0e0;">
                <h3 style="margin: 0 0 8px 0; color: #333; font-size: 1.2rem; display: flex; align-items: center;">
                    ⚙️ 缓存管理
                </h3>
            </div>
            ''', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🗑️ 清空缓存", use_container_width=True):
                    try:
                        rag_system.clear_all_cache()
                        st.success("缓存已清空")
                    except AttributeError:
                        st.error("缓存功能不可用，请刷新页面")
                    st.rerun()
            
            with col2:
                if st.button("🧹 清理过期", use_container_width=True):
                    try:
                        cleaned = rag_system.cleanup_expired_cache()
                        if cleaned > 0:
                            st.success(f"清理了 {cleaned} 个过期缓存项")
                        else:
                            st.info("没有过期缓存项需要清理")
                    except AttributeError:
                        st.error("缓存功能不可用，请刷新页面")
                    st.rerun()
            
            with col3:
                if st.button("🔄 重新初始化", use_container_width=True):
                    # 强制重新初始化RAG系统
                    if 'rag_system' in st.session_state:
                        del st.session_state.rag_system
                    st.success("系统已重新初始化")
                    st.rerun()
            
            # 文档上传区域 - 紧凑版
            st.markdown('''
            <div style="background: white; padding: 16px 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #e0e0e0;">
                <h3 style="margin: 0 0 8px 0; color: #333; font-size: 1.2rem; display: flex; align-items: center;">
                    📤 上传文档
                </h3>
                <p style="margin: 0; color: #666; font-size: 0.9rem;">支持TXT格式文档，支持批量上传，系统会自动处理文档分块和关键词提取</p>
            </div>
            ''', unsafe_allow_html=True)
            
            # 创建上传区域
            uploaded_files = st.file_uploader(
                "选择要上传的文档",
                type=['txt'],
                accept_multiple_files=True,
                help="目前支持 TXT 格式的文档，支持批量上传",
                label_visibility="collapsed"
            )
            
            if uploaded_files:
                st.markdown("#### 📋 上传进度")
                for uploaded_file in uploaded_files:
                    with st.container():
                        col_file, col_progress = st.columns([3, 1])
                        
                        with col_file:
                            st.markdown(f"**📄 {uploaded_file.name}** ({uploaded_file.size} 字节)")
                        
                        with col_progress:
                            with st.spinner("处理中..."):
                                try:
                                    file_content = uploaded_file.read()
                                    
                                    # 显示文件内容预览
                                    try:
                                        content_preview = file_content.decode('utf-8')[:150]
                                        with st.expander("📖 内容预览", expanded=False):
                                            st.text(content_preview + "..." if len(content_preview) == 150 else content_preview)
                                    except:
                                        st.warning("文件内容无法解码为UTF-8")
                                    
                                    success = rag_system.upload_document(file_content, uploaded_file.name)
                                    if success:
                                        st.success("✅ 上传成功")
                                    else:
                                        st.error("❌ 上传失败")
                                except Exception as e:
                                    st.error(f"❌ 处理失败: {str(e)}")
                                    with st.expander("错误详情", expanded=False):
                                        import traceback
                                        st.text(traceback.format_exc())
            
            # 文档管理 - 紧凑版
            st.markdown('''
            <div style="background: white; padding: 16px 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #e0e0e0;">
                <h3 style="margin: 0 0 8px 0; color: #333; font-size: 1.2rem; display: flex; align-items: center;">
                    📋 文档列表
                </h3>
                <p style="margin: 0; color: #666; font-size: 0.9rem;">管理已上传的文档，测试搜索功能，维护知识库内容</p>
            </div>
            ''', unsafe_allow_html=True)
            
            # 操作按钮
            col_refresh, col_test, col_clear = st.columns([1, 1, 1])
            with col_refresh:
                if st.button("🔄 刷新列表", key="refresh_docs", use_container_width=True):
                    st.rerun()
            
            with col_test:
                if st.button("🧪 测试搜索", key="test_search", use_container_width=True):
                    test_query = st.text_input("输入测试查询", key="test_query_input")
                    if test_query:
                        results = rag_system.search_documents(test_query, top_k=5)
                        if results:
                            st.write("**搜索结果:**")
                            for i, result in enumerate(results, 1):
                                st.write(f"**{i}. 相似度: {result['similarity_score']:.3f}**")
                                st.write(f"内容: {result['content'][:150]}...")
                                st.write("---")
                        else:
                            st.write("未找到相关内容")
            
            with col_clear:
                if st.button("🗑️ 清空知识库", key="clear_kb", use_container_width=True):
                    if st.session_state.get('confirm_clear', False):
                        # 执行清空操作
                        documents = rag_system.get_document_list()
                        for doc in documents:
                            rag_system.delete_document(doc['id'])
                        st.success("知识库已清空")
                        st.session_state.confirm_clear = False
                        st.rerun()
                    else:
                        st.session_state.confirm_clear = True
                        st.warning("⚠️ 再次点击确认清空知识库")
            
            # 获取文档列表
            documents = rag_system.get_document_list()
            
            if documents:
                st.markdown(f'''
                <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #e9ecef;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.2rem;">📊</span>
                        <span style="font-weight: 600; color: #495057;">共找到 {len(documents)} 个文档</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                for doc in documents:
                    # 根据处理状态设置不同的样式
                    if doc['processed']:
                        status_icon = "✅"
                        status_text = "已处理"
                        card_style = "background: linear-gradient(135deg, #e8f5e8, #f1f8e9); border-left: 4px solid #4caf50;"
                        status_color = "#4caf50"
                    else:
                        status_icon = "⏳"
                        status_text = "处理中"
                        card_style = "background: linear-gradient(135deg, #fff3e0, #ffe0b2); border-left: 4px solid #ff9800;"
                        status_color = "#ff9800"
                    
                    st.markdown(f'''
                    <div style="{card_style} padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                            <h4 style="margin: 0; color: #333; font-size: 1.1rem; display: flex; align-items: center;">
                                {status_icon} {doc['filename']}
                            </h4>
                            <div style="display: flex; gap: 10px; align-items: center;">
                                <span style="background: rgba(255,255,255,0.7); padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; color: #666;">
                                    {doc['file_type']}
                                </span>
                                <span style="background: rgba(255,255,255,0.7); padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; color: #666;">
                                    {status_text}
                                </span>
                            </div>
                        </div>
                        <div style="display: flex; gap: 20px; font-size: 0.9rem; color: #666;">
                            <span>📏 {doc['file_size']:,} 字节</span>
                            <span>⏰ {doc['upload_time']}</span>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    with st.expander(f"管理文档", expanded=False):
                        # 文档信息
                        col_info, col_actions = st.columns([2, 1])
                        
                        with col_info:
                            st.markdown(f"**📄 文件名:** {doc['filename']}")
                            st.markdown(f"**📁 文件类型:** {doc['file_type']}")
                            st.markdown(f"**📏 文件大小:** {doc['file_size']:,} 字节")
                            st.markdown(f"**⏰ 上传时间:** {doc['upload_time']}")
                            st.markdown(f"**🔄 处理状态:** {status_icon} {status_text}")
                        
                        with col_actions:
                            # 搜索测试
                            if st.button("🔍 搜索测试", key=f"search_{doc['id']}", use_container_width=True):
                                test_query = st.text_input("输入搜索关键词", key=f"query_{doc['id']}")
                                if test_query:
                                    results = rag_system.search_documents(test_query, top_k=3)
                                    if results:
                                        st.write("**搜索结果:**")
                                        for i, result in enumerate(results, 1):
                                            st.write(f"{i}. 相似度: {result['similarity_score']:.2f}")
                                            st.write(result['content'][:100] + "...")
                                    else:
                                        st.write("未找到相关内容")
                            
                            # 删除文档
                            if st.button("🗑️ 删除", key=f"delete_{doc['id']}", use_container_width=True):
                                if rag_system.delete_document(doc['id']):
                                    st.success("文档已删除")
                                    st.rerun()
                                else:
                                    st.error("删除失败")
            else:
                st.markdown('''
                <div style="text-align: center; padding: 60px 40px; border-radius: 15px; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border: 1px solid #dee2e6; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
                    <div style="font-size: 4rem; margin-bottom: 20px;">📚</div>
                    <h4 style="color: #6c757d; margin-bottom: 15px; font-size: 1.3rem;">暂无文档</h4>
                    <p style="color: #6c757d; margin: 0; font-size: 1rem;">请上传文档开始使用知识库功能</p>
                </div>
                ''', unsafe_allow_html=True)
            
            # 知识库操作
            st.markdown('<div class="sub-header">🔧 知识库操作</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 重建索引", help="重新构建向量索引"):
                    with st.spinner("正在重建索引..."):
                        rag_system.rebuild_knowledge_base()
                        st.success("索引重建完成")
                        st.rerun()
            
            with col2:
                if st.button("📊 查看统计", help="查看详细统计信息"):
                    stats = kb_status['stats']
                    st.write("**详细统计信息:**")
                    st.write(f"- 总文档数: {stats['total_documents']}")
                    st.write(f"- 总片段数: {stats['total_chunks']}")
                    st.write(f"- 总大小: {stats['total_size_mb']} MB")
                    st.write(f"- 文件类型分布: {stats['file_types']}")
            
            with col3:
                if st.button("🧪 测试搜索", help="测试知识库搜索功能"):
                    test_query = st.text_input("输入测试查询", key="test_query")
                    if test_query:
                        results = rag_system.search_documents(test_query, top_k=5)
                        if results:
                            st.write("**搜索结果:**")
                            for i, result in enumerate(results, 1):
                                st.write(f"**{i}. 相似度: {result['similarity_score']:.3f}**")
                                st.write(f"内容: {result['content'][:150]}...")
                                st.write("---")
                        else:
                            st.write("未找到相关内容")


elif page == "种植计划":
    st.markdown('<div class="main-header">🌾 农作物种植计划管理</div>', unsafe_allow_html=True)
    
    # 1. 生成种植建议
    st.markdown('<div class="sub-header">一、生成种植建议</div>', unsafe_allow_html=True)
    
    # 添加地区输入组件
    col1, col2 = st.columns(2)
    with col1:
        # 将作物类型从选择框改为文本输入框
        crop_type = st.text_input("作物类型", placeholder="例如：水稻、玉米、番茄等", 
                                 help="请输入您想种植的作物名称")
    
    with col2:
        # 添加地区输入
        region = st.text_input("所在地区", placeholder="例如：北京、广东、东北等", 
                              help="请输入您所在的地区，这将帮助生成更符合当地气候的种植建议")
    
    # 生成建议按钮
    if st.button("生成种植建议", type="primary") and st.session_state.api_key and crop_type:
        with st.spinner("正在分析该作物在您所在地区的适宜性并生成种植建议..."):
            try:
                api = SilicanAPI(st.session_state.api_key)
                
                # 先检查作物是否适合在该地区种植
                suitability_prompt = f"请分析{region}地区是否适合种植{crop_type}。请给出明确的判断（适合/不适合），并简要说明原因。如果适合，请继续提供种植建议；如果不适合，请说明原因并推荐替代作物。"
                
                suitability_result = api.agricultural_qa(suitability_prompt)
                
                # 检查是否适合种植
                if "不适合" in suitability_result or "不宜" in suitability_result:
                    st.markdown('<div class="warning-box">⚠️ 种植适宜性分析</div>', unsafe_allow_html=True)
                    st.error(f"根据分析，{crop_type}在{region}地区可能不太适合种植。原因如下：")
                    st.info(suitability_result)
                    
                    # 提供替代作物建议
                    alternative_prompt = f"既然{crop_type}不适合在{region}地区种植，请推荐3-5种适合{region}地区种植的类似作物，并简要说明每种作物的特点。"
                    alternative_result = api.agricultural_qa(alternative_prompt)
                    
                    st.markdown('<div class="sub-header">替代作物建议</div>', unsafe_allow_html=True)
                    st.success(alternative_result)
                    
                else:
                    # 适合种植，生成详细种植建议
                    st.markdown('<div class="success-box">✅ 种植适宜性分析</div>', unsafe_allow_html=True)
                    st.success(f"根据分析，{crop_type}适合在{region}地区种植！")
                    
                    # 生成详细的种植建议
                    if region:
                        prompt = f"请为{region}地区的{crop_type}提供详细的种植计划，包括关键时间节点和农事活动，考虑当地的气候条件和种植习惯。请提供具体的时间建议和操作指南。"
                    else:
                        prompt = f"请为{crop_type}提供详细的种植计划，包括关键时间节点和农事活动。请提供具体的时间建议和操作指南。"
                    
                    # 生成种植建议
                    advice = api.generate_planting_advice(crop_type, prompt)
                    # 提取关键事件
                    events = api.extract_events_from_advice(advice)
                    
                    # 保存到会话状态
                    st.session_state.extracted_events = events
                    st.session_state.planting_advice = advice
                    st.session_state.selected_crop_for_advice = crop_type
                    st.session_state.region = region
                    
                    # 显示建议和事件
                    st.markdown('<div class="sub-header">种植建议</div>', unsafe_allow_html=True)
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.info(advice)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('<div class="sub-header">提取的关键农事事件</div>', unsafe_allow_html=True)
                    if events:
                        for i, event in enumerate(events):
                            st.markdown('<div class="card crop-card">', unsafe_allow_html=True)
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])  
                            with col1:
                                st.write(f"**{event['activity']}**")
                            with col2:
                                st.write(f"推荐时间: {event['time_reference']}")
                            with col3:
                                st.write(f"重要性: {event['importance']}")
                            with col4:
                                # 只保留"添加到日程"按钮
                                if st.button("添加", key=f"add_{i}"):
                                    save_planting_schedule(
                                        crop_type=crop_type,
                                        activity=event['activity'],
                                        time_reference=event['time_reference'],
                                        importance=event['importance']
                                    )
                                    st.success("已添加到种植日程")
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="warning-box">未能从建议中提取到关键事件</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"生成建议失败: {str(e)}")
    elif not crop_type:
        st.markdown('<div class="warning-box">请输入作物类型</div>', unsafe_allow_html=True)
    
    # 显示缓存的建议
    elif (st.session_state.get('selected_crop_for_advice') == crop_type and 
          st.session_state.get('planting_advice') and
          st.session_state.get('region') == region):  # 添加地区比较条件
        
        st.markdown('<div class="sub-header">种植建议</div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.info(st.session_state.planting_advice)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sub-header">提取的关键农事事件</div>', unsafe_allow_html=True)
        if st.session_state.extracted_events:
            for i, event in enumerate(st.session_state.extracted_events):
                st.markdown('<div class="card crop-card">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.write(f"**{event['activity']}**")
                with col2:
                    st.write(f"推荐时间: {event['time_reference']}")
                with col3:
                    st.write(f"重要性: {event['importance']}")
                with col4:
                    if st.button("添加", key=f"add_cache_{i}"):
                        save_planting_schedule(
                            crop_type=crop_type,
                            activity=event['activity'],
                            time_reference=event['time_reference'],
                            importance=event['importance']
                        )
                        st.success("已添加到种植日程")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    
    # 2. 我的种植日程管理
    st.markdown("---")
    st.markdown('<div class="sub-header">二、我的种植日程</div>', unsafe_allow_html=True)
    
    # 加载日程数据
    user_schedule = get_planting_schedules()
    
    if user_schedule:
        # 显示到期提醒（系统内）
        due_reminders = get_due_reminders()
        if due_reminders:
            st.markdown('<div class="warning-box">📢 到期提醒：以下农事活动已到期，请及时处理！</div>', unsafe_allow_html=True)
            for reminder in due_reminders:
                st.error(f"• {reminder['crop_type']} - {reminder['activity']}（计划日期：{reminder['custom_date'] or '未设置'}）")
        
        # 显示所有日程
        for i, task in enumerate(user_schedule):
            with st.expander(f"{task['crop_type']} - {task['activity']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.write(f"**作物类型:** {task['crop_type']}")
                    st.write(f"**农事活动:** {task['activity']}")
                    st.write(f"**推荐时间:** {task['time_reference']}")
                    st.write(f"**重要性:** {task['importance']}")
                    st.write(f"**当前计划日期:** {task['custom_date'] or '未设置'}")
                    st.write(f"**创建时间:** {task['created_at']}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    # 只保留日期修改
                    # 处理默认日期
                    default_date = None
                    if task['custom_date']:
                        try:
                            default_date = datetime.strptime(task['custom_date'], "%Y-%m-%d").date()
                        except ValueError:
                            default_date = date.today()
                    else:
                        default_date = date.today()
                    
                    # 日期选择器
                    custom_date = st.date_input(
                        "修改计划日期", 
                        value=default_date,
                        key=f"date_{i}"
                    )
                    
                    # 保存日期按钮
                    if st.button("保存日期", key=f"save_date_{i}"):
                        update_planting_schedule(
                            schedule_id=task['id'],
                            custom_date=custom_date
                        )
                        st.success("计划日期已更新")
                        st.rerun()
                    
                    # 删除按钮
                    if st.button("删除日程", key=f"delete_schedule_{i}"):
                        delete_planting_schedule(task['id'])
                        st.success("已删除该种植日程")
                        st.rerun()
    else:
        st.markdown('<div class="info-box">暂无种植日程，请先通过「生成种植建议」添加农事活动</div>', unsafe_allow_html=True)

elif page == "天气预警":
    st.markdown('<div class="main-header">🌦️ 天气预警与监测</div>', unsafe_allow_html=True)
    
    # 初始化天气API
    weather_api = WeatherAPI()
    
    # 天气设置
    with st.expander("天气设置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            location = st.text_input("城市名称", st.session_state.weather_location)
            
            # 获取用户可能种植的作物类型（从历史记录中提取）
            history_data = st.session_state.history
            crop_options = ["全部作物"]
            if history_data:
                crop_types = list(set([item['crop_type'] for item in history_data if item['crop_type'] != "未知作物"]))
                crop_options.extend(crop_types)
            
            selected_crops = st.multiselect(
                "关注的作物类型",
                options=crop_options,
                default=st.session_state.selected_crops
            )
        
        with col2:
            alert_types = st.multiselect(
                "关注预警类型",
                ["暴雨", "大风", "寒潮", "干旱", "高温", "冰雹", "霜冻"],
                default=st.session_state.alert_types
            )
            
            if st.button("保存设置", type="primary"):
                st.session_state.weather_location = location
                st.session_state.selected_crops = selected_crops
                st.session_state.alert_types = alert_types
                st.success("天气设置已保存")
    
    # 获取天气信息
    if st.button("获取最新天气信息", type="primary"):
        with st.spinner("获取天气数据中..."):
            current_weather = weather_api.get_current_weather(location)
            weather_alerts = weather_api.get_weather_alerts(location)
            weather_forecast = weather_api.get_weather_forecast(location)
            
            if current_weather:
                st.session_state.current_weather = current_weather
                st.session_state.weather_alerts = weather_alerts
                st.session_state.weather_forecast = weather_forecast
                st.session_state.weather_location = location
                
                # 保存预警信息到数据库
                if weather_alerts:
                    conn = sqlite3.connect('crop_health.db')
                    c = conn.cursor()
                    
                    for alert in weather_alerts:
                        # 转换时间戳为可读格式
                        start_time = datetime.fromisoformat(alert.get('start').replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(alert.get('end').replace('Z', '+00:00'))
                        
                        c.execute('''INSERT OR IGNORE INTO weather_alerts 
                                     (location, alert_type, severity, description, effective_time, expiration_time)
                                     VALUES (?, ?, ?, ?, ?, ?)''',
                                 (location, alert.get('event', '未知'), 
                                  alert.get('severity', '未知'), 
                                  alert.get('description', '无详细描述'),
                                  start_time, end_time))
                    
                    conn.commit()
                    conn.close()
            else:
                st.error("获取天气数据失败，请检查城市名称是否正确")
    
    # 显示当前天气
    if st.session_state.current_weather:
        current_weather = st.session_state.current_weather
        weather_alerts = st.session_state.weather_alerts
        weather_forecast = st.session_state.weather_forecast
        location = st.session_state.weather_location
        
        st.markdown('<div class="sub-header">当前天气</div>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            temp = current_weather['main']['temp']
            st.metric("温度", f"{temp}°C")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            humidity = current_weather['main']['humidity']
            st.metric("湿度", f"{humidity}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            wind_speed = current_weather['wind']['speed']
            st.metric("风速", f"{wind_speed} m/s")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            weather_desc = current_weather['weather'][0]['description']
            st.metric("天气状况", weather_desc)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 显示天气预报
        st.markdown('<div class="sub-header">未来3天天气预报</div>', unsafe_allow_html=True)
        if weather_forecast:
            forecast_data = []
            for day in weather_forecast['daily']:
                forecast_data.append({
                    "日期": day['fxDate'],
                    "白天": day['textDay'],
                    "夜间": day['textNight'],
                    "最低温度": f"{day['tempMin']}°C",
                    "最高温度": f"{day['tempMax']}°C",
                    "风向": day['windDirDay'],
                    "风力": f"{day['windScaleDay']}级",
                    "降水量": f"{day['precip']}mm"
                })
            
            forecast_df = pd.DataFrame(forecast_data)
            st.dataframe(forecast_df, use_container_width=True)
        else:
            st.markdown('<div class="info-box">无法获取天气预报数据</div>', unsafe_allow_html=True)
        
        # 显示天气预警
        st.markdown('<div class="sub-header">天气预警信息</div>', unsafe_allow_html=True)
        if weather_alerts:
            for alert in weather_alerts:
                alert_type = alert.get('event', '未知预警')
                sender = alert.get('sender_name', '气象部门')
                
                # 只显示用户关注的预警类型
                if alert_type not in st.session_state.alert_types:
                    continue
                
                with st.expander(f"⚠️ {alert_type}预警 - {sender}", expanded=True):
                    st.error(f"预警类型: {alert_type}")
                    st.write(f"发布时间: {sender}")
                    st.write(f"开始时间: {alert.get('start')}")
                    st.write(f"结束时间: {alert.get('end')}")
                    st.write(f"描述: {alert.get('description', '无详细描述')}")
                    
                    # 使用AI模型生成预防建议
                    if st.button(f"生成{alert_type}预防建议", key=f"advice_{alert_type}"):
                        with st.spinner("生成预防建议中..."):
                            # 获取用户关注的作物类型
                            crops = st.session_state.selected_crops
                            if "全部作物" in crops:
                                crops = ["主要农作物"]  # 使用通用描述
                            
                            # 调用硅基流动API生成建议
                            try:
                                api = SilicanAPI(st.session_state.api_key)
                                advice_prompt = f"""你是一名农业专家，请根据以下天气预警信息为{', '.join(crops)}种植提供专业的预防建议：

预警类型: {alert_type}
预警描述: {alert.get('description', '无详细描述')}
预警时间: 从{alert.get('start')}到{alert.get('end')}

请提供:
1. 具体的防护措施
2. 建议的操作时间
3. 需要准备的物资
4. 长期应对策略

请用中文回答，内容要详细、实用，适合农民朋友理解:"""
                                
                                advice = api.agricultural_qa(advice_prompt)
                                st.info(f"**预防建议:**\n\n{advice}")
                            except Exception as e:
                                st.error(f"生成建议失败: {str(e)}")
        else:
            st.markdown('<div class="success-box">当前暂无天气预警</div>', unsafe_allow_html=True)
    
    else:
        st.markdown('<div class="info-box">请点击「获取最新天气信息」按钮获取天气数据</div>', unsafe_allow_html=True)


elif page == "电子农场":
    st.markdown('<div class="main-header">🌱 电子农场</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">在这里您可以种植虚拟作物，通过每日打卡获取水滴和肥料，帮助作物成长！</div>', unsafe_allow_html=True)
    
    # 初始化用户资源
    user_resources = get_user_resources()
    electronic_crop = get_electronic_crop()
    
    # 显示用户资源
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("💧 水滴", user_resources['water'])
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("🌱 肥料", user_resources['fertilizer'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 每日打卡功能
    st.markdown('<div class="sub-header">每日打卡</div>', unsafe_allow_html=True)
    today = date.today().isoformat()
    
    if user_resources['last_checkin'] == today:
        st.markdown('<div class="success-box">✅ 今日已打卡</div>', unsafe_allow_html=True)
    else:
        if st.button("📅 每日打卡", type="primary"):
            import random
            # 随机奖励：70%概率获得水滴，30%概率获得肥料
            if random.random() < 0.7:
                reward_type = "water"
                reward_amount = random.randint(1, 3)
                new_water = user_resources['water'] + reward_amount
                update_user_resources(1, water=new_water, last_checkin=today)
                st.success(f"🎉 打卡成功！获得 {reward_amount} 滴水滴💧")
            else:
                reward_type = "fertilizer"
                reward_amount = random.randint(1, 2)
                new_fertilizer = user_resources['fertilizer'] + reward_amount
                update_user_resources(1, fertilizer=new_fertilizer, last_checkin=today)
                st.success(f"🎉 打卡成功！获得 {reward_amount} 份肥料🌱")
            
            # 记录打卡
            add_checkin_record(1, today, reward_type, reward_amount)
            st.rerun()
    
    st.markdown("---")
    
    # 电子作物种植区域
    st.markdown('<div class="sub-header">我的电子作物</div>', unsafe_allow_html=True)
    
    if electronic_crop is None:
        # 选择要种植的作物
        crop_options = ["番茄", "水稻", "玉米", "小麦", "黄瓜", "草莓"]
        selected_crop = st.selectbox("选择要种植的作物", crop_options)
        
        if st.button("🌱 开始种植", type="primary"):
            plant_electronic_crop(selected_crop)
            st.success(f"已开始种植{selected_crop}！")
            st.rerun()
    else:
        # 显示作物状态
        st.write(f"**作物类型:** {electronic_crop['crop_type']}")
        
        # 根据生长阶段显示不同的图片或文字描述
        growth_stages = {
            0: {"name": "种子阶段", "description": "刚刚种下的种子，需要精心照料", "water_need": 3, "fertilizer_need": 1},
            1: {"name": "发芽阶段", "description": "种子已经发芽，长出嫩叶", "water_need": 5, "fertilizer_need": 2},
            2: {"name": "生长阶段", "description": "作物正在快速生长", "water_need": 8, "fertilizer_need": 3},
            3: {"name": "开花阶段", "description": "作物开始开花，即将结果", "water_need": 10, "fertilizer_need": 4},
            4: {"name": "成熟阶段", "description": "作物已经成熟，可以收获了！", "water_need": 0, "fertilizer_need": 0}
        }
        
        current_stage = growth_stages[electronic_crop['growth_stage']]
        next_stage = electronic_crop['growth_stage'] + 1 if electronic_crop['growth_stage'] < 4 else 4
        
        st.write(f"**生长阶段:** {current_stage['name']} ({electronic_crop['growth_stage']+1}/5)")
        st.write(f"**描述:** {current_stage['description']}")
        
        # 显示进度条
        progress_value = min(1.0, (electronic_crop['water_count'] + electronic_crop['fertilizer_count']) / 
                            (current_stage['water_need'] + current_stage['fertilizer_need']))
        st.progress(progress_value)
        
        st.write(f"💧 浇水: {electronic_crop['water_count']}/{current_stage['water_need']}")
        st.write(f"🌱 施肥: {electronic_crop['fertilizer_count']}/{current_stage['fertilizer_need']}")
        
        # 显示作物图片（如果有）
        growth_stage_images = {
            0: "images/seed.png",
            1: "images/sprout.png",
            2: "images/growing.png",
            3: "images/flowering.png",
            4: "images/mature.png"
        }
        
        # 检查图片是否存在，如果存在则显示
        image_path = growth_stage_images.get(electronic_crop['growth_stage'])
        if image_path and os.path.exists(image_path):
            st.image(image_path, width=200)
        else:
            # 如果没有图片，显示一个占位符
            st.info("🌱 作物生长中...")
        
        # 浇水施肥操作
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💧 浇水", disabled=user_resources['water'] < 1):
                if electronic_crop['water_count'] < current_stage['water_need']:
                    update_user_resources(1, water=user_resources['water'] - 1)
                    update_electronic_crop(1, water_count=electronic_crop['water_count'] + 1)
                    st.success("浇水成功！")
                else:
                    st.warning("当前阶段不需要更多水了")
                st.rerun()
        
        with col2:
            if st.button("🌱 施肥", disabled=user_resources['fertilizer'] < 1):
                if electronic_crop['fertilizer_count'] < current_stage['fertilizer_need']:
                    update_user_resources(1, fertilizer=user_resources['fertilizer'] - 1)
                    update_electronic_crop(1, fertilizer_count=electronic_crop['fertilizer_count'] + 1)
                    st.success("施肥成功！")
                else:
                    st.warning("当前阶段不需要更多肥料了")
                st.rerun()
        
        # 检查是否可以升级到下一阶段
        if (electronic_crop['water_count'] >= current_stage['water_need'] and 
            electronic_crop['fertilizer_count'] >= current_stage['fertilizer_need'] and
            electronic_crop['growth_stage'] < 4):
            
            if st.button("⬆️ 升级到下一阶段", type="primary"):
                update_electronic_crop(1, growth_stage=next_stage, water_count=0, fertilizer_count=0)
                st.success(f"作物已升级到 {growth_stages[next_stage]['name']}！")
                st.balloons()
                st.rerun()
        
        # 收获作物（最终阶段）
        if electronic_crop['growth_stage'] == 4:
            if st.button("🎉 收获作物", type="primary"):
                # 根据作物类型给予奖励
                crop_rewards = {
                    "番茄": {"water": 5, "fertilizer": 3},
                    "水稻": {"water": 3, "fertilizer": 5},
                    "玉米": {"water": 4, "fertilizer": 4},
                    "小麦": {"water": 4, "fertilizer": 4},
                    "黄瓜": {"water": 6, "fertilizer": 2},
                    "草莓": {"water": 2, "fertilizer": 6}
                }
                
                reward = crop_rewards.get(electronic_crop['crop_type'], {"water": 5, "fertilizer": 5})
                new_water = user_resources['water'] + reward['water']
                new_fertilizer = user_resources['fertilizer'] + reward['fertilizer']
                
                update_user_resources(1, water=new_water, fertilizer=new_fertilizer)
                plant_electronic_crop(electronic_crop['crop_type'])  # 重新种植
                
                st.success(f"收获成功！获得 {reward['water']} 滴水滴和 {reward['fertilizer']} 份肥料！")
                st.balloons()
                st.rerun()
    
    st.markdown("---")
    
    # 显示打卡历史
    st.markdown('<div class="sub-header">打卡历史</div>', unsafe_allow_html=True)
    conn = sqlite3.connect('crop_health.db')
    checkin_history = pd.read_sql_query(
        "SELECT checkin_date, reward_type, reward_amount FROM checkin_history ORDER BY checkin_date DESC LIMIT 10", 
        conn
    )
    conn.close()
    
    if not checkin_history.empty:
        st.dataframe(checkin_history)
    else:
        st.markdown('<div class="info-box">暂无打卡记录</div>', unsafe_allow_html=True)

# 页脚
st.markdown("---")

# 添加联系我们按钮
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📧 联系我们", use_container_width=True):
        # 使用弹出式对话框显示联系信息
        with st.popover("📧 联系我们", use_container_width=True):
            st.markdown("""
            ### 作者信息
            
            **开发人员:** 吴东吉(AJower)、赵佳凝、宋信函、周昶、史展旭
            
            **联系方式:**
            - 📧 邮箱: AJower@163.com
            - 📞 QQ: 3175268324
                        
            **下载方式:**
            - 🌐 开源仓库: https://gitee.com/ajower/cmsp1.1
            - 🌐 百度网盘:  https://pan.baidu.com/s/11PHZnSJapvZggF9cKqK72Q?pwd=42tq
            
            **技术支持:**
            - 如果您有任何问题或建议，请通过以上方式联系我们
            - 我们提供7×24小时技术支持服务
            
            **开发支持:**
            - Python、SQLite、Steamlit、硅基流动、和风天气等
            
            

            """)

st.markdown('<div style="text-align: center; color: #6c757d; padding: 1.5rem;">农作物健康管理系统 V1.2.1 © 2025</div>', unsafe_allow_html=True)