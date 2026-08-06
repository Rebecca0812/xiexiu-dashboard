import httpx
import json

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TIKHUB_DOUYIN_URL = "https://api.tikhub.io/api/v1/douyin/web/fetch_hot_search_list"
TIKHUB_XHS_URL = "https://api.tikhub.io/api/v1/xiaohongshu/web/search_notes"


def fetch_douyin_hot(config):
    """抓取抖音热榜"""
    api_key = config.get("TIKHUB_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "TikHub API Key未配置，先用手动模式"}
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        with httpx.Client(timeout=15) as client:
            resp = client.get(TIKHUB_DOUYIN_URL, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", {}).get("word_list", [])
            return {"success": True, "data": items[:20]}
    except Exception as e:
        return {"success": False, "error": f"抓取失败: {e}"}


def search_xiaohongshu(config, keyword):
    """搜索小红书笔记"""
    api_key = config.get("TIKHUB_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "TikHub API Key未配置，先用手动模式"}
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        params = {"keyword": keyword, "sort": "general", "page": 1}
        with httpx.Client(timeout=15) as client:
            resp = client.get(TIKHUB_XHS_URL, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", {}).get("items", [])
            return {"success": True, "data": items[:15]}
    except Exception as e:
        return {"success": False, "error": f"搜索失败: {e}"}


def _call_deepseek(config, messages):
    """调用DeepSeek API"""
    api_key = config.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "DeepSeek API Key未配置"}
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 2000
        }
        with httpx.Client(timeout=60) as client:
            resp = client.post(DEEPSEEK_URL, headers=headers, json=payload)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return {"success": True, "data": content}
    except Exception as e:
        return {"success": False, "error": f"AI调用失败: {e}"}


def classify_video(config, item):
    """AI分析热点视频"""
    title = item.get("word", "")
    hot = item.get("hot_value", "")
    messages = [
        {"role": "system", "content": "你是自媒体选题分析师，帮助分析热点话题与音疗赛道的结合点。"},
        {"role": "user", "content": f"热点话题：{title}（热度：{hot}）\n我的人设是：36岁汽车大厂预算牛马，做'抠搜邪修音疗'赛道，用平价好物平替昂贵音疗工具。\n请分析：1）这个热点能不能蹭？2）怎么结合我的赛道？3）给1个具体选题方向。简洁回答。"}
    ]
    return _call_deepseek(config, messages)
def generate_recreation(config, video_url, video_text, style, duration):
    """AI生成二创脚本"""
    source = video_url if video_url else video_text
    messages = [
        {"role": "system", "content": "你是爆款短视频编剧，擅长把热点内容改编成符合特定人设的脚本。"},
        {"role": "user", "content": f"""请基于以下内容生成一个二创脚本：

【原始内容】{source}

【要求】
- 风格：{style}
- 时长：{duration}
- 人设：36岁汽车大厂预算牛马，房贷车贷压力大，失眠，用平价好物平替音疗治愈自己（抠搜邪修音疗赛道）
- 开头3秒必须有强钩子
- 口语化，真实接地气
- 结尾引导互动

请输出完整脚本，包含：开头钩子、正文、结尾互动。""")}
    ]
    return _call_deepseek(config, messages)


def check_persona(config, script):
    """人设一致性检查（6维度评分）"""
    dimensions = ["幽默自嘲", "真实感", "抠搜实用", "治愈属性", "痛点共鸣", "音疗相关"]
    messages = [
        {"role": "system", "content": "你是人设一致性评估专家，请对脚本进行6维度评分。"},
        {"role": "user", "content": f"""请对以下脚本进行人设一致性评分：

【脚本】{script}

【人设】36岁汽车大厂预算牛马，抠搜邪修音疗赛道，幽默自嘲+真实治愈+抠搜实用

【评分维度】{", ".join(dimensions)}
每个维度打1-10分，只返回JSON格式：
{{"幽默自嘲": 8, "真实感": 7, "抠搜实用": 9, "治愈属性": 8, "痛点共鸣": 7, "音疗相关": 9}}"""}
    ]
    result = _call_deepseek(config, messages)
    if result["success"]:
        try:
            text = result["data"].strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            scores = json.loads(text)
            return {"success": True, "data": scores}
        except Exception:
            return {"success": True, "data": {"总评": 7}}
    return result


def analyze_review(config, df):
    """AI复盘分析"""
    try:
        summary = df.describe().to_string()
        top_videos = df.nlargest(3, "play_count")[["title", "play_count", "like_count"]].to_string()
        messages = [
            {"role": "system", "content": "你是自媒体数据分析师，帮助复盘视频表现并给出优化建议。"},
            {"role": "user", "content": f"""请分析我的抖音数据：

【整体数据】{summary}

【TOP3视频】{top_videos}

【我的人设】36岁汽车大厂预算牛马，抠搜邪修音疗赛道

请给出：
1. 整体表现评价
2. 哪些内容表现好，为什么
3. 哪些内容表现差，为什么
4. 3条优化建议
5. 下一步选题方向建议

简洁实用地回答。"""}
        ]
        return _call_deepseek(config, messages)
    except Exception as e:
        return {"success": False, "error": f"分析失败: {e}"}
