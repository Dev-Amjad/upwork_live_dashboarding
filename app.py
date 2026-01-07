# 🚀 Upwork Jobs - Live Dashboard
# Production-ready Streamlit app with real-time updates

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import numpy as np
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🚀 Upwork Live Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== STYLING ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
    }
    .live-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #e74c3c;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .whale-alert {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .stDataFrame {
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== COLORS ====================
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'success': '#27AE60',
    'warning': '#F18F01',
    'danger': '#C73E1D',
    'info': '#3498DB',
    'platinum': '#9B59B6',
    'gold': '#F1C40F',
    'silver': '#BDC3C7',
    'bronze': '#E67E22',
    'standard': '#95A5A6'
}

TIER_COLORS = {
    '💎 Platinum': COLORS['platinum'],
    '🥇 Gold': COLORS['gold'],
    '🥈 Silver': COLORS['silver'],
    '🥉 Bronze': COLORS['bronze'],
    '📦 Standard': COLORS['standard']
}

LEAD_COLORS = {
    '🔥 TOP 5%': COLORS['danger'],
    '⭐ TOP 20%': COLORS['warning'],
    '📋 STANDARD': COLORS['standard']
}

# ==================== DATABASE ====================
@st.cache_resource
def get_engine():
    """Create database connection (cached)"""
    # Priority: 1. Streamlit secrets (cloud) 2. Environment variables (local/docker)
    db_url = None

    # Try Streamlit secrets first (for Streamlit Cloud deployment)
    try:
        db_url = st.secrets["DATABASE_URL"]
    except:
        pass

    # Fall back to environment variables
    if not db_url:
        db_url = os.getenv("DATABASE_URL")

    # Raise error if no configuration found
    if not db_url:
        raise ValueError(
            "DATABASE_URL not found! Please set it in:\n"
            "- .env file for local development\n"
            "- Streamlit secrets for cloud deployment\n"
            "- Environment variables for Docker/production"
        )

    return create_engine(db_url)

def load_data():
    """Load fresh data from database (NO CACHE - always fresh)"""
    engine = get_engine()
    
    # Load jobs
    jobs_df = pd.read_sql("SELECT * FROM leads_job ORDER BY posted_at DESC", engine)
    
    # Load scanners
    scanners_df = pd.read_sql("SELECT * FROM leads_scanner", engine)
    
    return jobs_df, scanners_df

def process_data(jobs_df):
    """Process and calculate all metrics"""
    df = jobs_df.copy()
    
    # Extract client info from JSON
    def extract_client(row):
        ci = row['client_info']
        default = {'client_country': None, 'client_total_spent': 0, 'client_total_hires': 0}
        if ci is None:
            return pd.Series(default)
        if isinstance(ci, str):
            try:
                ci = json.loads(ci)
            except:
                return pd.Series(default)
        return pd.Series({
            'client_country': ci.get('country'),
            'client_total_spent': float(ci.get('total_spent', 0) or 0),
            'client_total_hires': int(ci.get('total_hires', 0) or 0)
        })
    
    client_data = df.apply(extract_client, axis=1)
    df = pd.concat([df, client_data], axis=1)
    
    # Budget calculations
    df['budget'] = pd.to_numeric(df['budget'], errors='coerce').fillna(0)
    df['hourly_budget_min'] = pd.to_numeric(df['hourly_budget_min'], errors='coerce').fillna(0)
    df['hourly_budget_max'] = pd.to_numeric(df['hourly_budget_max'], errors='coerce').fillna(0)
    df['is_hourly'] = df['budget_type'].str.lower().str.contains('hourly', na=False)
    df['is_fixed'] = ~df['is_hourly']
    df['effective_budget'] = np.where(df['is_hourly'], df['hourly_budget_max'], df['budget'])
    df['posted_at'] = pd.to_datetime(df['posted_at'], errors='coerce')
    
    # Q Score (Client Quality)
    df['avg_spend_per_hire'] = df['client_total_spent'] / (df['client_total_hires'] + 1)
    df['quality_score_Q'] = np.log(df['avg_spend_per_hire'] + 1)
    
    # Client Tiers
    q_pct = df['quality_score_Q'].quantile([0.5, 0.75, 0.9, 0.95])
    def get_tier(q):
        if q >= q_pct[0.95]: return '💎 Platinum'
        elif q >= q_pct[0.9]: return '🥇 Gold'
        elif q >= q_pct[0.75]: return '🥈 Silver'
        elif q >= q_pct[0.5]: return '🥉 Bronze'
        else: return '📦 Standard'
    df['client_tier'] = df['quality_score_Q'].apply(get_tier)
    
    # Scanner stats for Z-score
    scanner_stats = df.groupby('scanner_id')['effective_budget'].agg(['mean', 'std']).reset_index()
    scanner_stats.columns = ['scanner_id', 'niche_mean', 'niche_std']
    scanner_stats['niche_std'] = scanner_stats['niche_std'].fillna(1).replace(0, 1)
    df = df.merge(scanner_stats, on='scanner_id', how='left')
    
    # Z-Score
    df['z_score'] = (df['effective_budget'] - df['niche_mean']) / df['niche_std']
    df['z_score'] = df['z_score'].fillna(0)
    
    # RMS Score
    fixed_median = df[df['is_fixed'] & (df['budget'] > 0)]['budget'].median() or 1
    hourly_median = df[df['is_hourly'] & (df['hourly_budget_max'] > 0)]['hourly_budget_max'].median() or 1
    
    def calc_rms(row):
        if row['is_fixed']:
            return row['budget'] / fixed_median if row['budget'] > 0 else 0
        else:
            if row['hourly_budget_max'] > 0:
                base = row['hourly_budget_max'] / hourly_median
                spread_bonus = 1 + (row['hourly_budget_max'] - row['hourly_budget_min']) / row['hourly_budget_max']
                return base * spread_bonus
            return 0
    
    df['rms_score'] = df.apply(calc_rms, axis=1)
    
    # Unified Lead Score
    df['unified_score'] = df['quality_score_Q'] * df['rms_score'] * (1 + np.maximum(0, df['z_score']))
    df['unified_score'] = df['unified_score'].replace([np.inf, -np.inf], np.nan).fillna(0)
    max_score = df['unified_score'].quantile(0.99) or 1
    df['score_normalized'] = (df['unified_score'] / max_score * 100).clip(0, 100)
    
    # Lead Tiers
    p95 = df['score_normalized'].quantile(0.95)
    p80 = df['score_normalized'].quantile(0.80)
    def get_lead_tier(s):
        if s >= p95: return '🔥 TOP 5%'
        elif s >= p80: return '⭐ TOP 20%'
        else: return '📋 STANDARD'
    df['lead_tier'] = df['score_normalized'].apply(get_lead_tier)
    
    # Outlier Class
    def get_outlier_class(z):
        if z >= 3: return '🐋 Whale'
        elif z >= 2: return '🐠 Big Fish'
        elif z >= 1: return '🐟 Above Avg'
        elif z >= -1: return '➡️ Average'
        else: return '🦐 Below Avg'
    df['outlier_class'] = df['z_score'].apply(get_outlier_class)
    
    return df

