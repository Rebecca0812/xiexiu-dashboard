
import supabase
from config import SUPABASE_URL, SUPABASE_KEY
from datetime import datetime

_client = None


def get_client():
    global _client
    if _client is None:
        _client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ==================== 备忘录 ====================

def insert_memo(content, tag="灵感"):
    client = get_client()
    result = client.table("memos").insert({"content": content, "tag": tag}).execute()
    return result.data[0] if result.data else {}


def list_memos(tag=None):
    client = get_client()
    query = client.table("memos").select("*")
    if tag and tag != "全部":
        query = query.eq("tag", tag)
    result = query.order("created_at", desc=True).execute()
    return result.data


def update_memo(memo_id, content=None, tag=None):
    client = get_client()
    data = {}
    if content is not None:
        data["content"] = content
    if tag is not None:
        data["tag"] = tag
    if data:
        data["updated_at"] = datetime.now().isoformat()
        client.table("memos").update(data).eq("id", memo_id).execute()


def delete_memo(memo_id):
    client = get_client()
    client.table("memos").delete().eq("id", memo_id).execute()


# ==================== 热点话题 ====================

def insert_hot_topic(title, hot_value="", source="douyin"):
    client = get_client()
    client.table("hot_topics").insert({
        "title": title,
        "hot_value": str(hot_value),
        "source": source,
        "fetched_at": datetime.now().isoformat()
    }).execute()


def list_hot_topics(limit=20):
    client = get_client()
    result = client.table("hot_topics").select("*").order("fetched_at", desc=True).limit(limit).execute()
    return result.data

