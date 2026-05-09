import streamlit as st
import requests
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
import os

def chat(message):
    import os
    api_key = os.environ.get("GROQ_API_KEY", "")
    if api_key:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [{"role": "user", "content": message}]
            }
        )
        return response.json()["choices"][0]["message"]["content"]
    else:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "nous-hermes2",
                "prompt": message,
                "stream": False
            }
        )
        return response.json()["response"]

# 页面配置
st.set_page_config(page_title="AI理财助手", page_icon="💰", layout="wide")
st.title("💰 我的AI理财助手")

# 侧边栏输入
with st.sidebar:
    st.header("📊 输入您的资产")
    total = st.number_input("总资产（元）", value=50000, step=1000)
    st.divider()
    hs300 = st.number_input("沪深300指数基金", value=15000, step=1000)
    zz500 = st.number_input("中证500指数基金", value=7500, step=1000)
    money = st.number_input("货币基金", value=10000, step=1000)
    reserve = st.number_input("备用金", value=10000, step=1000)
    st.divider()
    monthly = st.number_input("每月定投金额（元）", value=1000, step=100)
    years = st.slider("定投年数", 1, 20, 5)
    analyze = st.button("🤖 开始AI分析", type="primary", use_container_width=True)

# 计算
gain_hs300 = hs300 * 0.08
gain_zz500 = zz500 * 0.12
gain_money = money * 0.025
total_gain = gain_hs300 + gain_zz500 + gain_money
annual_rate = total_gain / total * 100 if total > 0 else 0

# 顶部指标
col1, col2, col3, col4 = st.columns(4)
col1.metric("💼 总资产", f"{total:,}元")
col2.metric("📈 预期年收益", f"{total_gain:,.0f}元")
col3.metric("🎯 综合年化", f"{annual_rate:.1f}%")
col4.metric("📅 每月定投", f"{monthly:,}元")

st.divider()

# 两列布局
left, right = st.columns(2)

with left:
    st.subheader("🥧 资产分布")
    labels = ["沪深300", "中证500", "货币基金", "备用金"]
    values = [hs300, zz500, money, reserve]
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]

    fig_pie = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=colors
    )])
    fig_pie.update_layout(
        showlegend=True,
        height=300,
        margin=dict(t=0, b=0, l=0, r=0)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with right:
    st.subheader("💹 各类资产年收益")
    gains = [round(gain_hs300), round(gain_zz500), round(gain_money), 0]

    fig_bar = go.Figure(data=[go.Bar(
        x=labels,
        y=gains,
        marker_color=colors,
        text=[f"{g:,}元" for g in gains],
        textposition="auto"
    )])
    fig_bar.update_layout(
        height=300,
        margin=dict(t=0, b=0, l=0, r=0),
        yaxis_title="年收益（元）"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# 定投模拟图
st.subheader("📊 定投增长模拟")
monthly_rate = 0.08 / 12
months_total = years * 12
invested_list = []
value_list = []
month_labels = []
total_invested = 0
total_value = 0

for m in range(1, months_total + 1):
    total_invested += monthly
    total_value = (total_value + monthly) * (1 + monthly_rate)
    if m % 12 == 0:
        invested_list.append(total_invested)
        value_list.append(round(total_value))
        month_labels.append(f"第{m//12}年")

fig_line = go.Figure()
fig_line.add_trace(go.Scatter(
    x=month_labels, y=invested_list,
    name="累计投入", line=dict(color="#95A5A6", dash="dash")
))
fig_line.add_trace(go.Scatter(
    x=month_labels, y=value_list,
    name="资产价值", line=dict(color="#E74C3C"),
    fill="tonexty", fillcolor="rgba(231,76,60,0.1)"
))
fig_line.update_layout(
    height=300,
    margin=dict(t=10, b=0, l=0, r=0),
    yaxis_title="金额（元）",
    legend=dict(orientation="h")
)
st.plotly_chart(fig_line, use_container_width=True)

profit = total_value - total_invested
st.info(f"📌 每月定投{monthly:,}元，坚持{years}年，"
        f"累计投入{int(total_invested):,}元，"
        f"预计增长到 **{int(total_value):,}元**，"
        f"盈利 **{int(profit):,}元**")

# AI分析
if analyze:
    st.divider()
    st.subheader("🤖 AI深度分析")
    with st.spinner("AI分析中，请稍候约30秒..."):
        prompt = f"""
我的投资组合：
- 沪深300指数基金：{hs300}元（占{hs300/total*100:.1f}%，年化8%）
- 中证500指数基金：{zz500}元（占{zz500/total*100:.1f}%，年化12%）
- 货币基金：{money}元（占{money/total*100:.1f}%，年化2.5%）
- 备用金：{reserve}元（占{reserve/total*100:.1f}%）
- 综合年化：{annual_rate:.1f}%
- 每月定投：{monthly}元，计划{years}年

请给出3条具体可执行的优化建议，每条2句话。
"""
        result = chat(prompt)

    st.success(result)

    report = {
        "日期": str(date.today()),
        "总资产": total,
        "年化收益率": round(annual_rate, 1),
        "每月定投": monthly,
        "定投年数": years,
        "AI分析": result
    }
    with open("report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    st.caption("✅ 报告已保存到 report.json")
# ===== 每日市场简报 =====
st.divider()
st.subheader("📰 每日市场简报")

if st.button("🔄 获取今日AI市场分析", use_container_width=True):
    with st.spinner("AI正在分析今日市场..."):
        news_prompt = """
今天是2026年，请从以下角度简要分析中国股市：
1. 沪深300近期走势如何（一句话）
2. 影响A股的最主要因素（两点）
3. 对普通定投投资者的建议（一句话）
请用简洁的中文回答，总共不超过150字。
"""
        news_result = chat(news_prompt)
    st.info(news_result)

# ===== 保存和加载方案 =====
st.divider()
st.subheader("💾 我的投资方案")

col1, col2 = st.columns(2)

with col1:
    plan_name = st.text_input("方案名称", placeholder="例如：稳健型2026")
    if st.button("保存当前方案", use_container_width=True):
        plan = {
            "名称": plan_name,
            "日期": str(date.today()),
            "总资产": total,
            "沪深300": hs300,
            "中证500": zz500,
            "货币基金": money,
            "备用金": reserve,
            "月定投": monthly,
            "定投年数": years,
            "年化收益率": round(annual_rate, 1)
        }
        plans = []
        if os.path.exists("plans.json"):
            with open("plans.json", "r", encoding="utf-8") as f:
                plans = json.load(f)
        plans.append(plan)
        with open("plans.json", "w", encoding="utf-8") as f:
            json.dump(plans, f, ensure_ascii=False, indent=2)
        st.success(f"✅ 方案「{plan_name}」已保存！")

with col2:
    if os.path.exists("plans.json"):
        with open("plans.json", "r", encoding="utf-8") as f:
            plans = json.load(f)
        if plans:
            st.write("**历史方案：**")
            for p in plans[-3:]:
                st.write(f"📌 {p['名称']} ({p['日期']}) — 年化{p['年化收益率']}%")
    else:
        st.write("暂无保存的方案")
# ===== 分享引导 =====
st.divider()
st.markdown("""
<div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;'>
    <h3>💡 觉得有用？分享给朋友</h3>
    <p>复制链接发给需要理财规划的朋友</p>
    <h2>https://diefish7-finance.streamlit.app</h2>
    <p>完全免费 · AI驱动 · 3分钟看懂您的资产</p>
</div>
""", unsafe_allow_html=True)
