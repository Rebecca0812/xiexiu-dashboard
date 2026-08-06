"""
定时抓取脚本 —— 供 GitHub Actions 调用
每天早9点自动执行，抓取热点数据写入Supabase
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from api_service import fetch_douyin_hot, search_xiaohongshu, classify_video
from db import insert_hot_video, cleanup_old_videos
from config import XHS_KEYWORDS_TRACK, XHS_KEYWORDS_BROAD
from datetime import date


def main():
    print(f"=== 每日热点抓取 {date.today()} ===")

    # 1. 抓取
    print("[1/4] 抓取抖音热榜...")
    dy = fetch_douyin_hot(top_n=30)
    print(f"  获取 {len(dy)} 条")

    print("[2/4] 搜索小红书...")
    xhs = search_xiaohongshu(XHS_KEYWORDS_TRACK + XHS_KEYWORDS_BROAD, per_keyword=5)
    print(f"  获取 {len(xhs)} 条")

    # 2. 去重
    all_videos = dy + xhs
    seen = set()
    unique = []
    for v in all_videos:
        vid = v.get("video_id", "")
        if vid and vid not in seen:
            seen.add(vid)
            unique.append(v)
    print(f"  去重后 {len(unique)} 条")

    # 3. 分类+入库
    print("[3/4] AI分类+入库...")
    success = 0
    for v in unique:
        try:
            cat = classify_video(v.get("title", ""), v.get("desc", ""))
            v["category"] = cat.get("category", "泛赛道")
            v["reason"] = cat.get("reason", "")
        except Exception as e:
            v["category"] = "泛赛道"
            v["reason"] = f"分类失败: {e}"

        v["fetch_date"] = date.today().isoformat()
        try:
            insert_hot_video(v)
            success += 1
        except Exception:
            continue  # 重复跳过

    print(f"  成功入库 {success} 条")

    # 4. 清理旧数据
    print("[4/4] 清理旧数据...")
    deleted = cleanup_old_videos(30)
    print(f"  清理 {deleted} 条")

    print(f"=== 完成！新增 {success} 条 ===")


if __name__ == "__main__":
    main()
