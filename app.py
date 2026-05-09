import streamlit as st
import requests
import json
import plotly.graph_objects as go
from datetime import date
import os

def chat(message):
    api_key = os.environ.get("GROQ_API_KEY", "")
    if api_key:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": message}]
            }
        )
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", str(data))
    else:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "nous-hermes2", "prompt": message, "stream": False}
        )
        return response.json()["response"]

FUND_INFO = {
    "货币基金": {"说明": "最安全，类似存钱，随时可取，年化约2%", "年化": 0.020, "风险": "极低"},
    "债券基金": {"说明": "比存款高一点，波动小，年化约4%", "年化": 0.040, "风险": "低"},
    "沪深300": {"说明": "跟踪A股最大300家公司，长期稳健", "年化": 0.080, "风险": "中"},
    "中证500": {"说明": "中小企业为主，弹性更大收益更高", "年化": 0.100, "风险": "中高"},
    "纳斯达克": {"说明": "美国科技股，苹果微软等，美元资产", "年化": 0.120, "风险": "中高"},
    "黄金ETF": {"说明": "抗通胀避险，和股市反向波动", "年化": 0.060, "风险": "中"},
}

st.set_page_config(page_title="AI理财助手", page_icon="💰", layout="wide")

st.markdown("""
<style>
.fund-card {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 10px;
    margin: 5px 0;
    border-left: 4px solid #667eea;
}
</style>
""", unsafe_allow_html=True)

st.title("AI理财助手")
st.caption("输入您的资产，AI帮您分析配置是否合理")

with st.sidebar:
    st.header("我的资产")
    total = st.number_input("总资产（元）", value=50000, step=1000)
    st.divider()
    st.markdown("**选择投资品种**")

    holdings = {}
    defaults = {"货币基金": 10000, "沪深300": 15000, "中证500": 7500}
    for fund_name, info in FUND_INFO.items():
        amount = st.number_input(
            f"{fund_name}（{info['风险']}风险，年化{info['年化']*100:.0f}%）",
            value=defaults.get(fund_name, 0),
            step=1000,
            key=f"fund_{fund_name}",
            help=info["说明"]
        )
        if amount > 0:
            holdings[fund_name] = amount

    st.divider()
    monthly = st.number_input("每月定投（元）", value=1000, step=100)
    years = st.slider("定投年数", 1, 20, 5)
    analyze = st.button("AI分析", type="primary", use_container_width=True)

total_gain = sum(holdings.get(k, 0) * FUND_INFO[k]["年化"] for k in holdings)
annual_rate = total_gain / total * 100 if total > 0 else 0
allocated = sum(holdings.values())
unallocated = total - allocated

c1, c2, c3, c4 = st.columns(4)
c1.metric("总资产", f"{total:,}元")
c2.metric("预期年收益", f"{total_gain:,.0f}元")
c3.metric("综合年化", f"{annual_rate:.1f}%")
c4.metric("未配置", f"{unallocated:,}元")

if unallocated > 0:
    st.warning(f"还有 {unallocated:,}元 未配置，建议分配到货币基金或指数基金。")
elif unallocated < 0:
    st.error(f"配置金额超出总资产 {abs(unallocated):,}元，请检查各项金额。")

st.divider()

with st.expander("小白必看：各类基金是什么？"):
    for name, info in FUND_INFO.items():
        st.markdown(f"""
<div class="fund-card">
<b>{name}</b> — {info["说明"]}<br>
风险：{info["风险"]} | 预期年化：{info["年化"]*100:.0f}%
</div>
""", unsafe_allow_html=True)

