
"""
CSV解析器 —— 抖音创作者中心导出CSV
"""

import io
import csv
import re
from datetime import datetime, date

FIELD_RULES = {
    "title": ["标题", "作品标题", "视频标题", "title"],
    "publish_date": ["发布时间", "发布日期", "publish", "date", "创建时间"],
    "play_count": ["播放量", "播放", "play", "view", "观看"],
    "like_count": ["点赞", "like", "digg"],
    "comment_count": ["评论", "comment"],
    "share_count": ["分享", "share", "转发"],
    "follower_growth": ["涨粉", "新增粉丝", "粉丝增长", "follower"],
    "avg_watch_time": ["平均观看", "观看时长", "watch_time", "play_duration"],
    "completion_rate": ["完播率", "播放完成率", "completion"],
}


def parse_douyin_csv(content: bytes) -> list[dict]:
    """解析抖音CSV，返回结构化数据列表"""
    text = None
    for enc in ["utf-8-sig", "utf-8", "gbk", "gb2312"]:
        try:
            text = content.decode(enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if text is None:
        raise ValueError("无法解码CSV，请确认文件编码")

    text = text.lstrip('\ufeff')
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise ValueError("CSV为空或格式不正确")

    cols = list(rows[0].keys())
    field_map = _build_map(cols)

    results = []
    for row in rows:
        parsed = {}
        for std, csv_col in field_map.items():
            if csv_col and csv_col in row:
                parsed[std] = _convert(std, row[csv_col].strip())
            else:
                parsed[std] = _default(std)
        if parsed.get("title") or parsed.get("play_count"):
            results.append(parsed)
    return results


def _build_map(cols):
    fmap = {s: None for s in FIELD_RULES}
    for std, patterns in FIELD_RULES.items():
        for col in cols:
            for p in patterns:
                if p.lower() in col.strip().lower():
                    fmap[std] = col
                    break
            if fmap[std]:
                break
    return fmap


def _convert(field, raw):
    if not raw or raw == "-":
        return _default(field)
    if field in ["play_count", "like_count", "comment_count", "share_count", "follower_growth"]:
        return _parse_int(raw)
    elif field == "avg_watch_time":
        return _parse_float(raw)
    elif field == "completion_rate":
        return _parse_rate(raw)
    elif field == "publish_date":
        return _parse_date(raw)
    return raw


def _parse_int(s):
    s = s.strip().replace(",", "")
    try:
        if "万" in s: return int(float(s.replace("万", "")) * 10000)
        if "亿" in s: return int(float(s.replace("亿", "")) * 100000000)
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def _parse_float(s):
    try:
        return float(s.strip().replace(",", "").replace("秒", ""))
    except (ValueError, TypeError):
        return 0.0


def _parse_rate(s):
    s = s.strip().replace("%", "").replace(",", "")
    try:
        v = float(s)
        return v if v > 1 else v * 100
    except (ValueError, TypeError):
        return 0.0


def _parse_date(s):
    s = s.strip()
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"]:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    m = re.match(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return date.today().isoformat()


def _default(field):
    if field in ["play_count", "like_count", "comment_count", "share_count", "follower_growth"]:
        return 0
    elif field in ["avg_watch_time", "completion_rate"]:
        return 0.0
    elif field == "publish_date":
        return date.today().isoformat()
    return ""