# ==================== AUTO REFRESH ====================
# Refresh interval in seconds
REFRESH_INTERVAL = 60

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

time_since_refresh = time.time() - st.session_state.last_refresh

# Auto-rerun if refresh interval passed
if time_since_refresh > REFRESH_INTERVAL:
    st.session_state.last_refresh = time.time()
    st.rerun()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("🎛️ Dashboard Controls")
    
    # Refresh controls
    st.subheader("🔄 Refresh")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.session_state.last_refresh = time.time()
            st.rerun()
    
    with col2:
        refresh_interval = st.selectbox(
            "Interval",
            options=[30, 60, 120, 300],
            index=1,
            format_func=lambda x: f"{x}s"
        )
        REFRESH_INTERVAL = refresh_interval
    
    # Refresh status
    next_refresh = max(0, REFRESH_INTERVAL - int(time_since_refresh))
    st.progress(1 - (next_refresh / REFRESH_INTERVAL))
    st.caption(f"Next refresh in {next_refresh}s")
    
    st.markdown("---")

# ==================== LOAD DATA ====================
with st.spinner("📊 Loading fresh data..."):
    raw_jobs, scanners_df = load_data()
    jobs_df = process_data(raw_jobs)

# ==================== SIDEBAR FILTERS ====================
with st.sidebar:
    st.subheader("🔍 Filters")
    
    # Client Tier Filter
    all_tiers = ['All'] + list(jobs_df['client_tier'].unique())
    selected_tier = st.selectbox("Client Tier", all_tiers)
    
    # Lead Priority Filter
    all_leads = ['All'] + list(jobs_df['lead_tier'].unique())
    selected_lead = st.selectbox("Lead Priority", all_leads)
    
    # Outlier Class Filter
    all_outliers = ['All'] + list(jobs_df['outlier_class'].unique())
    selected_outlier = st.selectbox("Outlier Class", all_outliers)
    
    # Budget Range Filter
    min_budget = int(jobs_df['effective_budget'].min())
    max_budget = int(jobs_df['effective_budget'].max())
    budget_range = st.slider(
        "Budget Range ($)",
        min_value=min_budget,
        max_value=min(max_budget, 50000),
        value=(min_budget, min(max_budget, 50000))
    )
    
    # Date Range Filter
    st.subheader("📅 Date Range")
    min_date = jobs_df['posted_at'].min().date()
    max_date = jobs_df['posted_at'].max().date()
    date_range = st.date_input(
        "Select Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    st.markdown("---")
    st.caption(f"📊 Data: {len(jobs_df):,} jobs | {len(scanners_df)} scanners")

# ==================== APPLY FILTERS ====================
filtered_df = jobs_df.copy()

if selected_tier != 'All':
    filtered_df = filtered_df[filtered_df['client_tier'] == selected_tier]

if selected_lead != 'All':
    filtered_df = filtered_df[filtered_df['lead_tier'] == selected_lead]

if selected_outlier != 'All':
    filtered_df = filtered_df[filtered_df['outlier_class'] == selected_outlier]

filtered_df = filtered_df[
    (filtered_df['effective_budget'] >= budget_range[0]) &
    (filtered_df['effective_budget'] <= budget_range[1])
]

if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['posted_at'].dt.date >= date_range[0]) &
        (filtered_df['posted_at'].dt.date <= date_range[1])
    ]

