import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import json

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Bhopal Smart City AI Assistant",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stAppViewBlockContainer"] {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    [data-testid="stSidebar"] {
        width: 250px !important;
        background-color: #1a1a2e;
        border-right: 1px solid #00b894;
    }
    .stApp { background-color: #0f1117; color: #ffffff; }
    .metric-card {
        background: #1e2130;
        border: 1px solid #2d3436;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin: 8px 0;
    }
    .metric-value { font-size: 32px; font-weight: bold; color: #00b894; }
    .metric-label { font-size: 13px; color: #b2bec3; margin-top: 4px; }
    .user-msg {
        background: #2d3436;
        border-radius: 12px 12px 4px 12px;
        padding: 12px 16px; margin: 8px 0;
        color: white; max-width: 80%; margin-left: auto;
    }
    .ai-msg {
        background: #1e3a2f;
        border: 1px solid #00b894;
        border-radius: 12px 12px 12px 4px;
        padding: 12px 16px; margin: 8px 0;
        color: white; max-width: 85%;
    }
    .insight-box {
        background: #1e2130;
        border-left: 4px solid #00b894;
        border-radius: 0 12px 12px 0;
        padding: 16px 20px; margin: 12px 0;
        color: #dfe6e9; line-height: 1.7;
    }
    .stButton > button {
        background: #00b894; color: white;
        border: none; border-radius: 8px;
        font-weight: bold; width: 100%;
    }
    .stButton > button:hover { background: #00a381; }
    .main-title {
        font-size: 28px; font-weight: bold;
        color: white; margin-top: 20px !important;
    }
    .sub-title { font-size: 14px; color: #b2bec3; margin-bottom: 12px; }
    .section-header {
        font-size: 18px; font-weight: bold; color: #00b894;
        border-bottom: 1px solid #2d3436;
        padding-bottom: 8px; margin: 16px 0 12px 0;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────
@st.cache_resource
def get_engine():
    DB_USER = st.secrets.get("DB_USER", "postgres")
    DB_PASS = st.secrets.get("DB_PASS", "your_password")
    DB_HOST = st.secrets.get("DB_HOST", "localhost")
    DB_PORT = st.secrets.get("DB_PORT", "5432")
    DB_NAME = st.secrets.get("DB_NAME", "bhopal_smart_city")
    return create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

@st.cache_data(ttl=300)
def load_summary_data():
    engine = get_engine()
    summaries = {}
    try:
        summaries["smart_city"] = pd.read_sql("""
            SELECT status, COUNT(*) as count,
                   ROUND(SUM(budget_cr),2) as budget,
                   ROUND(SUM(spent_cr),2) as spent
            FROM smart_city_projects GROUP BY status
        """, engine).to_dict(orient="records")

        summaries["aqi"] = pd.read_sql("""
            SELECT season,
                   ROUND(AVG(aqi_value),1) as avg_aqi,
                   COUNT(CASE WHEN health_flag='Unhealthy' THEN 1 END) as unhealthy_days
            FROM air_quality GROUP BY season
        """, engine).to_dict(orient="records")

        summaries["lakes"] = pd.read_sql("""
            SELECT lake_name,
                   ROUND(AVG(dissolved_oxygen),2) as avg_do,
                   ROUND(AVG(bod),2) as avg_bod,
                   COUNT(CASE WHEN pollution_flag='Heavily Polluted' THEN 1 END) as polluted_months
            FROM lake_quality GROUP BY lake_name
        """, engine).to_dict(orient="records")

        summaries["healthcare"] = pd.read_sql("""
            SELECT w.zone,
                   COUNT(h.facility_id) as facilities,
                   COALESCE(SUM(h.beds),0) as beds,
                   ROUND(COALESCE(SUM(h.beds),0)*1000.0/SUM(w.population),2) as beds_per_1000
            FROM wards w LEFT JOIN healthcare h ON w.ward_id=h.ward_id
            GROUP BY w.zone
        """, engine).to_dict(orient="records")

        summaries["complaints"] = pd.read_sql("""
            SELECT zone,
                   COUNT(*) as total,
                   COUNT(CASE WHEN status='Resolved' THEN 1 END) as resolved,
                   ROUND(COUNT(CASE WHEN status='Resolved' THEN 1 END)*100.0/COUNT(*),2) as rate,
                   ROUND(AVG(CASE WHEN days_to_resolve IS NOT NULL
                             AND days_to_resolve != -1
                             THEN days_to_resolve END),1) as avg_days
            FROM complaints GROUP BY zone
        """, engine).to_dict(orient="records")

    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.info("Please update DB credentials in the sidebar.")
    return summaries

@st.cache_data(ttl=300)
def load_chart_data():
    engine = get_engine()
    data = {}
    try:
        data["monthly_aqi"] = pd.read_sql("""
            SELECT month_num,
                   TO_CHAR(TO_DATE(month_num::TEXT,'MM'),'Mon') as month_name,
                   ROUND(AVG(aqi_value),1) as avg_aqi
            FROM air_quality GROUP BY month_num ORDER BY month_num
        """, engine)

        data["zone_complaints"] = pd.read_sql("""
            SELECT zone,
                   COUNT(*) as total,
                   ROUND(COUNT(CASE WHEN status='Resolved' THEN 1 END)*100.0/COUNT(*),1) as resolution_pct
            FROM complaints GROUP BY zone
        """, engine)

        data["lake_trend"] = pd.read_sql("""
            SELECT lake_name, year_num,
                   ROUND(AVG(dissolved_oxygen),2) as avg_do
            FROM lake_quality GROUP BY lake_name, year_num ORDER BY year_num
        """, engine)

        data["zone_beds"] = pd.read_sql("""
            SELECT w.zone,
                   ROUND(COALESCE(SUM(h.beds),0)*1000.0/SUM(w.population),2) as beds_per_1000
            FROM wards w LEFT JOIN healthcare h ON w.ward_id=h.ward_id
            GROUP BY w.zone
        """, engine)

        data["project_status"] = pd.read_sql("""
            SELECT status, COUNT(*) as count
            FROM smart_city_projects GROUP BY status
        """, engine)

    except Exception as e:
        st.error(f"Chart data error: {e}")
    return data


# ─────────────────────────────────────────
# GEMINI AI FUNCTIONS
# ─────────────────────────────────────────
def get_ai_client():
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")

def build_context(summaries):
    return f"""
You are an expert data analyst assistant for the Bhopal Smart City Intelligence Dashboard.
You have deep knowledge of Bhopal's urban data across 4 dimensions.

Here is the actual data from the database:

SMART CITY PROJECTS:
{json.dumps(summaries.get('smart_city', []), indent=2)}

AIR QUALITY BY SEASON:
{json.dumps(summaries.get('aqi', []), indent=2)}

LAKE WATER QUALITY:
{json.dumps(summaries.get('lakes', []), indent=2)}

HEALTHCARE BY ZONE:
{json.dumps(summaries.get('healthcare', []), indent=2)}

CITIZEN COMPLAINTS BY ZONE:
{json.dumps(summaries.get('complaints', []), indent=2)}

IMPORTANT CONTEXT:
- Data covers Bhopal, Madhya Pradesh, India (2019-2024)
- Bhopal is designated as a Smart City under India's Smart Cities Mission
- The city has 4 zones: New Bhopal, Old Bhopal, North Bhopal, Periphery
- Upper Lake and Lower Lake are Bhopal's two major water bodies
- WHO recommends 5 hospital beds per 1000 population

Always answer in a clear, professional data analyst style.
Use specific numbers from the data. Be concise but insightful.
If asked about something not in the data, say so clearly.
"""

def chat_with_ai(client, messages, summaries):
    context = build_context(summaries)
    # Build full conversation for Gemini
    history = ""
    for msg in messages[:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history += f"{role}: {msg['content']}\n\n"
    last_msg = messages[-1]["content"]
    full_prompt = f"{context}\n\nConversation so far:\n{history}\nUser: {last_msg}\n\nAnswer as an expert data analyst:"
    response = client.generate_content(full_prompt)
    return response.text

def generate_insights(client, module, summaries):
    context = build_context(summaries)
    prompts = {
        "🏛️ Smart City Delivery": """
            Analyze the Smart City project data and generate a professional insight report.
            Cover: completion rate, budget utilization, zone-wise distribution,
            biggest risks, and 3 specific actionable recommendations.
            Format with clear sections: Finding, Risk, Recommendation.
            Be specific with numbers.
        """,
        "🌿 Environment & Lakes": """
            Analyze Bhopal's air quality and lake data.
            Cover: worst AQI seasons, unhealthy days count, Upper vs Lower Lake comparison,
            dissolved oxygen trends, pollution classification, and 3 recommendations.
            Format with clear sections: Finding, Risk, Recommendation.
        """,
        "🏥 Healthcare Access": """
            Analyze Bhopal's healthcare infrastructure data.
            Cover: beds per 1000 by zone, most underserved areas, facility distribution,
            comparison to WHO standards, and 3 specific recommendations.
            Format with clear sections: Finding, Risk, Recommendation.
        """,
        "📋 Citizen Grievances": """
            Analyze Bhopal's citizen complaint data.
            Cover: total complaints, resolution rates by zone, worst performing areas,
            trends, and 3 specific actionable recommendations.
            Format with clear sections: Finding, Risk, Recommendation.
        """
    }
    full_prompt = f"{context}\n\n{prompts[module]}"
    response = client.generate_content(full_prompt)
    return response.text


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; margin-top: -40px; padding-bottom: 10px;'>
        <img src="https://upload.wikimedia.org/wikipedia/commons/d/da/Bhopal_Smart_City_Logo.png"
             style="width:100%; max-width:180px; height:auto; object-fit:contain;">
        <div style='font-size:18px; font-weight:bold; color:white; margin-top:8px'>Bhopal Smart City</div>
        <div style='font-size:12px; color:#00b894'>AI Intelligence Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["🏠 Overview", "🤖 AI Chatbot", "📊 AI Insight Generator"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("""
    <div style='font-size:11px; color:#636e72; text-align:center'>
        Built by Om Jitpure<br>
        Python | SQL | KNIME | Power BI<br>
        Powered by Google Gemini AI
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────
summaries  = load_summary_data()
chart_data = load_chart_data()

if "messages" not in st.session_state:
    st.session_state["messages"] = []


# ─────────────────────────────────────────
# PAGE 1 — OVERVIEW
# ─────────────────────────────────────────
if page == "🏠 Overview":
    st.markdown("""
    <div class='main-title'>🏙️ Bhopal Smart City Intelligence Dashboard</div>
    <div class='sub-title'>AI-powered audit of India's Smart City Mission · 2019–2024</div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    try:
        sc = summaries.get("smart_city", [])
        total_proj = sum(x["count"] for x in sc)
        completed  = next((x["count"] for x in sc if x["status"] == "Completed"), 0)
        completion_pct = round(completed / total_proj * 100) if total_proj else 0
        aqi_data = summaries.get("aqi", [])
        avg_aqi  = round(sum(x["avg_aqi"] for x in aqi_data) / len(aqi_data)) if aqi_data else 0
        hc       = summaries.get("healthcare", [])
        avg_beds = round(sum(x["beds_per_1000"] for x in hc) / len(hc), 2) if hc else 0
        comp     = summaries.get("complaints", [])
        avg_res  = round(sum(x["rate"] for x in comp) / len(comp), 1) if comp else 0

        with col1:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{completion_pct}%</div><div class='metric-label'>Project Completion</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{avg_aqi}</div><div class='metric-label'>Avg City AQI</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{avg_beds}</div><div class='metric-label'>Beds per 1000 Pop</div></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='metric-card'><div class='metric-value'>{avg_res}%</div><div class='metric-label'>Grievance Resolution</div></div>", unsafe_allow_html=True)
    except:
        st.info("Connect to database to see KPIs")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-header'>📈 Monthly AQI Pattern</div>", unsafe_allow_html=True)
        if "monthly_aqi" in chart_data and not chart_data["monthly_aqi"].empty:
            df  = chart_data["monthly_aqi"]
            fig = px.bar(df, x="month_name", y="avg_aqi", color="avg_aqi",
                         color_continuous_scale=["#00b894","#f39c12","#e74c3c"])
            fig.add_hline(y=100, line_dash="dash", line_color="#f39c12", annotation_text="Moderate")
            fig.add_hline(y=200, line_dash="dash", line_color="#e74c3c", annotation_text="Poor")
            fig.update_layout(paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
                              font_color="white", margin=dict(l=10,r=10,t=10,b=10),
                              coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div class='section-header'>🏥 Beds per 1000 by Zone</div>", unsafe_allow_html=True)
        if "zone_beds" in chart_data and not chart_data["zone_beds"].empty:
            df     = chart_data["zone_beds"].sort_values("beds_per_1000")
            colors = ["#e74c3c" if x < df["beds_per_1000"].mean() else "#00b894" for x in df["beds_per_1000"]]
            fig    = go.Figure(go.Bar(x=df["beds_per_1000"], y=df["zone"], orientation="h",
                                      marker_color=colors, text=df["beds_per_1000"], textposition="outside"))
            fig.update_layout(paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
                              font_color="white", margin=dict(l=10,r=10,t=10,b=10),
                              xaxis_title="Beds per 1000 People")
            st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-header'>💧 Lake Dissolved Oxygen Trend</div>", unsafe_allow_html=True)
        if "lake_trend" in chart_data and not chart_data["lake_trend"].empty:
            df  = chart_data["lake_trend"]
            fig = px.line(df, x="year_num", y="avg_do", color="lake_name", markers=True,
                          color_discrete_map={"Upper Lake":"#00b894","Lower Lake":"#e74c3c"})
            fig.add_hline(y=6, line_dash="dash", line_color="orange", annotation_text="Min Safe Level")
            fig.update_layout(paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
                              font_color="white", margin=dict(l=10,r=10,t=10,b=10),
                              legend=dict(bgcolor="#1e2130"))
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("<div class='section-header'>📋 Resolution Rate by Zone</div>", unsafe_allow_html=True)
        if "zone_complaints" in chart_data and not chart_data["zone_complaints"].empty:
            df     = chart_data["zone_complaints"].sort_values("resolution_pct")
            colors = ["#e74c3c" if x < 65 else "#00b894" for x in df["resolution_pct"]]
            fig    = go.Figure(go.Bar(x=df["resolution_pct"], y=df["zone"], orientation="h",
                                      marker_color=colors,
                                      text=[f"{x}%" for x in df["resolution_pct"]],
                                      textposition="outside"))
            fig.add_vline(x=65, line_dash="dash", line_color="orange", annotation_text="Target 65%")
            fig.update_layout(paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
                              font_color="white", margin=dict(l=10,r=10,t=10,b=10),
                              xaxis_title="Resolution Rate %")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    <div style='text-align:center; color:#636e72; font-size:12px; padding:8px; margin-top:8px'>
        🤖 Use <b style='color:#00b894'>AI Chatbot</b> to ask questions ·
        📊 Use <b style='color:#00b894'>AI Insight Generator</b> for auto analysis
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
# PAGE 2 — AI CHATBOT
# ─────────────────────────────────────────
elif page == "🤖 AI Chatbot":
    st.markdown("""
    <div class='main-title'>🤖 AI Data Chatbot</div>
    <div class='sub-title'>Ask anything about Bhopal's Smart City data in plain English</div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='section-header'>💡 Try asking:</div>", unsafe_allow_html=True)

    example_questions = [
        "Which zone has the worst healthcare access?",
        "How does winter AQI compare to monsoon?",
        "Which lake is more polluted and why?",
        "What is the overall Smart City performance score?",
        "Which zone resolves complaints fastest?",
        "What are the top 3 issues Bhopal needs to fix urgently?"
    ]

    cols = st.columns(3)
    for i, q in enumerate(example_questions):
        if cols[i % 3].button(q, key=f"eq_{i}"):
            st.session_state["messages"].append({"role": "user", "content": q})
            st.session_state["pending"] = True

    st.markdown("---")

    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            st.markdown(f"<div class='user-msg'><b>You:</b> {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='ai-msg'><b>🤖 AI Analyst:</b><br>{msg['content']}</div>", unsafe_allow_html=True)

    if st.session_state.get("pending"):
        client = get_ai_client()
        if client:
            with st.spinner("Analyzing data..."):
                response = chat_with_ai(client, st.session_state["messages"], summaries)
            st.session_state["messages"].append({"role": "assistant", "content": response})
            st.session_state["pending"] = False
            st.rerun()
        else:
            st.warning("Please add your Gemini API key in the sidebar.")
            st.session_state["pending"] = False

    user_input = st.chat_input("Ask anything about Bhopal's data...")
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        client = get_ai_client()
        if client:
            with st.spinner("Analyzing data..."):
                response = chat_with_ai(client, st.session_state["messages"], summaries)
            st.session_state["messages"].append({"role": "assistant", "content": response})
            st.rerun()
        else:
            st.warning("Please add your Gemini API key in the sidebar.")

    if st.session_state["messages"]:
        if st.button("🗑️ Clear Chat"):
            st.session_state["messages"] = []
            st.rerun()


# ─────────────────────────────────────────
# PAGE 3 — AI INSIGHT GENERATOR
# ─────────────────────────────────────────
elif page == "📊 AI Insight Generator":
    st.markdown("""
    <div class='main-title'>📊 AI Insight Generator</div>
    <div class='sub-title'>Select any module — AI reads the data and generates a full analysis report</div>
    """, unsafe_allow_html=True)

    modules = [
        "🏛️ Smart City Delivery",
        "🌿 Environment & Lakes",
        "🏥 Healthcare Access",
        "📋 Citizen Grievances"
    ]

    selected = st.selectbox("Select Analysis Module:", modules, label_visibility="collapsed")

    col1, col2 = st.columns([1, 3])
    with col1:
        generate = st.button("✨ Generate AI Insights", use_container_width=True)

    if generate:
        client = get_ai_client()
        if client:
            with st.spinner(f"AI is analyzing {selected} data..."):
                result = generate_insights(client, selected, summaries)

            st.markdown(f"<div class='section-header'>{selected} — AI Analysis Report</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='insight-box'>{result.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-header'>📈 Supporting Data</div>", unsafe_allow_html=True)

            if selected == "🏛️ Smart City Delivery" and "project_status" in chart_data:
                fig = px.pie(chart_data["project_status"], names="status", values="count",
                             hole=0.4, color_discrete_sequence=["#00b894","#f39c12","#e74c3c","#636e72"])
                fig.update_layout(paper_bgcolor="#1e2130", font_color="white", legend=dict(bgcolor="#1e2130"))
                st.plotly_chart(fig, use_container_width=True)

            elif selected == "🌿 Environment & Lakes":
                c1, c2 = st.columns(2)
                with c1:
                    if "monthly_aqi" in chart_data:
                        df  = chart_data["monthly_aqi"]
                        fig = px.bar(df, x="month_name", y="avg_aqi", color="avg_aqi",
                                     color_continuous_scale=["#00b894","#f39c12","#e74c3c"])
                        fig.update_layout(paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
                                          font_color="white", coloraxis_showscale=False)
                        st.plotly_chart(fig, use_container_width=True)
                with c2:
                    if "lake_trend" in chart_data:
                        df  = chart_data["lake_trend"]
                        fig = px.line(df, x="year_num", y="avg_do", color="lake_name", markers=True,
                                      color_discrete_map={"Upper Lake":"#00b894","Lower Lake":"#e74c3c"})
                        fig.add_hline(y=6, line_dash="dash", line_color="orange")
                        fig.update_layout(paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
                                          font_color="white", legend=dict(bgcolor="#1e2130"))
                        st.plotly_chart(fig, use_container_width=True)

            elif selected == "🏥 Healthcare Access" and "zone_beds" in chart_data:
                df     = chart_data["zone_beds"].sort_values("beds_per_1000")
                colors = ["#e74c3c" if x < df["beds_per_1000"].mean() else "#00b894" for x in df["beds_per_1000"]]
                fig    = go.Figure(go.Bar(x=df["beds_per_1000"], y=df["zone"], orientation="h",
                                          marker_color=colors, text=df["beds_per_1000"], textposition="outside"))
                fig.update_layout(paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
                                  font_color="white", xaxis_title="Beds per 1000 People")
                st.plotly_chart(fig, use_container_width=True)

            elif selected == "📋 Citizen Grievances" and "zone_complaints" in chart_data:
                df  = chart_data["zone_complaints"]
                fig = px.bar(df, x="zone", y="resolution_pct", color="resolution_pct",
                             color_continuous_scale=["#e74c3c","#f39c12","#00b894"],
                             text="resolution_pct")
                fig.add_hline(y=65, line_dash="dash", line_color="white", annotation_text="Target 65%")
                fig.update_layout(paper_bgcolor="#1e2130", plot_bgcolor="#1e2130",
                                  font_color="white", coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            st.download_button(
                label="📥 Download Insight Report",
                data=result,
                file_name=f"bhopal_{selected[:4]}_insights.txt",
                mime="text/plain"
            )
        else:
            st.warning("Please add your Gemini API key in the sidebar.")
            st.info("""
            **How to get your free Gemini API key:**
            1. Go to aistudio.google.com
            2. Sign in with Google account
            3. Click Get API Key → Create API Key
            4. Paste it in the sidebar under 🔑 Gemini API Key
            """)