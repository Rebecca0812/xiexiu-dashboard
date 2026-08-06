import os
import streamlit as st

# 人设档案
PERSONA = {
    "track": "抠搜邪修音疗",
    "persona": "36岁汽车大厂预算牛马，房贷车贷压力大，失眠，用便宜好物平替音疗治愈自己",
    "age": "36",
    "job": "汽车大厂项目预算",
    "pain_points": ["失眠", "经济压力", "中年焦虑", "裁员风险"],
    "solution": "用平价好物替代昂贵音疗工具，自愈又省钱",
    "tone": "幽默自嘲 + 真实治愈 + 抠搜实用",
    "keywords": ["平替", "音疗", "ASMR", "助眠", "解压", "便宜好物", "颂钵平替"]
}


def get_config():
    """获取配置，优先从Streamlit Secrets读取"""
    config = {
        "DEEPSEEK_API_KEY": "",
        "SUPABASE_URL": "",
        "SUPABASE_KEY": "",
        "TIKHUB_API_KEY": ""
    }
    
    # 优先从Streamlit Secrets读取
    try:
        secrets = st.secrets
        config["DEEPSEEK_API_KEY"] = secrets.get("DEEPSEEK_API_KEY", "")
        config["SUPABASE_URL"] = secrets.get("SUPABASE_URL", "")
        config["SUPABASE_KEY"] = secrets.get("SUPABASE_KEY", "")
        config["TIKHUB_API_KEY"] = secrets.get("TIKHUB_API_KEY", "")
    except Exception:
        pass
    
    # 兜底：从环境变量读取（GitHub Actions用）
    config["DEEPSEEK_API_KEY"] = config["DEEPSEEK_API_KEY"] or os.environ.get("DEEPSEEK_API_KEY", "")
    config["SUPABASE_URL"] = config["SUPABASE_URL"] or os.environ.get("SUPABASE_URL", "")
    config["SUPABASE_KEY"] = config["SUPABASE_KEY"] or os.environ.get("SUPABASE_KEY", "")
    config["TIKHUB_API_KEY"] = config["TIKHUB_API_KEY"] or os.environ.get("TIKHUB_API_KEY", "")
    
    return config