# ==================== HEADER ====================
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <span class="live-indicator"></span>
    <span class="main-header">Upwork Jobs - Live Dashboard</span>
</div>
""", unsafe_allow_html=True)

st.caption(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Showing {len(filtered_df):,} of {len(jobs_df):,} jobs")

# ==================== ALERTS ====================
# Check for new whales in last 10 minutes
recent_whales = filtered_df[
    (filtered_df['z_score'] >= 3) & 
    (filtered_df['posted_at'] > datetime.now() - timedelta(minutes=10))
]

if len(recent_whales) > 0:
    st.error(f"🚨 **WHALE ALERT: {len(recent_whales)} new exceptional job(s) in the last 10 minutes!**")
    for _, whale in recent_whales.head(3).iterrows():
        st.markdown(f"""
        <div class="whale-alert">
            <strong>🐋 {whale['title'][:70]}...</strong><br>
            💰 Budget: <strong>${whale['effective_budget']:,.0f}</strong> | 
            📊 Z-Score: <strong>{whale['z_score']:.1f}</strong> |
            🏷️ {whale['client_tier']}
        </div>
        """, unsafe_allow_html=True)

# ==================== KPIs ====================
today = datetime.now().date()
yesterday = today - timedelta(days=1)
jobs_today = len(filtered_df[filtered_df['posted_at'].dt.date == today])
jobs_yesterday = len(filtered_df[filtered_df['posted_at'].dt.date == yesterday])
delta_jobs = jobs_today - jobs_yesterday

top5_count = len(filtered_df[filtered_df['lead_tier'] == '🔥 TOP 5%'])
whale_count = len(filtered_df[filtered_df['z_score'] >= 3])

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="📊 Total Jobs",
        value=f"{len(filtered_df):,}",
        delta=f"+{jobs_today} today"
    )

with col2:
    st.metric(
        label="💰 Total Value",
        value=f"${filtered_df['effective_budget'].sum():,.0f}"
    )

with col3:
    st.metric(
        label="📈 Avg Budget",
        value=f"${filtered_df['effective_budget'].mean():,.0f}"
    )

with col4:
    st.metric(
        label="🔥 Top 5% Leads",
        value=f"{top5_count:,}"
    )

with col5:
    st.metric(
        label="🐋 Whales",
        value=f"{whale_count:,}"
    )

st.markdown("---")

# ==================== CHARTS ROW 1 ====================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🏆 Client Tier Distribution")
    tier_counts = filtered_df['client_tier'].value_counts()
    
    fig = px.pie(
        values=tier_counts.values,
        names=tier_counts.index,
        color=tier_counts.index,
        color_discrete_map=TIER_COLORS,
        hole=0.4
    )
    fig.update_layout(
        height=350,
        margin=dict(t=20, b=20, l=20, r=20),
        legend=dict(orientation='h', yanchor='bottom', y=-0.2)
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)
    
    # Click to filter
    if st.checkbox("Show Tier Details", key="tier_details"):
        selected_tier_detail = st.selectbox("Select Tier", tier_counts.index.tolist(), key="tier_select")
        tier_jobs = filtered_df[filtered_df['client_tier'] == selected_tier_detail]
        st.dataframe(
            tier_jobs[['title', 'effective_budget', 'client_country', 'quality_score_Q']].head(10),
            use_container_width=True,
            hide_index=True
        )

with col_right:
    st.subheader("🎯 Lead Priority Distribution")
    lead_counts = filtered_df['lead_tier'].value_counts()
    
    fig = px.bar(
        x=lead_counts.index,
        y=lead_counts.values,
        color=lead_counts.index,
        color_discrete_map=LEAD_COLORS,
        text=lead_counts.values
    )
    fig.update_layout(
        height=350,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
        xaxis_title="",
        yaxis_title="Count"
    )
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
    
    # Click to filter
    if st.checkbox("Show Lead Details", key="lead_details"):
        selected_lead_detail = st.selectbox("Select Priority", lead_counts.index.tolist(), key="lead_select")
        lead_jobs = filtered_df[filtered_df['lead_tier'] == selected_lead_detail]
        st.dataframe(
            lead_jobs[['title', 'effective_budget', 'client_tier', 'score_normalized']].head(10),
            use_container_width=True,
            hide_index=True
        )

st.markdown("---")

# ==================== CHARTS ROW 2 ====================
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("🐋 Outlier Classification")
    outlier_counts = filtered_df['outlier_class'].value_counts()
    outlier_order = ['🐋 Whale', '🐠 Big Fish', '🐟 Above Avg', '➡️ Average', '🦐 Below Avg']
    outlier_counts = outlier_counts.reindex([o for o in outlier_order if o in outlier_counts.index])
    
    fig = go.Figure(go.Funnel(
        y=outlier_counts.index,
        x=outlier_counts.values,
        textinfo="value+percent total",
        marker_color=[COLORS['platinum'], COLORS['primary'], COLORS['success'], COLORS['standard'], COLORS['silver']][:len(outlier_counts)]
    ))
    fig.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)
    
    # Click to filter
    if st.checkbox("Show Outlier Details", key="outlier_details"):
        selected_outlier_detail = st.selectbox("Select Class", outlier_counts.index.tolist(), key="outlier_select")
        outlier_jobs = filtered_df[filtered_df['outlier_class'] == selected_outlier_detail]
        st.dataframe(
            outlier_jobs[['title', 'effective_budget', 'z_score', 'client_tier']].head(10),
            use_container_width=True,
            hide_index=True
        )

with col_right2:
    st.subheader("📊 Budget Distribution")
    
    fig = px.histogram(
        filtered_df[filtered_df['effective_budget'] > 0],
        x='effective_budget',
        nbins=50,
        color_discrete_sequence=[COLORS['primary']]
    )
    
    median_budget = filtered_df['effective_budget'].median()
    fig.add_vline(x=median_budget, line_dash="dash", line_color=COLORS['danger'],
                  annotation_text=f"Median: ${median_budget:,.0f}")
    
    fig.update_layout(
        height=350,
        margin=dict(t=20, b=20, l=20, r=20),
        xaxis_title="Budget ($)",
        yaxis_title="Count",
        xaxis_range=[0, filtered_df['effective_budget'].quantile(0.95)]
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==================== LIVE FEED ====================
st.subheader("📡 Live Job Feed (Most Recent)")

recent_jobs = filtered_df.nlargest(15, 'posted_at').copy()
recent_jobs['posted_at'] = recent_jobs['posted_at'].dt.strftime('%m/%d %H:%M')
recent_jobs['effective_budget'] = recent_jobs['effective_budget'].apply(lambda x: f"${x:,.0f}")
recent_jobs['score_normalized'] = recent_jobs['score_normalized'].apply(lambda x: f"{x:.1f}")
recent_jobs['z_score'] = recent_jobs['z_score'].apply(lambda x: f"{x:.2f}")

display_cols = ['title', 'effective_budget', 'client_tier', 'lead_tier', 'z_score', 'score_normalized', 'posted_at']
recent_jobs = recent_jobs[display_cols]
recent_jobs.columns = ['Title', 'Budget', 'Client Tier', 'Priority', 'Z-Score', 'Score', 'Posted']

st.dataframe(recent_jobs, use_container_width=True, hide_index=True, height=400)

st.markdown("---")

# ==================== TOP LEADS ====================
st.subheader("🏆 Top 20 Leads (Highest Score)")

top_leads = filtered_df.nlargest(20, 'score_normalized').copy()
top_leads['effective_budget'] = top_leads['effective_budget'].apply(lambda x: f"${x:,.0f}")
top_leads['score_normalized'] = top_leads['score_normalized'].apply(lambda x: f"{x:.1f}")
top_leads['z_score'] = top_leads['z_score'].apply(lambda x: f"{x:.2f}")
top_leads['quality_score_Q'] = top_leads['quality_score_Q'].apply(lambda x: f"{x:.2f}")

display_cols = ['title', 'effective_budget', 'client_tier', 'z_score', 'score_normalized', 'lead_tier', 'client_country']
top_leads = top_leads[display_cols]
top_leads.columns = ['Title', 'Budget', 'Client Tier', 'Z-Score', 'Score', 'Priority', 'Country']

st.dataframe(top_leads, use_container_width=True, hide_index=True, height=500)

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🚀 <strong>Upwork Jobs Live Dashboard</strong> | Auto-refreshes every 60 seconds</p>
    <p>Built with Streamlit | Data from PostgreSQL</p>
</div>
""", unsafe_allow_html=True)
