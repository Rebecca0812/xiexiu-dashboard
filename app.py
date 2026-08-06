"""
🎵 抠搜邪修音疗 · 自媒体运营工作台
单一Streamlit应用，部署到Streamlit Community Cloud（免费）
"""

import streamlit as st
import json
from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import PERSONA, CONTENT_DNA, XHS_KEYWORDS_TRACK, XHS_KEYWORDS_BROAD
from db import (
    get_today_videos, get_videos_by_date, insert_hot_video, cleanup_old_videos,
    insert_recreation, get_recreation, list_recreations, update_recreation_status,
    insert_review, list_reviews,
    insert_memo, list_memos, update_memo, delete_memo,
)
from api_service import (
    fetch_douyin_hot, search_xiaohongshu, get_video_detail,
    classify_video, generate_recreation, check_persona, analyze_review,
)
from csv_parser import parse_douyin_csv

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="邪修音疗工作台",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================== 全局样式 ====================
def inject_style():
    st.markdown("""
    <style>
    /* 主背景 */
    .stApp { background: #0f0f23; }

    /* 侧边栏 */
    section[data-testid="stSidebar"] {
        background: #16213e;
    }
    section[data-testid="stSidebar"] .stMarkdown h1 {
        color: #e94560;
        font-size: 18px;
    }

    /* 主内容区 */
    .main .block-container {
        padding-top: 1.5rem;
        max-width: 900px;
    }

    /* 标题 */
    h1 { color: #e94560 !important; font-size: 24px !important; }
    h2 { color: #f5a623 !important; font-size: 18px !important; }
    h3 { color: #e0e0e0 !important; font-size: 15px !important; }

    /* 卡片 */
    div[data-testid="stVerticalBlock"] > div {
        background: #16213e;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
    }

    /* 按钮 */
    .stButton > button {
        background: #e94560;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 13px;
        min-height: 40px;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #ff5577;
        transform: translateY(-1px);
    }

    /* 标签 */
    .tag-track {
        background: #e94560; color: white;
        padding: 2px 10px; border-radius: 10px;
        font-size: 11px; font-weight: 600;
    }
    .tag-broad {
        background: #0f3460; color: #a0d0ff;
        padding: 2px 10px; border-radius: 10px;
        font-size: 11px; font-weight: 600;
    }

    /* 表格 */
    .dataframe { font-size: 12px; }
    table { border-radius: 8px; overflow: hidden; }
    th { background: #0f3460 !important; color: #e0e0e0 !important; }

    /* 手机适配 */
    @media (max-width: 768px) {
        .main .block-container { padding: 1rem 0.5rem; max-width: 100%; }
        h1 { font-size: 20px !important; }
        h2 { font-size: 16px !important; }
        .stButton > button { min-height: 44px; font-size: 14px; }
    }

    /* Tab */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        background: #16213e; border-radius: 8px 8px 0 0;
        padding: 8px 16px; font-size: 13px;
    }
    .stTabs [aria-selected="true"] {
        background: #e94560; color: white;
    }

    /* 隐藏footer */
    footer { display: none; }

    /* 链接 */
    a { color: #f5a623; }
    </style>
    """, unsafe_allow_html=True)


inject_style()


