"""
API服务层 —— TikHub + DeepSeek 封装
"""

import httpx
import json
from config import (
    TIKHUB_API_KEY, TIKHUB_BASE_URL,
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    PERSONA, CONTENT_DNA
)


# ==================== TikHub ====================

def _tikhub_headers():
    return {"Authorization": f"Bearer {TIKHUB_API_KEY}"}


def fetch_douyin_hot(top_n: int = 50) -> list[dict]:
    """获取抖音热榜"""
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(
                f"{TIKHUB_BASE_URL}/douyin/web/hot_list/",
                headers=_tikhub_headers()
            )
            resp.raise_for_status()
            data = resp.json()

        videos = []
        items = data.get("data", {}).get("word_list", [])
        for item in items[:top_n]:
            videos.append({
                "source_platform": "douyin",
                "video_id": str(item.get("sentence_id", item.get("word_id", ""))),
                "title": item.get("word", ""),
                "author": "",
                "description": item.get("sentence_title", ""),
                "play_count": item.get("hot_value", 0),
                "like_count": 0,
                "comment_count": 0,
                "share_count": 0,
                "cover_url": item.get("cover_image_url", ""),
                "video_url": item.get("video_url", ""),
                "tags": "",
            })
        return videos
    except Exception as e:
        print(f"[TikHub] 抖音热榜失败: {e}")
        return []


def search_xiaohongshu(keywords: list[str], per_keyword: int = 10) -> list[dict]:
    """搜索小红书笔记"""
    all_results = []
    try:
        with httpx.Client(timeout=30) as client:
            for kw in keywords:
                try:
                    resp = client.get(
                        f"{TIKHUB_BASE_URL}/xiaohongshu/web/search_notes/",
                        headers=_tikhub_headers(),
                        params={"keyword": kw, "sort": "popularity_descending"}
                    )
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                    items = data.get("data", {}).get("items", [])
                    for item in items[:per_keyword]:
                        note = item.get("note_card", item)
                        user = note.get("user", {})
                        interact = note.get("interact_info", {})
                        all_results.append({
                            "source_platform": "xiaohongshu",
                            "video_id": str(note.get("note_id", item.get("id", ""))),
                            "title": note.get("display_title", ""),
                            "author": user.get("nickname", ""),
                            "description": note.get("desc", ""),
                            "play_count": 0,
                            "like_count": _parse_count(interact.get("liked_count", "0")),
                            "comment_count": _parse_count(interact.get("comment_count", "0")),
                            "share_count": _parse_count(interact.get("share_count", "0")),
                            "cover_url": note.get("cover", {}).get("url", ""),
                            "video_url": f"https://www.xiaohongshu.com/explore/{note.get('note_id', '')}",
                            "tags": kw,
                        })
                except Exception:
                    continue
        return all_results
    except Exception as e:
        print(f"[TikHub] 小红书搜索失败: {e}")
        return []


def get_video_detail(video_url: str, platform: str = "douyin") -> dict:
    """获取视频详情"""
    try:
        with httpx.Client(timeout=30) as client:
            if platform == "douyin":
                resp = client.get(
                    f"{TIKHUB_BASE_URL}/douyin/web/video_info/",
                    headers=_tikhub_headers(),
                    params={"url": video_url}
                )
            else:
                resp = client.get(
                    f"{TIKHUB_BASE_URL}/xiaohongshu/web/note_detail/",
                    headers=_tikhub_headers(),
                    params={"url": video_url}
                )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            if platform == "douyin":
                return {
                    "title": data.get("desc", ""),
                    "desc": data.get("desc", ""),
                    "tags": ",".join([t.get("hashtag_name", "") for t in data.get("text_extra", []) if t.get("type") == 1]),
                    "author": data.get("author", {}).get("nickname", ""),
                    "like_count": data.get("statistics", {}).get("digg_count", 0),
                    "comment_count": data.get("statistics", {}).get("comment_count", 0),
                    "share_count": data.get("statistics", {}).get("share_count", 0),
                    "play_count": data.get("statistics", {}).get("play_count", 0),
                }
            else:
                return {
                    "title": data.get("title", ""),
                    "desc": data.get("desc", ""),
                    "tags": ",".join(data.get("tag_list", [])),
                    "author": data.get("user", {}).get("nickname", ""),
                    "like_count": data.get("interact_info", {}).get("liked_count", 0),
                    "comment_count": data.get("interact_info", {}).get("comment_count", 0),
                    "share_count": data.get("interact_info", {}).get("share_count", 0),
                    "play_count": 0,
                }
    except Exception as e:
        print(f"[TikHub] 视频详情失败: {e}")
        return {}


