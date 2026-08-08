
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import TIKHUB_API_KEY, SUPABASE_URL, SUPABASE_KEY
import api_service
import db


def main():
    print(f"=== 开始抓取 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")

    if not TIKHUB_API_KEY:
        print("TikHub API Key未配置，跳过")
        return

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Supabase未配置，跳过")
        return

    print("抓取抖音热榜...")
    items = api_service.fetch_douyin_hot(15)

    if items:
        print(f"抓取成功，共 {len(items)} 条")
        saved = 0
        for item in items:
            try:
                db.insert_hot_topic(item["title"], item.get("hot_value", ""))
                saved += 1
            except Exception as e:
                print(f"保存失败: {e}")
        print(f"保存到数据库 {saved} 条")
    else:
        print("抓取失败")

    print("=== 完成 ===")


if __name__ == "__main__":
    main()