# ==================== 侧边栏导航 ====================
with st.sidebar:
    st.markdown("## 🎵 邪修音疗工作台")
    st.caption("36岁汽车大厂牛马的自救工具")
    st.markdown("---")

    page = st.radio(
        "导航",
        ["💡 选题每日灵感", "🎬 爆款二创", "📊 发布复盘", "📝 备忘录"],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.caption("💼 0元部署 · 手机可访问")
    st.caption("📍 Streamlit Cloud")


# ==================== 模块1：选题每日灵感 ====================
def render_inspiration():
    st.title("💡 选题每日灵感")
    st.caption("每天9点自动更新 · 本赛道 vs 泛赛道")

    # 日期选择
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_date = st.date_input("选择日期", value=date.today())
    with col2:
        if st.button("🔄 手动抓取今日热点"):
            _manual_fetch()

    date_str = selected_date.isoformat()

    # Tab分类
    tab_track, tab_broad = st.tabs(["🎯 本赛道热点", "🌐 泛赛道热点"])

    with tab_track:
        videos = get_videos_by_date(date_str, "本赛道")
        if videos:
            for v in videos:
                _render_video_card(v)
        else:
            st.info(f"暂无{selected_date}的本赛道热点数据。点击右上角「手动抓取」试试")

    with tab_broad:
        videos = get_videos_by_date(date_str, "泛赛道")
        if videos:
            for v in videos:
                _render_video_card(v)
        else:
            st.info(f"暂无{selected_date}的泛赛道热点数据")


def _manual_fetch():
    """手动触发抓取"""
    with st.spinner("正在抓取抖音热榜和小红书..."):
        import db as dbmod
        from datetime import date as dt_date

        # 抖音热榜
        dy_videos = fetch_douyin_hot(top_n=30)
        # 小红书
        xhs_track = search_xiaohongshu(XHS_KEYWORDS_TRACK, per_keyword=5)
        xhs_broad = search_xiaohongshu(XHS_KEYWORDS_BROAD, per_keyword=5)

        all_videos = dy_videos + xhs_track + xhs_broad
        seen = set()
        unique = []
        for v in all_videos:
            vid = v.get("video_id", "")
            if vid and vid not in seen:
                seen.add(vid)
                unique.append(v)

        success = 0
        for v in unique:
            try:
                cat_result = classify_video(v.get("title", ""), v.get("desc", ""))
                v["category"] = cat_result.get("category", "泛赛道")
                v["reason"] = cat_result.get("reason", "")
            except Exception:
                v["category"] = "泛赛道"
                v["reason"] = "分类失败"

            v["fetch_date"] = dt_date.today().isoformat()
            try:
                insert_hot_video(v)
                success += 1
            except Exception:
                continue  # 重复数据跳过

        st.success(f"✅ 抓取完成！共获取 {success} 条热点")


def _render_video_card(v: dict):
    """渲染视频卡片"""
    cat = v.get("category", "泛赛道")
    tag_class = "tag-track" if cat == "本赛道" else "tag-broad"

    col1, col2 = st.columns([4, 1])
    with col1:
        platform_icon = "📺" if v.get("source_platform") == "douyin" else "📕"
        st.markdown(f"""
        <span class="{tag_class}">{cat}</span>
        &nbsp;{platform_icon} <b>{v.get('title', '无标题')}</b>
        """, unsafe_allow_html=True)
        if v.get("reason"):
            st.caption(f"💡 {v['reason']}")
        if v.get("author"):
            st.caption(f"@{v['author']}")

        # 互动数据
        stats = []
        if v.get("play_count"): stats.append(f"🔥 {v['play_count']}")
        if v.get("like_count"): stats.append(f"❤️ {v['like_count']}")
        if v.get("comment_count"): stats.append(f"💬 {v['comment_count']}")
        if stats:
            st.caption(" · ".join(stats))

    with col2:
        if st.button("二创", key=f"btn_{v.get('video_id', id(v))}"):
            st.session_state["selected_video"] = v
            st.session_state["current_page"] = "🎬 爆款二创"
            st.rerun()

    st.markdown("---")


# ==================== 模块2：爆款二创 ====================
def render_recreation():
    st.title("🎬 爆款二创生成")
    st.caption("选定爆款 → AI生成脚本+分镜+钩子+人设检查")

    selected = st.session_state.get("selected_video")

    if selected:
        st.success(f"已选定：{selected.get('title', '')[:40]}")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🚀 生成二创", type="primary"):
                _do_generate(selected)
        with col2:
            if st.button("❌ 清除选择"):
                st.session_state.pop("selected_video", None)
                st.rerun()
    else:
        st.info("👈 请先在「选题每日灵感」中选择一个爆款视频")

    # 手动输入
    with st.expander("📌 或手动输入视频信息"):
        with st.form("manual_form"):
            m_title = st.text_input("视频标题")
            m_desc = st.text_area("视频描述")
            m_tags = st.text_input("标签（逗号分隔）")
            if st.form_submit_button("生成"):
                _do_generate({"title": m_title, "desc": m_desc, "tags": m_tags,
                               "like_count": 0, "comment_count": 0})

    # 显示生成结果
    result = st.session_state.get("recreation_result")
    if result:
        st.markdown("---")
        st.markdown(f"## 📋 {result.get('title', '生成结果')}")

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📝 脚本", "🎬 分镜", "📕 笔记", "📋 拍摄", "🎣 钩子", "✅ 检查"
        ])

        with tab1:
            st.text_area("口播脚本", value=result.get("script", ""), height=350, key="script_out")
        with tab2:
            st.markdown(result.get("storyboard", ""))
        with tab3:
            st.text_area("小红书笔记", value=result.get("xhs_note", ""), height=350, key="xhs_out")
        with tab4:
            st.markdown(result.get("shooting_list", ""))
        with tab5:
            hooks = result.get("hooks", [])
            if isinstance(hooks, str):
                hooks = json.loads(hooks)
            for i, h in enumerate(hooks):
                st.markdown(f"### 版本{chr(65+i)}：{h.get('type', '')}")
                st.markdown(f"**内容**：{h.get('content', '')}")
                st.markdown(f"**动作**：{h.get('action', '')}")
                st.markdown("")
        with tab6:
            st.markdown(result.get("persona_check", "无检查报告"))

        # 状态操作
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 确认采用"):
                rc_id = st.session_state.get("recreation_id")
                if rc_id:
                    update_recreation_status(rc_id, "selected")
                    st.success("已标记为「采用」")
        with col2:
            if st.button("📢 标记已发布"):
                rc_id = st.session_state.get("recreation_id")
                if rc_id:
                    update_recreation_status(rc_id, "published")
                    st.success("已标记「已发布」")

    # 历史记录
    st.markdown("---")
    st.markdown("## 📚 历史二创")
    history = list_recreations(limit=20)
    if history:
        for r in history:
            emoji = {"draft": "📝", "selected": "✅", "published": "📢"}.get(r.get("status"), "📝")
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"{emoji} **{r.get('title', '无标题')}**")
                st.caption(f"源：{r.get('source_title', '')[:30]} · {r.get('created_at', '')[:10]}")
            with col2:
                if st.button("查看", key=f"hist_{r['id']}"):
                    detail = get_recreation(r["id"])
                    if detail:
                        st.session_state["recreation_result"] = detail
                        st.session_state["recreation_id"] = r["id"]
                        st.rerun()
    else:
        st.info("暂无历史记录")


