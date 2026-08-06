import pandas as pd
import streamlit as st


def parse_douyin_csv(uploaded_file):
    """解析抖音创作者中心导出的CSV数据"""
    try:
        # 尝试多种编码
        for encoding in ["utf-8", "utf-8-sig", "gbk", "gb2312"]:
            try:
                df = pd.read_csv(uploaded_file, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            return None
        
        # 字段模糊匹配
        field_map = {}
        columns_lower = {col.lower().strip(): col for col in df.columns}
        
        mappings = {
            "title": ["作品标题", "标题", "视频标题", "title", "作品名称"],
            "play_count": ["播放量", "播放", "play", "views", "观看量"],
            "like_count": ["点赞量", "点赞", "like", "likes", "赞"],
            "comment_count": ["评论量", "评论", "comment", "comments"],
            "share_count": ["分享量", "分享", "share", "shares", "转发"],
            "collect_count": ["收藏量", "收藏", "collect", "favorites"],
            "publish_time": ["发布时间", "发布日期", "publish_time", "date", "时间"],
        }
        
        for target, candidates in mappings.items():
            for cand in candidates:
                cand_lower = cand.lower()
                for col_lower, col_orig in columns_lower.items():
                    if cand_lower in col_lower:
                        field_map[target] = col_orig
                        break
                if target in field_map:
                    break
        
        # 重命名列
        df_clean = pd.DataFrame()
        for target, source_col in field_map.items():
            df_clean[target] = df[source_col]
        
        # 确保必要列存在
        required = ["title", "play_count", "like_count"]
        for req in required:
            if req not in df_clean.columns:
                df_clean[req] = 0
        
        # 填充缺失列
        for col in ["comment_count", "share_count", "collect_count", "publish_time"]:
            if col not in df_clean.columns:
                df_clean[col] = 0
        
        # 数值转换
        for col in ["play_count", "like_count", "comment_count", "share_count", "collect_count"]:
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce").fillna(0).astype(int)
        
        return df_clean
        
    except Exception as e:
        st.error(f"CSV解析错误: {e}")
        return None