if holdings:
    col1, col2 = st.columns(2)
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD"]

    with col1:
        st.subheader("资产分布")
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(holdings.keys()),
            values=list(holdings.values()),
            hole=0.4,
            marker_colors=colors[:len(holdings)]
        )])
        fig_pie.update_layout(height=280, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("预期年收益")
        gains = [round(holdings.get(k, 0) * FUND_INFO[k]["年化"]) for k in holdings]
        fig_bar = go.Figure(data=[go.Bar(
            x=list(holdings.keys()),
            y=gains,
            marker_color=colors[:len(holdings)],
            text=[f"{g:,}元" for g in gains],
            textposition="auto"
        )])
        fig_bar.update_layout(height=280, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("定投增长模拟")
monthly_rate = 0.08 / 12
months_total = years * 12
invested_list, value_list, month_labels = [], [], []
total_invested, total_value = 0, 0

for m in range(1, months_total + 1):
    total_invested += monthly
    total_value = (total_value + monthly) * (1 + monthly_rate)
    if m % 12 == 0:
        invested_list.append(total_invested)
        value_list.append(round(total_value))
        month_labels.append(f"第{m//12}年")

fig_line = go.Figure()
fig_line.add_trace(go.Scatter(x=month_labels, y=invested_list, name="累计投入",
    line=dict(color="#95A5A6", dash="dash")))
fig_line.add_trace(go.Scatter(x=month_labels, y=value_list, name="资产价值",
    line=dict(color="#E74C3C"), fill="tonexty", fillcolor="rgba(231,76,60,0.1)"))
fig_line.update_layout(height=280, margin=dict(t=10, b=0, l=0, r=0),
    yaxis_title="金额（元）", legend=dict(orientation="h"))
st.plotly_chart(fig_line, use_container_width=True)

profit = total_value - total_invested
st.info(f"每月定投{monthly:,}元，坚持{years}年，累计投入{int(total_invested):,}元，预计增长到 {int(total_value):,}元，盈利 {int(profit):,}元")

if analyze and holdings:
    st.divider()
    st.subheader("AI深度分析")
    holdings_text = "\n".join([f"- {k}：{v}元（占{v/total*100:.1f}%）" for k, v in holdings.items()])
    with st.spinner("AI分析中..."):
        result = chat(f"""
我的投资组合：
{holdings_text}
总资产：{total}元，综合年化：{annual_rate:.1f}%
每月定投：{monthly}元，计划{years}年
请给出3条具体可执行的优化建议，每条2句话，用中文回答。
""")
    st.success(result)

st.divider()
st.subheader("每日市场简报")
if st.button("获取今日AI市场分析", use_container_width=True):
    with st.spinner("分析中..."):
        news_result = chat("请简要分析2026年中国股市现状，给普通定投投资者3条建议，用中文，150字以内。")
    st.info(news_result)

st.divider()
st.subheader("保存我的方案")
col1, col2 = st.columns(2)
with col1:
    plan_name = st.text_input("方案名称", placeholder="例如：稳健型2026")
    if st.button("保存当前方案", use_container_width=True):
        plan = {"名称": plan_name, "日期": str(date.today()),
                "总资产": total, "持仓": holdings,
                "月定投": monthly, "年化": round(annual_rate, 1)}
        plans = []
        if os.path.exists("plans.json"):
            with open("plans.json", "r", encoding="utf-8") as f:
                plans = json.load(f)
        plans.append(plan)
        with open("plans.json", "w", encoding="utf-8") as f:
            json.dump(plans, f, ensure_ascii=False, indent=2)
        st.success(f"已保存「{plan_name}」")
with col2:
    if os.path.exists("plans.json"):
        with open("plans.json", "r", encoding="utf-8") as f:
            plans = json.load(f)
        st.write("**历史方案：**")
        for p in plans[-3:]:
            st.write(f"{p['名称']} ({p['日期']}) 年化{p['年化']}%")
    else:
        st.write("暂无保存的方案")

st.divider()
st.markdown("""
<div style='text-align:center;padding:20px;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:10px;color:white;'>
<h3>觉得有用？分享给朋友</h3>
<h2>https://diefish7-finance.streamlit.app</h2>
<p>完全免费 · AI驱动 · 3分钟看懂您的资产</p>
</div>
""", unsafe_allow_html=True)