def _parse_count(s) -> int:
    if isinstance(s, int):
        return s
    if not s:
        return 0
    s = str(s).strip()
    try:
        if "万" in s:
            return int(float(s.replace("万", "")) * 10000)
        if "亿" in s:
            return int(float(s.replace("亿", "")) * 100000000)
        return int(s)
    except (ValueError, TypeError):
        return 0


# ==================== DeepSeek ====================

def _deepseek_headers():
    return {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}


def _chat(messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
    with httpx.Client(timeout=120) as client:
        resp = client.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers=_deepseek_headers(),
            json={
                "model": DEEPSEEK_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"}
            }
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def classify_video(title: str, desc: str) -> dict:
    """分类视频：本赛道/泛赛道"""
    prompt = f"""将以下视频分类为"本赛道"或"泛赛道"。
本赛道：颂钵平替、ASMR助眠、省钱疗愈、白噪音、音疗、助眠好物
泛赛道：中年失眠、打工人焦虑、房贷压力、裁员、睡不着、情绪共鸣

标题：{title}
描述：{desc}

返回JSON：{{"category": "本赛道"或"泛赛道", "reason": "一句话理由"}}"""
    return json.loads(_chat([{"role": "user", "content": prompt}], temperature=0.1, max_tokens=200))


def generate_recreation(video_info: dict) -> dict:
    """生成二创素材包"""
    prompt = f"""你是"抠搜邪修音疗"账号的脚本撰写人，你就是账号主角本人。

【你的人设】
{PERSONA}

【内容DNA】
{CONTENT_DNA}

【人设红线】
- 不说教，只记录自己的自救过程
- 不假装专业，保持外行摸索感
- 不卖惨，底色是自嘲和乐观
- 不偏离省钱，任何道具必须有价格锚点

对以下爆款视频进行二创：

【爆款视频】
标题：{video_info.get('title', '')}
描述：{video_info.get('desc', '')}
标签：{video_info.get('tags', '')}
互动：点赞{video_info.get('like_count', 0)}，评论{video_info.get('comment_count', 0)}

返回JSON：
{{
  "title": "二创标题（15字内，数字+反差感）",
  "script": "口播脚本（30-60秒，开头3秒价格反差钩子，融入中年牛马生活，口语化，结尾互动引导）",
  "storyboard": "分镜表markdown表格，6-9镜头，列：镜头|画面|时长|声音|拍摄备注",
  "xhs_note": "小红书笔记（标题+正文200-300字带emoji+10标签+封面建议）",
  "shooting_list": "拍摄清单（道具注明来源+价格，场景要求，预计时长）",
  "hooks": [
    {{"type": "悬念型", "content": "前3秒画面+口播", "action": "动作"}},
    {{"type": "情感共鸣型", "content": "前3秒画面+口播", "action": "动作"}},
    {{"type": "反常识型", "content": "前3秒画面+口播", "action": "动作"}}
  ]
}}"""
    return json.loads(_chat([{"role": "user", "content": prompt}], temperature=0.8, max_tokens=4096))


def check_persona(script: str) -> dict:
    """人设一致性检查"""
    prompt = f"""检查脚本是否符合人设。

【人设】{PERSONA}

【检查维度（1-5分）】
1.不说教 2.省钱度 3.真实感 4.外行感 5.共鸣点 6.乐观度

【脚本】{script}

返回JSON：{{"pass": true/false, "scores": {{"不说教": x, "省钱度": x, "真实感": x, "外行感": x, "共鸣点": x, "乐观度": x}}, "suggestions": "建议或通过"}}"""
    return json.loads(_chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=500))


def analyze_review(review_data: list[dict]) -> dict:
    """分析发布数据"""
    data_text = ""
    for i, v in enumerate(review_data, 1):
        data_text += f"\n视频{i}：{v.get('title', '无标题')}\n  播放:{v.get('play_count',0)} 点赞:{v.get('like_count',0)} 评论:{v.get('comment_count',0)} 完播率:{v.get('completion_rate',0)}% 涨粉:{v.get('follower_growth',0)}\n"

    prompt = f"""你是自媒体数据分析专家。分析以下抖音发布数据。

账号人设：{PERSONA}

【数据】{data_text}

返回JSON：
{{
  "per_video": [{{"title": "标题", "performance": "好/一般/差", "highlight": "亮点", "issue": "问题"}}],
  "trend": "趋势分析",
  "comparison": "对比分析",
  "suggestions": ["建议1", "建议2", "建议3"]
}}"""
    return json.loads(_chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=2048))