def _do_generate(video: dict):
    """执行二创生成"""
    with st.spinner("AI正在生成二创素材...（约30-60秒）"):
        # 获取详情
        if video.get("video_url"):
            try:
                detail = get_video_detail(video["video_url"], video.get("source_platform", "douyin"))
                if detail:
                    video.update(detail)
            except Exception:
                pass

        # 生成
        try:
            result = generate_recreation(video)
        except Exception as e:
            st.error(f"生成失败：{e}")
            return

        # 人设检查
        try:
            check = check_persona(result.get("script", ""))
            scores = check.get("scores", {})
            score_lines = "\n".join([f"  {k}: {v}/5" for k, v in scores.items()])
            passed = "✅ 通过" if check.get("pass") else "❌ 未通过"
            persona_str = f"检查结果：{passed}\n\n评分：\n{score_lines}\n\n建议：{check.get('suggestions', '')}"
            result["persona_check"] = persona_str
        except Exception as e:
            result["persona_check"] = f"人设检查失败：{e}"

        # 存数据库
        rc_data = {
            "source_title": video.get("title", ""),
            "source_url": video.get("video_url", ""),
            "title": result.get("title", ""),
            "script": result.get("script", ""),
            "storyboard": result.get("storyboard", ""),
            "xhs_note": result.get("xhs_note", ""),
            "shooting_list": result.get("shooting_list", ""),
            "hooks": json.dumps(result.get("hooks", []), ensure_ascii=False),
            "persona_check": result.get("persona_check", ""),
            "status": "draft",
        }
        try:
            saved = insert_recreation(rc_data)
            st.session_state["recreation_id"] = saved.get("id")
        except Exception as e:
            st.warning(f"保存到数据库失败（不影响使用）：{e}")

        st.session_state["recreation_result"] = result
        st.success("✅ 生成完成！")
        st.rerun()


