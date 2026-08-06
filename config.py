
"""
配置中心 —— API Key 和 人设档案
优先从Streamlit Secrets读取，如果没有则用默认值
"""

import os

# 尝试从Streamlit Secrets读取（部署后生效）
try:
    import streamlit as st
    _secrets = st.secrets
except Exception:
    _secrets = {}

# ==================== API Keys ====================
TIKHUB_API_KEY = _secrets.get("TIKHUB_API_KEY", os.getenv("TIKHUB_API_KEY", ""))
TIKHUB_BASE_URL = "https://api.tikhub.io/api/v1"

DEEPSEEK_API_KEY = _secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

SUPABASE_URL = _secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
SUPABASE_KEY = _secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))

# ==================== 人设档案 ====================
PERSONA = '''36岁，汽车大厂项目预算岗。房贷车贷都有，被裁员风险压着，晚上睡不着。
不想花大钱买颂钵，就用厨房里、五金店、宜家、零食铺的便宜东西做音疗平替。
语气：疲惫但幽默、自嘲、不说教、有外行感。
一句话定位：36岁汽车大厂预算岗牛马，唯一能让我睡着的，是厨房里这些碗。'''

CONTENT_DNA = '''价格反差钩子 + 奇葩物品做音疗 + 中年牛马真实生活 + 我没钱但我有办法
人设红线：不说教 / 不假装专业 / 不卖惨 / 不偏离省钱 / 不精致滤镜'''

# ==================== 小红书搜索关键词 ====================
XHS_KEYWORDS_TRACK = ["颂钵平替", "ASMR助眠", "省钱疗愈", "白噪音", "助眠好物"]
XHS_KEYWORDS_BROAD = ["中年失眠", "打工人焦虑", "房贷压力", "睡不着", "牛马日常"]

# ==================== 数据保留 ====================
DATA_RETENTION_DAYS = 30

