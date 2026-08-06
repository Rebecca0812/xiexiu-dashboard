"""GitHub Actions定时抓取脚本 - 每日9点自动抓取热点"""
import os
import sys
from datetime import datetime

# 配置（GitHub Actions用环境变量）
config = {
    "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY", ""),
    "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
    "SUPABASE_KEY": os.environ.get("SUPABASE_KEY", ""),
    "TIKHUB_API_KEY": os.environ.get("TIKHUB_API_KEY", ""),
}


def main():
    print(f"=== 开始抓取 {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    
    # 检查配置
    if not config["TIKHUB_API_KEY"]:
        print("⚠️ TikHub API Key未配置，跳过抓取")
        print("提示：在GitHub仓库Settings → Secrets → Actions中配置TIKHUB_API_KEY")
        return
    
    # 延迟导入（避免GitHub Actions缺包报错）
    try:
        from api_service import fetch_douyin_hot
        from db import Database
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return
    
    db = Database(config)
    if not db.client:
        print("❌ 数据库连接失败")
        return
    
    # 抓取抖音热榜
    print("正在抓取抖音热榜...")
    result = fetch_douyin_hot(config)
    
    if result["success"]:
        items = result["data"]
        print(f"✅ 抓取成功，共 {len(items)} 条")
        
        saved = 0
        for item in items[:15]:
            save_result = db.save_hot_topic({
                "word": item.get("word", ""),
                "hot_value": str(item.get("hot_value", "")),
                "source": "douyin"
            })
            if save_result["success"]:
                saved += 1
        
        print(f"✅ 保存到数据库 {saved} 条")
    else:
        print(f"❌ 抓取失败: {result['error']}")
    
    print("=== 抓取完成 ===")


if __name__ == "__main__":
    main()