# ==================== 模块3：发布复盘 ====================
def render_review():
    st.title("📊 发布内容复盘")
    st.caption("上传抖音创作者中心CSV → AI自动分析 + 优化建议")

    # 上传
    uploaded = st.file_uploader("选择CSV文件", type=["csv"])

    if uploaded:
        try:
            parsed = parse_douyin_csv(uploaded.getvalue())
            st.success(f"✅ 解析成功，共 {len(parsed)} 条数据")

            # 预览
            import pandas as pd
            df = pd.DataFrame(parsed)
            show_cols = {"title": "标题", "publish_date": "日期", "play_count": "播放",
                         "like_count": "点赞", "comment_count": "评论", "completion_rate": "完播率%"}
            available = {k: v for k, v in show_cols.items() if k in df.columns}
            if available:
                st.dataframe(df[list(available.keys())].rename(columns=available),
                           use_container_width=True, hide_index=True)

            # 分析
            if st.button("🚀 AI复盘分析", type="primary"):
                with st.spinner("AI分析中...（约30秒）"):
                    try:
                        analysis = analyze_review(parsed)
                        st.session_state["review_analysis"] = analysis
                        # 存数据库
                        for p in parsed:
                            p["ai_analysis"] = json.dumps(analysis, ensure_ascii=False)
                            try:
                                insert_review(p)
                            except Exception:
                                continue
                        st.success("分析完成！")
                        st.rerun()
                    except Exception as e:
                        st.error(f"分析失败：{e}")
        except Exception as e:
            st.error(f"CSV解析失败：{e}")

    # 分析结果
    analysis = st.session_state.get("review_analysis")
    if analysis:
        st.markdown("---")
        st.markdown("## 📈 复盘报告")

        # 单条表现
        per_video = analysis.get("per_video", [])
        if per_video:
            st.markdown("### 🎬 单条表现")
            for v in per_video:
                emoji = {"好": "🟢", "一般": "🟡", "差": "🔴"}.get(v.get("performance", ""), "⚪")
                with st.expander(f"{emoji} {v.get('title', '')} — {v.get('performance', '')}"):
                    if v.get("highlight"):
                        st.markdown(f"**✨ 亮点**：{v['highlight']}")
                    if v.get("issue"):
                        st.markdown(f"**⚠️ 问题**：{v['issue']}")

        if analysis.get("trend"):
            st.markdown("### 📉 趋势分析")
            st.info(analysis["trend"])

        if analysis.get("comparison"):
            st.markdown("### 🔍 对比分析")
            st.info(analysis["comparison"])

        suggestions = analysis.get("suggestions", [])
        if suggestions:
            st.markdown("### 💡 优化建议")
            for i, s in enumerate(suggestions, 1):
                st.markdown(f"**{i}.** {s}")

    # 历史图表
    st.markdown("---")
    st.markdown("## 📊 历史数据趋势")
    reviews = list_reviews(limit=50)
    if reviews and len(reviews) > 0:
        import pandas as pd
        import plotly.graph_objects as go

        df = pd.DataFrame(reviews)
        df = df.sort_values("publish_date")

        col1, col2 = st.columns(2)
        with col1:
            fig1 = go.Figure()
            if "play_count" in df.columns:
                fig1.add_trace(go.Scatter(x=df["publish_date"], y=df["play_count"],
                                         mode="lines+markers", name="播放量",
                                         line=dict(color="#e94560", width=2)))
            if "like_count" in df.columns:
                fig1.add_trace(go.Scatter(x=df["publish_date"], y=df["like_count"],
                                         mode="lines+markers", name="点赞",
                                         line=dict(color="#0f3460", width=2)))
            fig1.update_layout(title="播放&点赞趋势", template="plotly_dark",
                             height=280, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            fig2 = go.Figure()
            if "completion_rate" in df.columns:
                fig2.add_trace(go.Bar(x=df["publish_date"], y=df["completion_rate"],
                                     name="完播率%", marker_color="#e94560"))
            fig2.update_layout(title="完播率趋势", template="plotly_dark",
                             height=280, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("暂无历史数据，上传CSV后查看趋势图表")


# ==================== 模块4：备忘录 ====================
def render_memo():
    st.title("📝 备忘录")
    st.caption("随手记录灵感 · 手机随时记")

    # 快速记录
    col1, col2, col3 = st.columns([5, 2, 1])
    with col1:
        content = st.text_input("内容", placeholder="想到了什么？", label_visibility="collapsed")
    with col2:
        tag = st.selectbox("标签", ["灵感", "选题", "拍摄", "剪辑", "其他"], label_visibility="collapsed")
    with col3:
        if st.button("保存"):
            if content.strip():
                insert_memo(content.strip(), tag)
                st.success("已保存")
                st.rerun()
            else:
                st.warning("内容不能为空")

    st.markdown("---")

    # 筛选
    col1, col2 = st.columns(2)
    with col1:
        filter_tag = st.selectbox("筛选", ["全部", "灵感", "选题", "拍摄", "剪辑", "其他"])
    with col2:
        show_archived = st.checkbox("显示已归档")

    # 列表
    memos = list_memos(tag=filter_tag, archived=show_archived)
    if not memos:
        st.info("暂无记录")
        return

    st.caption(f"共 {len(memos)} 条")

    for m in memos:
        tag_color = {"灵感": "#e94560", "选题": "#0f3460", "拍摄": "#f5a623",
                     "剪辑": "#27ae60", "其他": "#888"}.get(m.get("tag", ""), "#888")
        created = m.get("created_at", "")[:16].replace("T", " ")

        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            st.markdown(f"""
            <span style="background:{tag_color};color:white;padding:2px 8px;border-radius:8px;font-size:10px;">{m.get('tag', '')}</span>
            &nbsp;<span style="color:#e0e0e0;">{m.get('content', '')}</span>
            &nbsp;<span style="color:#555;font-size:10px;">{created}</span>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("✏️", key=f"edit_{m['id']}", help="编辑"):
                st.session_state[f"editing_{m['id']}"] = True
                st.rerun()
        with col3:
            if st.button("📦", key=f"del_{m['id']}", help="归档"):
                delete_memo(m["id"])
                st.rerun()

        # 编辑模式
        if st.session_state.get(f"editing_{m['id']}"):
            with st.form(f"form_{m['id']}"):
                e_content = st.text_area("内容", value=m.get("content", ""))
                e_tag = st.selectbox("标签", ["灵感", "选题", "拍摄", "剪辑", "其他"],
                                    index=["灵感", "选题", "拍摄", "剪辑", "其他"].index(m.get("tag", "灵感")))
                c1, c2 = st.columns(2)
                with c1:
                    if st.form_submit_button("保存"):
                        update_memo(m["id"], content=e_content, tag=e_tag)
                        st.session_state.pop(f"editing_{m['id']}", None)
                        st.rerun()
                with c2:
                    if st.form_submit_button("取消"):
                        st.session_state.pop(f"editing_{m['id']}", None)
                        st.rerun()


# ==================== 路由 ====================
if "选题" in page:
    render_inspiration()
elif "二创" in page:
    render_recreation()
elif "复盘" in page:
    render_review()
elif "备忘录" in page:
    render_memo()

