
"""
抠搜邪修音疗 · 自媒体运营工作台
最终版 - 支持粘贴视频链接自动解析
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from config import (
    DEEPSEEK_API_KEY, SUPABASE_URL, SUPABASE_KEY,
    TIKHUB_API_KEY, PERSONA, CONTENT_DNA
)

st.set_page_config(
    page_title="邪修音疗工作台",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== 初始化 ====================

def init_db():
    try:
        import db
        return db
    except Exception as e:
        st.error(f"数据库初始化失败: {e}")
        return None


def init_api():
    try:
        import api_service
        return api_service
    except Exception as e:
        st.error(f"API初始化失败: {e}")
        return None


# ==================== 侧边栏 ====================

def render_sidebar():
    with st.sidebar:
        st.markdown("## 🎵 邪修音疗工作台")
        st.markdown("---")

        st.markdown("### ⚙️ 系统状态")
        if DEEPSEEK_API_KEY:
            st.success("✅ DeepSeek 已连接")
        else:
            st.error("❌ DeepSeek 未配置")

        if SUPABASE_URL and SUPABASE_KEY:
            st.success("✅ 数据库已连接")
        else:
            st.error("❌ 数据库未配置")

        if TIKHUB_API_KEY:
            st.success("✅ TikHub 已连接")
        else:
            st.warning("⚠️ TikHub 未配置（手动模式）")

        st.markdown("---")
        st.markdown("### 👤 人设档案")
        st.markdown(PERSONA)

        st.markdown("---")
        st.info("💡 每日9点自动抓取热点，也可手动刷新")


# ==================== 模块1：选题灵感 ====================

def render_inspiration(db, api):
    st.markdown("### 🎯 每日选题灵感")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📺 抖音热榜")
        if st.button("🔄 抓取抖音热榜", use_container_width=True):
            if not TIKHUB_API_KEY:
                st.warning("TikHub API Key未配置")
            else:
                with st.spinner("正在抓取..."):
                    items = api.fetch_douyin_hot(15)
                    if items:
                        for i, item in enumerate(items):
                            st.markdown(f"**#{i+1}** {item['title']}  🔥{item.get('hot_value', '')}")
                            try:
                                db.insert_hot_topic(item['title'], item.get('hot_value', ''))
                            except Exception:
                                pass
                        st.success(f"抓取成功，共 {len(items)} 条")
                    else:
                        st.error("抓取失败，请查看日志")

        st.markdown("#### 📕 小红书搜索")
        keyword = st.text_input("关键词", placeholder="如：颂钵平替、助眠好物")
        if st.button("搜索小红书", use_container_width=True) and keyword:
            if not TIKHUB_API_KEY:
                st.warning("TikHub API Key未配置")
            else:
                with st.spinner("搜索中..."):
                    results = api.search_xiaohongshu(keyword, 10)
                    if results:
                        for r in results:
                            st.markdown(f"**{r['title']}**  ❤️{r.get('like_count', 0)} 💬{r.get('comment_count', 0)}")
                    else:
                        st.info("未搜到结果")

    with col2:
        st.markdown("#### 📋 历史热点")
        try:
            topics = db.list_hot_topics(15)
            if topics:
                for t in topics:
                    time_str = t.get('fetched_at', '')[:16]
                    st.markdown(f"**{t.get('title', '')}**  🔥{t.get('hot_value', '')}  📅{time_str}")
            else:
                st.info("暂无历史热点")
        except Exception as e:
            st.info("暂无历史数据")

        st.markdown("#### 💡 AI选题建议")
        if st.button("🚀 生成今日选题", use_container_width=True):
            if not DEEPSEEK_API_KEY:
                st.warning("DeepSeek API Key未配置")
            else:
                with st.spinner("AI生成中..."):
                    try:
                        topics = db.list_hot_topics(5)
                        topic_text = "\n".join([t.get('title', '') for t in topics]) if topics else "暂无热点数据"
                        prompt = f"""你是"抠搜邪修音疗"账号的选题顾问。

人设：{PERSONA}

今日热点：
{topic_text}

