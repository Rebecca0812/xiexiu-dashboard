import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from config import get_config, PERSONA
from db import Database
from api_service import (
    fetch_douyin_hot, search_xiaohongshu,
    classify_video, generate_recreation,
    check_persona, analyze_review
)
from csv_parser import parse_douyin_csv

st.set_page_config(
    page_title="邪修音疗工作台",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化
config = get_config()
db = Database(config)

# 自定义样式
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }
    .metric-card {
        background: #1e1e2e;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #7E57C2;
    }
    .hot-item {
        background: #1e1e2e;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 3px solid #7E57C2;
    }
    .persona-score {
        font-size: 1.2em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)
# ============ 侧边栏 ============
with st.sidebar:
    st.markdown("## 🎵 邪修音疗工作台")
    st.markdown("---")
    
    # API状态
    st.markdown("### ⚙️ 系统状态")
    if config["DEEPSEEK_API_KEY"]:
        st.success("✅ DeepSeek 已连接")
    else:
        st.error("❌ DeepSeek 未配置")
    
    if config["SUPABASE_URL"]:
        st.success("✅ 数据库已连接")
    else:
        st.error("❌ 数据库未配置")
    
    st.markdown("---")
    st.markdown("### 👤 人设档案")
    st.markdown(f"**赛道**：{PERSONA['track']}")
    st.markdown(f"**人设**：{PERSONA['persona']}")
    st.markdown(f"**年龄**：{PERSONA['age']}")
    st.markdown(f"**职业**：{PERSONA['job']}")
    
    st.markdown("---")
    st.markdown("### 💡 小贴士")
    st.info("每天9点自动抓取热点，也可手动刷新")


# ============ 主页面 ============
st.markdown('<div class="main-header"><h1>🎵 邪修音疗工作台</h1><p>抠搜邪修 · 音疗平替 · 治愈自己</p></div>', unsafe_allow_html=True)

# 四大模块导航
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 选题灵感", "🔥 爆款二创", "📊 发布复盘", "📝 备忘录"
])


