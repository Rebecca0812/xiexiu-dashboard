
"""
数据库层 —— Supabase (PostgreSQL) 封装
免费版：500MB存储，足够个人使用
"""

import supabase
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime, date

_client = None


def get_client():
    """获取Supabase客户端（单例）"""
    global _client
    if _client is None:
        _client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ==================== 热点视频 ====================

def insert_hot_video(data: dict):
    """插入一条热点视频"""
    client = get_client()
    client.table("hot_videos").insert(data).execute()


def get_today_videos(category: str = None) -> list[dict]:
    """获取今日热点视频"""
    client = get_client()
    today = date.today().isoformat()
    query = client.table("hot_videos").select("*").eq("fetch_date", today)
    if category:
        query = query.eq("category", category)
    result = query.order("like_count", desc=True).execute()
    return result.data


def get_videos_by_date(fetch_date: str, category: str = None) -> list[dict]:
    """获取指定日期的热点视频"""
    client = get_client()
    query = client.table("hot_videos").select("*").eq("fetch_date", fetch_date)
    if category:
        query = query.eq("category", category)
    result = query.order("like_count", desc=True).execute()
    return result.data


def cleanup_old_videos(days: int = 30) -> int:
    """清理过期数据"""
    from datetime import timedelta
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    client = get_client()
    result = client.table("hot_videos").lt("fetch_date", cutoff).delete().execute()
    return len(result.data) if result.data else 0


# ==================== 二创记录 ====================

def insert_recreation(data: dict) -> dict:
    """插入二创记录"""
    client = get_client()
    result = client.table("re_creations").insert(data).execute()
    return result.data[0] if result.data else {}


def get_recreation(rc_id: int) -> dict:
    """获取单条二创详情"""
    client = get_client()
    result = client.table("re_creations").select("*").eq("id", rc_id).execute()
    return result.data[0] if result.data else {}


def list_recreations(limit: int = 50) -> list[dict]:
    """获取二创列表"""
    client = get_client()
    result = client.table("re_creations").select("*").order("created_at", desc=True).limit(limit).execute()
    return result.data


def update_recreation_status(rc_id: int, status: str):
    """更新状态"""
    client = get_client()
    client.table("re_creations").update({"status": status}).eq("id", rc_id).execute()


# ==================== 发布复盘 ====================

def insert_review(data: dict) -> dict:
    """插入复盘记录"""
    client = get_client()
    result = client.table("published_reviews").insert(data).execute()
    return result.data[0] if result.data else {}


def list_reviews(limit: int = 100) -> list[dict]:
    """获取复盘列表"""
    client = get_client()
    result = client.table("published_reviews").select("*").order("publish_date", desc=True).limit(limit).execute()
    return result.data


# ==================== 备忘录 ====================

def insert_memo(content: str, tag: str = "灵感") -> dict:
    """创建备忘录"""
    client = get_client()
    result = client.table("memos").insert({"content": content, "tag": tag}).execute()
    return result.data[0] if result.data else {}


def list_memos(tag: str = None, archived: bool = False) -> list[dict]:
    """获取备忘录列表"""
    client = get_client()
    query = client.table("memos").select("*").eq("is_archived", archived)
    if tag and tag != "全部":
        query = query.eq("tag", tag)
    result = query.order("created_at", desc=True).execute()
    return result.data


def update_memo(memo_id: int, content: str = None, tag: str = None, is_archived: bool = None):
    """更新备忘录"""
    client = get_client()
    data = {}
    if content is not None:
        data["content"] = content
    if tag is not None:
        data["tag"] = tag
    if is_archived is not None:
        data["is_archived"] = is_archived
    if data:
        data["updated_at"] = datetime.now().isoformat()
        client.table("memos").update(data).eq("id", memo_id).execute()


def delete_memo(memo_id: int):
    """归档备忘录"""
    update_memo(memo_id, is_archived=True)
