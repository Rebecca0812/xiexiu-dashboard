
import httpx
import json
import re
from config import (
    TIKHUB_API_KEY, TIKHUB_BASE_URL,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    PERSONA, CONTENT_DNA
)


def _tikhub_headers():
    return {"Authorization": f"Bearer {TIKHUB_API_KEY}"}


# ==================== 平台识别 ====================

def detect_platform(url):
    """识别链接是抖音还是小红书"""
    url = url.lower()
    if "douyin" in url or "iesdouyin" in url:
        return "douyin"
    if "xiaohongshu" in url or "xhslink" in url or "rednote" in url:
        return "xiaohongshu"
    return None


# ==================== 抖音热榜 ====================

def fetch_douyin_hot(top_n=20):
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{TIKHUB_BASE_URL}/douyin/web/fetch_hot_search_list",
                headers=_tikhub_headers()
            )
            print(f"抖音热榜状态码: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            print(f"抖音热榜返回: {data.keys() if isinstance(data, dict) else type(data)}")
        items = data.get("data", {}).get("word_list", [])
        return [{"title": i.get("word", ""), "hot_value": i.get("hot_value", "")} for i in items[:top_n]]
    except Exception as e:
        print(f"抖音热榜失败: {e}")
        return []


# ==================== 小红书搜索 ====================

def search_xiaohongshu(keyword, per_page=10):
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{TIKHUB_BASE_URL}/xiaohongshu/web/search_notes",
                headers=_tikhub_headers(),
                params={"keyword": keyword}
            )
            print(f"小红书搜索状态码: {resp.status_code}")
            if resp.status_code != 200:
                return []
            data = resp.json()
            print(f"小红书搜索返回: {data.keys() if isinstance(data, dict) else type(data)}")
        items = data.get("data", {}).get("items", [])
        results = []
        for item in items[:per_page]:
            note = item.get("note_card", item)
            interact = note.get("interact_info", {}) or {}
            results.append({
                "title": note.get("display_title", ""),
                "author": note.get("user", {}).get("nickname", ""),
                "like_count": _parse_count(interact.get("liked_count", "0")),
                "comment_count": _parse_count(interact.get("comment_count", "0")),
            })
        return results
    except Exception as e:
        print(f"小红书搜索失败: {e}")
        return []


# ==================== 链接解析（抖音/小红书）====================

def parse_video_link(url):
    """粘贴链接，自动解析视频/笔记详情"""
    platform = detect_platform(url)
    if not platform:
        return {"error": "链接无法识别，请粘贴抖音或小红书分享链接"}
    if not TIKHUB_API_KEY:
        return {"error": "TikHub API Key未配置"}

    try:
        with httpx.Client(timeout=30) as client:
            if platform == "douyin":
                resp = client.get(
                    f"{TIKHUB_BASE_URL}/douyin/web/fetch_one_video",
                    headers=_tikhub_headers(),
                    params={"url": url}
                )
            else:
                resp = client.get(
                    f"{TIKHUB_BASE_URL}/xiaohongshu/web/fetch_note_info",
                    headers=_tikhub_headers(),
                    params={"url": url}
                )
            print(f"链接解析状态码: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()
            print(f"链接解析返回结构: {data.keys() if isinstance(data, dict) else type(data)}")
            return _extract_video_info(platform, data)
    except Exception as e:
        print(f"链接解析失败: {e}")
        return {"error": f"解析失败: {e}"}


def _extract_video_info(platform, data):
    """从TikHub返回数据中提取需要的信息"""
    result = {"title": "", "desc": "", "tags": "", "like_count": 0, "comment_count": 0}
    try:
        if platform == "douyin":
            video = data.get("data", {})
            author = video.get("author", {}).get("nickname", "")
            result["title"] = video.get("desc", "")[:100]
            result["desc"] = video.get("desc", "")
            result["tags"] = ",".join([t.get("hashtag_name", "") for t in video.get("text_extra", []) if t.get("type") == 1])
            stats = video.get("statistics", {})
            result["like_count"] = stats.get("digg_count", 0)
            result["comment_count"] = stats.get("comment_count", 0)
            result["share_count"] = stats.get("share_count", 0)
            result["play_count"] = stats.get("play_count", 0)
            result["author"] = author
        else:
            note = data.get("data", {})
            result["title"] = note.get("title", "")[:100]
            result["desc"] = note.get("desc", "")
            result["tags"] = ",".join(note.get("tag_list", []))
            interact = note.get("interact_info", {}) or {}
            result["like_count"] = _parse_count(interact.get("liked_count", "0"))
            result["comment_count"] = _parse_count(interact.get("comment_count", "0"))
            result["share_count"] = _parse_count(interact.get("share_count", "0"))
            result["author"] = note.get("user", {}).get("nickname", "")
    except Exception as e:
        print(f"提取信息失败: {e}")
    return result


def _parse_count(s):
    if isinstance(s, int):
        return s
    if not s:
        return 0
    s = str(s).strip()
    try:
        if "万" in s:
            return int(float(s.replace("万", "")) * 10000)
        return int(s)
    except (ValueError, TypeError):
        return 0


# ==================== DeepSeek ====================

def _chat(messages, temperature=0.7, max_tokens=4096):
    with httpx.Client(timeout=120) as client:
        resp = client.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def generate_recreation(video_title, video_desc="", style="幽默自嘲", duration="30秒"):
    prompt = f"""你是"抠搜邪修音疗"账号的脚本撰写人。

【你的人设】
{PERSONA}

【内容DNA】
{CONTENT_DNA}

对以下内容进行二创：
标题：{video_title}
描述：{video_desc}
风格：{style}
时长：{duration}

请直接输出完整脚本，包含：
1. 标题（15字内，数字+反差感）
2. 开头3秒钩子（价格反差）
3. 口播脚本（口语化，融入中年牛马生活）
4. 分镜建议（6-9个镜头）
5. 结尾互动引导
6. 拍摄道具清单（注明来源和价格）"""
    return _chat([{"role": "user", "content": prompt}], temperature=0.8, max_tokens=4096)


def check_persona(script):
    prompt = f"""检查脚本是否符合人设。

【人设】{PERSONA}

【检查维度（1-10分）】
1.幽默自嘲 2.省钱度 3.真实感 4.治愈属性 5.痛点共鸣 6.音疗相关

【脚本】{script}

返回JSON：
{{"幽默自嘲": x, "省钱度": x, "真实感": x, "治愈属性": x, "痛点共鸣": x, "音疗相关": x, "suggestions": "建议"}}"""
    try:
        result = _chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=500)
        text = result.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        return {"error": f"解析失败: {e}", "raw": result}


def analyze_review(data_text):
    prompt = f"""你是自媒体数据分析专家。分析以下抖音发布数据。

账号人设：{PERSONA}

【数据】
{data_text}

请给出：
1. 整体表现评价
2. 哪些内容表现好，为什么
3. 哪些内容表现差，为什么
4. 3条优化建议
5. 下一步选题方向建议

简洁实用地回答。"""
    return _chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=2048)