# ============ 模块1：选题灵感 ============
with tab1:
    st.markdown("### 🎯 每日选题灵感")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 抓取抖音热榜", use_container_width=True):
            with st.spinner("正在抓取抖音热榜..."):
                result = fetch_douyin_hot(config)
                if result["success"]:
                    st.success(f"✅ 抓取成功，共 {len(result['data'])} 条")
                    st.session_state["douyin_hot"] = result["data"]
                else:
                    st.error(f"❌ {result['error']}")
    
    with col2:
        keyword = st.text_input("🔍 小红书搜索关键词", placeholder="如：平替音疗、助眠好物")
        if st.button("搜索小红书", use_container_width=True) and keyword:
            with st.spinner(f"正在搜索「{keyword}」..."):
                result = search_xiaohongshu(config, keyword)
                if result["success"]:
                    st.session_state["xhs_results"] = result["data"]
                    st.success(f"✅ 搜索到 {len(result['data'])} 条")
                else:
                    st.error(f"❌ {result['error']}")
    
    st.markdown("---")
    
    # 显示抖音热榜
    if "douyin_hot" in st.session_state:
        st.markdown("#### 📺 抖音热榜")
        for i, item in enumerate(st.session_state["douyin_hot"][:15]):
            with st.container():
                st.markdown(f"""
                <div class="hot-item">
                    <strong>#{i+1} {item.get('word', '未知标题')}</strong><br>
                    <small>🔥 热度：{item.get('hot_value', 'N/A')}</small>
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b = st.columns([3, 1])
                with col_b:
                    if st.button(f"AI分析", key=f"hot_{i}"):
                        with st.spinner("AI分析中..."):
                            analysis = classify_video(config, item)
                            if analysis["success"]:
                                st.info(analysis["data"])
                            else:
                                st.error(analysis["error"])
    
    # 显示小红书搜索结果
    if "xhs_results" in st.session_state:
        st.markdown("#### 📕 小红书搜索结果")
        for i, item in enumerate(st.session_state["xhs_results"][:10]):
            st.markdown(f"""
            <div class="hot-item">
                <strong>{item.get('title', '无标题')}</strong><br>
                <small>❤️ {item.get('likes', 0)} | 💬 {item.get('comments', 0)} | 🔖 {item.get('collects', 0)}</small>
            </div>
            """, unsafe_allow_html=True)
# ============ 模块2：爆款二创 ============
with tab2:
    st.markdown("### 🔥 爆款视频二创")
    st.markdown("输入爆款视频链接或文案，AI帮你生成符合人设的二创脚本")
    
    col1, col2 = st.columns([3, 2])
    with col1:
        video_url = st.text_input("📺 爆款视频链接", placeholder="粘贴抖音/小红书视频链接")
        video_text = st.text_area("📝 或直接粘贴视频文案", height=100, placeholder="把爆款视频的文案内容粘贴到这里...")
    
    with col2:
        st.markdown("#### ⚙️ 生成选项")
        style = st.selectbox("风格", ["幽默吐槽", "干货分享", "治愈叙事", "对比测评"])
        duration = st.selectbox("时长", ["15秒", "30秒", "60秒", "90秒"])
        if st.button("🚀 生成二创脚本", use_container_width=True):
            if video_url or video_text:
                with st.spinner("AI正在生成二创脚本..."):
                    result = generate_recreation(config, video_url, video_text, style, duration)
                    if result["success"]:
                        st.session_state["recreation"] = result["data"]
                    else:
                        st.error(result["error"])
            else:
                st.warning("请输入视频链接或文案")
    
    # 显示生成结果
    if "recreation" in st.session_state:
        st.markdown("---")
        st.markdown("#### 📋 二创脚本")
        st.markdown(st.session_state["recreation"])
        
        # 人设一致性检查
        st.markdown("---")
        st.markdown("#### 🔍 人设一致性检查")
        if st.button("检查人设一致性"):
            with st.spinner("AI检查中..."):
                check_result = check_persona(config, st.session_state["recreation"])
                if check_result["success"]:
                    scores = check_result["data"]
                    
                    # 评分展示
                    cols = st.columns(len(scores))
                    total = 0
                    for col, (dim, score) in zip(cols, scores.items()):
                        col.metric(dim, f"{score}/10")
                        total += score
                    
                    avg = total / len(scores) if scores else 0
                    if avg >= 8:
                        st.success(f"✅ 人设一致性：{avg:.1f}/10，非常符合！")
                    elif avg >= 6:
                        st.warning(f"⚠️ 人设一致性：{avg:.1f}/10，基本符合，可以优化")
                    else:
                        st.error(f"❌ 人设一致性：{avg:.1f}/10，偏差较大，建议调整")
                else:
                    st.error(check_result["error"])
# ============ 模块3：发布复盘 ============
with tab3:
    st.markdown("### 📊 发布内容复盘")
    st.markdown("上传抖音创作者中心导出的CSV数据，AI帮你分析复盘")
    
    col1, col2 = st.columns([2, 3])
    with col1:
        uploaded_file = st.file_uploader("📁 上传CSV文件", type=["csv"])
        if uploaded_file is not None:
            with st.spinner("正在解析CSV..."):
                df = parse_douyin_csv(uploaded_file)
                if df is not None and len(df) > 0:
                    st.session_state["review_df"] = df
                    st.success(f"✅ 解析成功，共 {len(df)} 条数据")
                else:
                    st.error("❌ CSV解析失败，请检查文件格式")
    
    with col2:
        if st.button("💡 AI复盘分析", use_container_width=True):
            if "review_df" in st.session_state:
                with st.spinner("AI正在分析你的内容数据..."):
                    result = analyze_review(config, st.session_state["review_df"])
                    if result["success"]:
                        st.session_state["review_analysis"] = result["data"]
                    else:
                        st.error(result["error"])
            else:
                st.warning("请先上传CSV文件")
    
    # 数据展示
    if "review_df" in st.session_state:
        st.markdown("---")
        df = st.session_state["review_df"]
        
        # 核心指标
        st.markdown("#### 📈 核心数据")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("总播放量", f"{df['play_count'].sum():,}")
        m2.metric("总点赞", f"{df['like_count'].sum():,}")
        m3.metric("总评论", f"{df['comment_count'].sum():,}")
        m4.metric("总分享", f"{df['share_count'].sum():,}")
        
        # 图表
        st.markdown("#### 📊 数据趋势")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            fig = px.bar(
                df, x="title", y="play_count",
                title="各视频播放量", color="play_count",
                color_continuous_scale="Purples"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            fig2 = px.scatter(
                df, x="play_count", y="like_count",
                title="播放vs点赞", size="comment_count",
                color="play_count", color_continuous_scale="Purples"
            )
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
        
        # 数据表格
        st.markdown("#### 📋 详细数据")
        st.dataframe(df, use_container_width=True)
    
    # AI分析结果
    if "review_analysis" in st.session_state:
        st.markdown("---")
        st.markdown("#### 🤖 AI复盘报告")
        st.info(st.session_state["review_analysis"])
# ============ 模块4：备忘录 ============
with tab4:
    st.markdown("### 📝 备忘录")
    st.markdown("记录灵感、待办、拍摄计划等")
    
    # 新增备忘
    with st.form("add_memo"):
        col1, col2 = st.columns([3, 1])
        with col1:
            memo_content = st.text_input("✏️ 输入备忘内容", placeholder="如：周末拍锅具敲击ASMR、找不锈钢碗平替...")
        with col2:
            memo_tag = st.selectbox("标签", ["灵感", "待办", "拍摄计划", "素材", "其他"])
        
        submitted = st.form_submit_button("➕ 添加备忘", use_container_width=True)
        if submitted and memo_content:
            result = db.add_memo(memo_content, memo_tag)
            if result["success"]:
                st.success("✅ 添加成功！")
                st.rerun()
            else:
                st.error(result["error"])
    
    st.markdown("---")
    
    # 筛选
    filter_tag = st.selectbox("筛选标签", ["全部", "灵感", "待办", "拍摄计划", "素材", "其他"])
    
    # 备忘列表
    memos = db.get_memos(filter_tag if filter_tag != "全部" else None)
    
    if memos:
        for memo in memos:
            col_a, col_b, col_c = st.columns([5, 1, 1])
            with col_a:
                tag_color = {
                    "灵感": "🔵", "待办": "🔴", "拍摄计划": "🟢",
                    "素材": "🟡", "其他": "⚪"
                }
                st.markdown(f"""
                <div class="hot-item">
                    {tag_color.get(memo.get('tag', ''), '⚪')} <strong>{memo.get('tag', '')}</strong><br>
                    {memo.get('content', '')}<br>
                    <small>📅 {memo.get('created_at', '')[:16]}</small>
                </div>
                """, unsafe_allow_html=True)
            with col_c:
                if st.button("🗑️", key=f"del_{memo.get('id')}"):
                    db.delete_memo(memo["id"])
                    st.rerun()
    else:
        st.info("暂无备忘，快添加第一条吧~ ✏️")


# ============ 页脚 ============
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#666;font-size:0.8em'>"
    "🎵 邪修音疗工作台 · 抠搜邪修 · 治愈自己<br>"
    f"⏰ 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    "</div>",
    unsafe_allow_html=True）
