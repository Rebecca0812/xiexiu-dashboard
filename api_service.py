
import httpx
import json
from config import (
    TIKHUB_API_KEY, TIKHUB_BASE_URL,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    PERSONA, CONTENT_DNA
)


def _tikhub_headers():
    return {"Authorization": f"Bearer {TIKHUB_API_KEY}"}


def fetch_douyin_hot(top_n=20):
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{TIKHUB_BASE_URL}/douyin/web/hot_list/",
                headers=_tikhub_headers()
            )
            resp.raise_for_status()
            data = resp.json()
        items = data.get("data", {}).get("word_list", [])
        return [{"title": i.get("word", ""), "hot_value": i.get("hot_value", "")} for i in items[:top_n]]
    except Exception as e:
        print(f"抖音热榜失败: {e}")
        return []


def search_xiaohongshu(keyword, per_page=10):
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{TIKHUB_BASE_URL}/xiaohongshu/web/search_notes/",
                headers=_tikhub_headers(),
                params={"keyword": keyword, "sort": "popularity_descending"}
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
        items = data.get("data", {}).get("items", [])
        results = []
        for item in items[:per_page]:
            note = item.get("note_card", item)
            results.append({
                "title": note.get("display_title", ""),
                "author": note.get("user", {}).get("nickname", ""),
                "like_count": _parse_count(note.get("interact_info", {}).get("liked_count", "0")),
            })
        return results
    except Exception as e:
        print(f"小红书搜索失败: {e}")
        return []


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
    except Exception:
        return {"error": "解析失败", "raw": result}


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


