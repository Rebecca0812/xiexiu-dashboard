from supabase import create_client, Client
from datetime import datetime


class Database:
    def __init__(self, config):
        self.url = config.get("SUPABASE_URL", "")
        self.key = config.get("SUPABASE_KEY", "")
        self.client = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
            except Exception as e:
                print(f"数据库连接失败: {e}")
    
    def add_memo(self, content, tag="其他"):
        """添加备忘录"""
        if not self.client:
            return {"success": False, "error": "数据库未连接"}
        try:
            data = {
                "content": content,
                "tag": tag,
                "created_at": datetime.now().isoformat()
            }
            result = self.client.table("memos").insert(data).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_memos(self, tag=None):
        """获取备忘录列表"""
        if not self.client:
            return []
        try:
            query = self.client.table("memos").select("*").order("created_at", desc=True)
            if tag:
                query = query.eq("tag", tag)
            result = query.execute()
            return result.data
        except Exception as e:
            print(f"获取备忘录失败: {e}")
            return []
    
    def delete_memo(self, memo_id):
        """删除备忘录"""
        if not self.client:
            return {"success": False, "error": "数据库未连接"}
        try:
            self.client.table("memos").delete().eq("id", memo_id).execute()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_hot_topic(self, topic_data):
        """保存热点话题"""
        if not self.client:
            return {"success": False, "error": "数据库未连接"}
        try:
            data = {
                "title": topic_data.get("word", ""),
                "hot_value": topic_data.get("hot_value", ""),
                "source": topic_data.get("source", "douyin"),
                "fetched_at": datetime.now().isoformat()
            }
            self.client.table("hot_topics").insert(data).execute()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_hot_topics(self, limit=20):
        """获取热点话题"""
        if not self.client:
            return []
        try:
            result = (
                self.client.table("hot_topics")
                .select("*")
                .order("fetched_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data
        except Exception as e:
            print(f"获取热点失败: {e}")
            return []