请给出3个结合热点的选题方向，每个包含：
1. 标题
2. 为什么能火
3. 拍摄思路
简洁回答。"""
                        suggestion = api._chat([{"role": "user", "content": prompt}], temperature=0.8)
                        st.info(suggestion)
                    except Exception as e:
                        st.error(f"生成失败: {e}")


# ==================== 模块2：爆款二创（支持链接解析）====================

def render_recreation(api):
    st.markdown("### 🔥 爆款视频二创")
    st.markdown("粘贴抖音/小红书链接自动解析，或手动输入视频信息")

    # 链接解析区
    st.markdown("#### 📎 第一步：粘贴爆款链接（自动解析）")
    video_url = st.text_input("视频链接", placeholder="粘贴抖音或小红书分享链接")

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        parse_clicked = st.button("🔍 解析视频", use_container_width=True)

    if parse_clicked and video_url:
        if not TIKHUB_API_KEY:
            st.warning("TikHub API Key未配置，无法解析链接")
        else:
            with st.spinner("正在解析视频..."):
                try:
                    info = api.parse_video_link(video_url)
                    if "error" in info:
                        st.error(info["error"])
                    else:
                        st.session_state["parsed_video"] = info
                        st.success("✅ 解析成功！")
                except Exception as e:
                    st.error(f"解析失败: {e}")

    # 显示解析结果
    if "parsed_video" in st.session_state:
        info = st.session_state["parsed_video"]
        st.markdown("---")
        st.markdown("#### 📋 解析结果")
        st.markdown(f"**标题：** {info.get('title', '')}")
        st.markdown(f"**作者：** {info.get('author', '')}")
        st.markdown(f"**点赞：** {info.get('like_count', 0)}  **评论：** {info.get('comment_count', 0)}")
        st.markdown(f"**描述：** {info.get('desc', '')[:200]}")

    # 手动输入区
    st.markdown("---")
    st.markdown("#### ✏️ 或直接输入视频信息")

    default_title = ""
    default_desc = ""
    if "parsed_video" in st.session_state:
        default_title = st.session_state["parsed_video"].get("title", "")
        default_desc = st.session_state["parsed_video"].get("desc", "")

    col1, col2 = st.columns([3, 2])

    with col1:
        video_title = st.text_input("视频标题", value=default_title, placeholder="粘贴视频标题")
        video_desc = st.text_area("视频文案/描述", value=default_desc, height=100, placeholder="粘贴视频文案内容...")

    with col2:
        st.markdown("#### ⚙️ 生成选项")
        style = st.selectbox("风格", ["幽默自嘲", "干货分享", "治愈叙事", "对比测评"])
        duration = st.selectbox("时长", ["15秒", "30秒", "60秒", "90秒"])

        if st.button("🚀 生成二创脚本", use_container_width=True):
            if not video_title:
                st.warning("请输入视频标题")
            elif not DEEPSEEK_API_KEY:
                st.warning("DeepSeek API Key未配置")
            else:
                with st.spinner("AI生成中，请稍候..."):
                    try:
                        result = api.generate_recreation(video_title, video_desc, style, duration)
                        st.session_state["recreation"] = result
                    except Exception as e:
                        st.error(f"生成失败: {e}")

    if "recreation" in st.session_state:
        st.markdown("---")
        st.markdown("#### 📋 二创脚本")
        st.markdown(st.session_state["recreation"])

        st.markdown("---")
        st.markdown("#### 🔍 人设一致性检查")
        if st.button("检查人设一致性"):
            with st.spinner("AI检查中..."):
                try:
                    scores = api.check_persona(st.session_state["recreation"])
                    if "error" not in scores:
                        cols = st.columns(len(scores) - 1)
                        total = 0
                        for col, (dim, score) in zip(cols, [(k, v) for k, v in scores.items() if k != "suggestions"]):
                            col.metric(dim, f"{score}/10")
                            total += score
                        avg = total / (len(scores) - 1)
                        if avg >= 8:
                            st.success(f"✅ 人设一致性：{avg:.1f}/10，非常符合！")
                        elif avg >= 6:
                            st.warning(f"⚠️ 人设一致性：{avg:.1f}/10，可以优化")
                        else:
                            st.error(f"❌ 人设一致性：{avg:.1f}/10，偏差较大")
                        if "suggestions" in scores:
                            st.info(scores["suggestions"])
                    else:
                        st.error("检查失败")
                except Exception as e:
                    st.error(f"检查失败: {e}")


# ==================== 模块3：发布复盘 ====================

def render_review(api):
    st.markdown("### 📊 发布内容复盘")
    st.markdown("上传抖音创作者中心导出的CSV，AI帮你分析")

    col1, col2 = st.columns([2, 3])

    with col1:
        uploaded_file = st.file_uploader("📁 上传CSV文件", type=["csv"])
        if uploaded_file is not None:
            try:
                from csv_parser import parse_douyin_csv
                content = uploaded_file.read()
                data = parse_douyin_csv(content)
                if data:
                    st.session_state["review_data"] = data
                    st.success(f"✅ 解析成功，共 {len(data)} 条")
                else:
                    st.error("解析失败")
            except Exception as e:
                st.error(f"解析失败: {e}")

    with col2:
        if st.button("💡 AI复盘分析", use_container_width=True):
            if "review_data" not in st.session_state:
                st.warning("请先上传CSV")
            elif not DEEPSEEK_API_KEY:
                st.warning("DeepSeek API Key未配置")
            else:
                with st.spinner("AI分析中..."):
                    try:
                        data = st.session_state["review_data"]
                        data_text = ""
                        for i, v in enumerate(data, 1):
                            data_text += f"视频{i}：{v.get('title', '')}\n  播放:{v.get('play_count',0)} 点赞:{v.get('like_count',0)} 评论:{v.get('comment_count',0)}\n"
                        result = api.analyze_review(data_text)
                        st.session_state["review_analysis"] = result
                    except Exception as e:
                        st.error(f"分析失败: {e}")

    if "review_data" in st.session_state:
        st.markdown("---")
        data = st.session_state["review_data"]
        df = pd.DataFrame(data)

        st.markdown("#### 📈 核心数据")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("总播放量", f"{df['play_count'].sum():,}")
        m2.metric("总点赞", f"{df['like_count'].sum():,}")
        m3.metric("总评论", f"{df['comment_count'].sum():,}")
        m4.metric("总分享", f"{df['share_count'].sum():,}")

        st.markdown("#### 📊 数据图表")
        fig = px.bar(df, x="title", y="play_count", title="各视频播放量", color="play_count", color_continuous_scale="Purples")
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### 📋 详细数据")
        st.dataframe(df, use_container_width=True)

    if "review_analysis" in st.session_state:
        st.markdown("---")
        st.markdown("#### 🤖 AI复盘报告")
        st.info(st.session_state["review_analysis"])


# ==================== 模块4：备忘录 ====================

def render_memo(db):
    st.markdown("### 📝 备忘录")

    with st.form("add_memo"):
        col1, col2 = st.columns([3, 1])
        with col1:
            content = st.text_input("✏️ 输入备忘内容", placeholder="如：周末拍锅具敲击ASMR...")
        with col2:
            tag = st.selectbox("标签", ["灵感", "选题", "拍摄", "剪辑", "其他"])

        if st.form_submit_button("➕ 添加备忘", use_container_width=True):
            if content:
                try:
                    db.insert_memo(content, tag)
                    st.success("✅ 添加成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"添加失败: {e}")

    st.markdown("---")

    filter_tag = st.selectbox("筛选标签", ["全部", "灵感", "选题", "拍摄", "剪辑", "其他"])

    try:
        memos = db.list_memos(filter_tag if filter_tag != "全部" else None)
        if memos:
            for m in memos:
                col_a, col_b = st.columns([5, 1])
                with col_a:
                    tag_emoji = {"灵感": "🔵", "选题": "🟢", "拍摄": "🟡", "剪辑": "🟣", "其他": "⚪"}
                    st.markdown(f"""{tag_emoji.get(m.get('tag', ''), '⚪')} **{m.get('tag', '')}** | {m.get('content', '')}
<small>📅 {m.get('created_at', '')[:16]}</small>""", unsafe_allow_html=True)
                with col_b:
                    if st.button("🗑️", key=f"del_{m['id']}"):
                        db.delete_memo(m["id"])
                        st.rerun()
        else:
            st.info("暂无备忘，快添加第一条吧~ ✏️")
    except Exception as e:
        st.error(f"读取备忘失败: {e}")


# ==================== 主程序 ====================

def main():
    render_sidebar()

    st.markdown('<h1 style="color:#7E57C2">🎵 邪修音疗工作台</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#888">抠搜邪修 · 音疗平替 · 治愈自己</p>', unsafe_allow_html=True)
    st.markdown("---")

    db = init_db()
    api = init_api()

    page = st.radio("选择模块", ["🎯 选题灵感", "🔥 爆款二创", "📊 发布复盘", "📝 备忘录"], horizontal=True)

    if "选题" in page and db and api:
        render_inspiration(db, api)
    elif "二创" in page and api:
        render_recreation(api)
    elif "复盘" in page and api:
        render_review(api)
    elif "备忘录" in page and db:
        render_memo(db)


if __name__ == "__main__":
    main()


