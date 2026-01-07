# 🚀 Upwork Jobs Analytics - Executive Dashboard
# Enhanced Version with Fixed Styling & Compact Layout

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import json
import time

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🚀 Upwork Analytics",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== FIXED CSS - DARK THEME COMPATIBLE ====================
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Reduce padding */
    .main .block-container {
        padding: 1rem 2rem 2rem 2rem;
        max-width: 100%;
    }
    
    /* Section Headers */
    .section-header {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 1.5rem 0 0.5rem 0;
        padding: 0;
    }
    
    /* Insight Boxes - FIXED FOR DARK THEME */
    .insight-box {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-left: 4px solid #6366f1;
        padding: 1rem 1.2rem;
        margin: 1rem 0;
        border-radius: 0 10px 10px 0;
        color: #e2e8f0 !important;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    .insight-box h4 {
        color: #a5b4fc !important;
        margin: 0 0 0.5rem 0;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .insight-box p, .insight-box li, .insight-box span {
        color: #cbd5e1 !important;
    }
    
    .insight-box strong {
        color: #f1f5f9 !important;
    }
    
    .insight-box ul {
        margin: 0.5rem 0;
        padding-left: 1.2rem;
    }
    
    .insight-box li {
        margin: 0.3rem 0;
    }
    
    /* Formula Box - FIXED */
    .formula-box {
        background: #0f172a;
        border: 1px solid #334155;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 0.85rem;
        margin: 0.5rem 0;
        color: #22d3ee !important;
    }
    
    /* Data Tables - FIXED */
    .tier-table {
        width: 100%;
        border-collapse: collapse;
        margin: 0.5rem 0;
        font-size: 0.85rem;
    }
    
    .tier-table th {
        background: #1e293b;
        color: #a5b4fc !important;
        padding: 0.5rem;
        text-align: left;
        border-bottom: 2px solid #4f46e5;
    }
    
    .tier-table td {
        padding: 0.5rem;
        border-bottom: 1px solid #334155;
        color: #cbd5e1 !important;
    }
    
    .tier-table tr:hover {
        background: #1e293b;
    }
    
    /* KPI Cards */
    .kpi-container {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .kpi-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.2);
    }
    
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0;
    }
    
    .kpi-label {
        font-size: 0.8rem;
        color: #94a3b8;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Live Badge */
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: linear-gradient(90deg, #dc2626, #ef4444);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        color: white;
        animation: pulse-badge 2s infinite;
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: white;
        border-radius: 50%;
        animation: pulse-dot 1.5s infinite;
    }
    
    @keyframes pulse-badge {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    @keyframes pulse-dot {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
    }
    
    /* Metric styling override */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #1e293b !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background: #1e293b;
        border-color: #334155;
    }
    
    /* DataFrame styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Plotly chart container */
    .stPlotlyChart {
        background: transparent !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #1e293b;
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        color: #94a3b8;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        color: white !important;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #334155, transparent);
        margin: 1.5rem 0;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e293b;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4f46e5;
        border-radius: 4px;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }
    
    /* Compact section intro */
    .section-intro {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== COLORS ====================
COLORS = {
    'primary': '#6366f1',
    'secondary': '#8b5cf6',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'info': '#3b82f6',
    'platinum': '#a855f7',
    'gold': '#eab308',
    'silver': '#94a3b8',
    'bronze': '#f97316',
    'standard': '#64748b'
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

OUTLIER_COLORS = {
    '🐋 Whale': COLORS['platinum'],
    '🐠 Big Fish': COLORS['primary'],
    '🐟 Above Avg': COLORS['success'],
    '➡️ Average': COLORS['standard'],
    '🦐 Below Avg': COLORS['silver']
}

# ==================== PLOTLY TEMPLATE ====================
PLOT_TEMPLATE = {
    'layout': {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': '#e2e8f0', 'family': 'Inter'},
        'title': {'font': {'color': '#f1f5f9', 'size': 16}},
        'xaxis': {
            'gridcolor': '#334155',
            'linecolor': '#334155',
            'tickfont': {'color': '#94a3b8'}
        },
        'yaxis': {
            'gridcolor': '#334155',
            'linecolor': '#334155',
            'tickfont': {'color': '#94a3b8'}
        },
        'legend': {'font': {'color': '#e2e8f0'}},
        'margin': {'t': 40, 'b': 40, 'l': 40, 'r': 40}
    }
}

def apply_chart_styling(fig, height=350):
    """Apply consistent dark theme styling to charts"""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0', family='Inter'),
        height=height,
        margin=dict(t=40, b=40, l=50, r=30),
        legend=dict(
            bgcolor='rgba(30,41,59,0.8)',
            bordercolor='#334155',
            font=dict(color='#e2e8f0')
        ),
        hoverlabel=dict(
            bgcolor='#1e293b',
            font_size=12,
            font_family='Inter'
        )
    )
    fig.update_xaxes(
        gridcolor='#334155',
        linecolor='#475569',
        tickfont=dict(color='#94a3b8'),
        title_font=dict(color='#cbd5e1')
    )
    fig.update_yaxes(
        gridcolor='#334155',
        linecolor='#475569',
        tickfont=dict(color='#94a3b8'),
        title_font=dict(color='#cbd5e1')
    )
    return fig

# ==================== DATABASE ====================
@st.cache_resource
def get_engine():
    try:
        db_url = st.secrets["DATABASE_URL"]
    except:
        db_url = "postgresql://analytics_user:Rahnuma824630*@46.62.227.215:54321/postgres"
    return create_engine(db_url)

@st.cache_data(ttl=60)
def load_data():
    engine = get_engine()
    jobs_df = pd.read_sql("SELECT * FROM leads_job ORDER BY posted_at DESC", engine)
    scanners_df = pd.read_sql("SELECT * FROM leads_scanner", engine)
    return jobs_df, scanners_df

def process_data(jobs_df, scanners_df):
    df = jobs_df.copy()
    
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
    
    df['budget'] = pd.to_numeric(df['budget'], errors='coerce').fillna(0)
    df['hourly_budget_min'] = pd.to_numeric(df['hourly_budget_min'], errors='coerce').fillna(0)
    df['hourly_budget_max'] = pd.to_numeric(df['hourly_budget_max'], errors='coerce').fillna(0)
    df['is_hourly'] = df['budget_type'].str.lower().str.contains('hourly', na=False)
    df['is_fixed'] = ~df['is_hourly']
    df['effective_budget'] = np.where(df['is_hourly'], df['hourly_budget_max'], df['budget'])
    df['posted_at'] = pd.to_datetime(df['posted_at'], errors='coerce')
    
    df['avg_spend_per_hire'] = df['client_total_spent'] / (df['client_total_hires'] + 1)
    df['quality_score_Q'] = np.log(df['avg_spend_per_hire'] + 1)
    
    q_pct = df['quality_score_Q'].quantile([0.5, 0.75, 0.9, 0.95])
    def get_tier(q):
        if q >= q_pct[0.95]: return '💎 Platinum'
        elif q >= q_pct[0.9]: return '🥇 Gold'
        elif q >= q_pct[0.75]: return '🥈 Silver'
        elif q >= q_pct[0.5]: return '🥉 Bronze'
        else: return '📦 Standard'
    df['client_tier'] = df['quality_score_Q'].apply(get_tier)
    
    scanner_stats = df.groupby('scanner_id')['effective_budget'].agg(['mean', 'std', 'count', 'sum']).reset_index()
    scanner_stats.columns = ['scanner_id', 'niche_mean', 'niche_std', 'job_count', 'total_value']
    scanner_stats['niche_std'] = scanner_stats['niche_std'].fillna(1).replace(0, 1)
    scanner_stats = scanner_stats.merge(scanners_df[['id', 'name']], left_on='scanner_id', right_on='id', how='left')
    df = df.merge(scanner_stats[['scanner_id', 'niche_mean', 'niche_std']], on='scanner_id', how='left')
    
    df['z_score'] = (df['effective_budget'] - df['niche_mean']) / df['niche_std']
    df['z_score'] = df['z_score'].fillna(0)
    
    def get_outlier_class(z):
        if z >= 3: return '🐋 Whale'
        elif z >= 2: return '🐠 Big Fish'
        elif z >= 1: return '🐟 Above Avg'
        elif z >= -1: return '➡️ Average'
        else: return '🦐 Below Avg'
    df['outlier_class'] = df['z_score'].apply(get_outlier_class)
    
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
    df['unified_score'] = df['quality_score_Q'] * df['rms_score'] * (1 + np.maximum(0, df['z_score']))
    df['unified_score'] = df['unified_score'].replace([np.inf, -np.inf], np.nan).fillna(0)
    max_score = df['unified_score'].quantile(0.99) or 1
    df['score_normalized'] = (df['unified_score'] / max_score * 100).clip(0, 100)
    
    p95 = df['score_normalized'].quantile(0.95)
    p80 = df['score_normalized'].quantile(0.80)
    def get_lead_tier(s):
        if s >= p95: return '🔥 TOP 5%'
        elif s >= p80: return '⭐ TOP 20%'
        else: return '📋 STANDARD'
    df['lead_tier'] = df['score_normalized'].apply(get_lead_tier)
    
    return df, scanner_stats, fixed_median, hourly_median

def show_records_table(df, max_rows=15):
    """Display a compact formatted table"""
    if len(df) == 0:
        st.info("No records found")
        return
        
    display_df = df.head(max_rows).copy()
    
    cols_to_show = ['title', 'effective_budget', 'client_tier', 'lead_tier', 'z_score', 'score_normalized']
    cols_available = [c for c in cols_to_show if c in display_df.columns]
    display_df = display_df[cols_available]
    
    if 'title' in display_df.columns:
        display_df['title'] = display_df['title'].str[:40] + '...'
    if 'effective_budget' in display_df.columns:
        display_df['effective_budget'] = display_df['effective_budget'].apply(lambda x: f"${x:,.0f}")
    if 'z_score' in display_df.columns:
        display_df['z_score'] = display_df['z_score'].apply(lambda x: f"{x:.1f}")
    if 'score_normalized' in display_df.columns:
        display_df['score_normalized'] = display_df['score_normalized'].apply(lambda x: f"{x:.0f}")
    
    col_names = {
        'title': 'Title', 'effective_budget': 'Budget', 'client_tier': 'Tier',
        'lead_tier': 'Priority', 'z_score': 'Z', 'score_normalized': 'Score'
    }
    display_df.columns = [col_names.get(c, c) for c in display_df.columns]
    
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=min(400, 35 * len(display_df) + 38))

# ==================== LOAD DATA ====================
with st.spinner("🔄 Loading data..."):
    raw_jobs, scanners_df = load_data()
    jobs_df, scanner_stats, fixed_median, hourly_median = process_data(raw_jobs, scanners_df)

# ==================== HEADER ====================
col_title, col_live, col_refresh = st.columns([6, 1, 1])

with col_title:
    st.markdown("# 🚀 Upwork Analytics Dashboard")
    
with col_live:
    st.markdown("""
    <div class="live-badge">
        <span class="live-dot"></span>
        LIVE
    </div>
    """, unsafe_allow_html=True)

with col_refresh:
    if st.button("🔄", help="Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# Data period info
date_min = jobs_df['posted_at'].min()
date_max = jobs_df['posted_at'].max()
st.caption(f"📅 {date_min.strftime('%b %d')} - {date_max.strftime('%b %d, %Y')} • {len(jobs_df):,} jobs • {len(scanners_df)} scanners")

st.markdown("---")

# ==================== KPI ROW ====================
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

with kpi1:
    st.metric("📊 Total Jobs", f"{len(jobs_df):,}")
with kpi2:
    st.metric("💰 Market Value", f"${jobs_df['effective_budget'].sum()/1e6:.1f}M")
with kpi3:
    st.metric("📈 Avg Budget", f"${jobs_df['effective_budget'].mean():,.0f}")
with kpi4:
    st.metric("🔥 Top 5%", f"{len(jobs_df[jobs_df['lead_tier'] == '🔥 TOP 5%']):,}")
with kpi5:
    st.metric("🐋 Whales", f"{len(jobs_df[jobs_df['z_score'] >= 3]):,}")
with kpi6:
    st.metric("🐠 Big Fish", f"{len(jobs_df[(jobs_df['z_score'] >= 2) & (jobs_df['z_score'] < 3)]):,}")

st.markdown("---")

# ==================== SECTION 1: OVERVIEW ====================
st.markdown('<p class="section-header">📊 Overview: Job Types & Client Quality</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Job Type Pie
    fixed_count = jobs_df['is_fixed'].sum()
    hourly_count = jobs_df['is_hourly'].sum()
    
    fig = go.Figure(data=[go.Pie(
        labels=['Fixed Price', 'Hourly'],
        values=[fixed_count, hourly_count],
        hole=0.6,
        marker_colors=[COLORS['primary'], COLORS['warning']],
        textinfo='percent',
        textfont=dict(color='white', size=14),
        hovertemplate='<b>%{label}</b><br>Count: %{value:,}<br>%{percent}<extra></extra>'
    )])
    
    fig.add_annotation(
        text=f"<b>{len(jobs_df):,}</b><br>Jobs",
        x=0.5, y=0.5, font=dict(size=16, color='#e2e8f0'),
        showarrow=False
    )
    
    fig.update_layout(
        title=dict(text="💼 Job Type Distribution", font=dict(size=14, color='#f1f5f9')),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5)
    )
    fig = apply_chart_styling(fig, height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    # Interactive filter
    with st.expander("🔍 View Job Records by Type"):
        job_type = st.radio("Select:", ['Fixed Price', 'Hourly'], horizontal=True, key='jt1')
        filtered = jobs_df[jobs_df['is_fixed']] if job_type == 'Fixed Price' else jobs_df[jobs_df['is_hourly']]
        st.caption(f"Showing {len(filtered):,} {job_type} jobs")
        show_records_table(filtered.sort_values('effective_budget', ascending=False))

with col2:
    # Client Tier Bar
    tier_order = ['💎 Platinum', '🥇 Gold', '🥈 Silver', '🥉 Bronze', '📦 Standard']
    tier_counts = jobs_df['client_tier'].value_counts().reindex(tier_order).fillna(0)
    
    fig = go.Figure(data=[go.Bar(
        x=tier_counts.values,
        y=tier_order,
        orientation='h',
        marker_color=[TIER_COLORS.get(t) for t in tier_order],
        text=[f'{int(v):,}' for v in tier_counts.values],
        textposition='outside',
        textfont=dict(color='#e2e8f0'),
        hovertemplate='<b>%{y}</b><br>Jobs: %{x:,}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(text="🏆 Client Quality Tiers", font=dict(size=14, color='#f1f5f9')),
        xaxis_title="Number of Jobs",
        yaxis=dict(categoryorder='array', categoryarray=tier_order[::-1])
    )
    fig = apply_chart_styling(fig, height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("🔍 View Jobs by Client Tier"):
        tier = st.selectbox("Select Tier:", tier_order, key='tier1')
        filtered = jobs_df[jobs_df['client_tier'] == tier]
        c1, c2, c3 = st.columns(3)
        c1.metric("Jobs", f"{len(filtered):,}")
        c2.metric("Avg Budget", f"${filtered['effective_budget'].mean():,.0f}")
        c3.metric("Avg Spent", f"${filtered['client_total_spent'].mean():,.0f}")
        show_records_table(filtered.sort_values('effective_budget', ascending=False))

# Insight Box
st.markdown("""
<div class="insight-box">
    <h4>💡 Key Insights</h4>
    <ul>
        <li><strong>Fixed Price dominates</strong> — ~67% of clients prefer fixed budgets (easier to close deals)</li>
        <li><strong>Client Tiers</strong> — Based on spend-per-hire: 💎 Platinum (top 5%) are your priority targets</li>
        <li><strong>Strategy</strong> — Focus on Platinum/Gold clients with fixed-price jobs for best ROI</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==================== SECTION 2: BUDGET ANALYSIS ====================
st.markdown('<p class="section-header">💰 Budget Analysis</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    fixed_jobs = jobs_df[jobs_df['is_fixed'] & (jobs_df['budget'] > 0)]
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=fixed_jobs['budget'].clip(upper=5000),
        nbinsx=40,
        marker_color=COLORS['primary'],
        opacity=0.8,
        hovertemplate='Budget: $%{x:,.0f}<br>Count: %{y}<extra></extra>'
    ))
    
    median_val = fixed_jobs['budget'].median()
    fig.add_vline(x=median_val, line_dash='dash', line_color=COLORS['danger'],
                  annotation_text=f'Median: ${median_val:,.0f}',
                  annotation_font_color='#f1f5f9')
    
    fig.update_layout(
        title=dict(text=f"📊 Fixed Price Distribution (n={len(fixed_jobs):,})", font=dict(size=14, color='#f1f5f9')),
        xaxis_title="Budget ($)",
        yaxis_title="Jobs"
    )
    fig = apply_chart_styling(fig, height=280)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    hourly_jobs = jobs_df[jobs_df['is_hourly'] & (jobs_df['hourly_budget_max'] > 0)]
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=hourly_jobs['hourly_budget_max'].clip(upper=150),
        nbinsx=30,
        marker_color=COLORS['warning'],
        opacity=0.8,
        hovertemplate='Rate: $%{x:.0f}/hr<br>Count: %{y}<extra></extra>'
    ))
    
    median_val = hourly_jobs['hourly_budget_max'].median()
    fig.add_vline(x=median_val, line_dash='dash', line_color=COLORS['danger'],
                  annotation_text=f'Median: ${median_val:.0f}/hr',
                  annotation_font_color='#f1f5f9')
    
    fig.update_layout(
        title=dict(text=f"⏰ Hourly Rate Distribution (n={len(hourly_jobs):,})", font=dict(size=14, color='#f1f5f9')),
        xaxis_title="Max Hourly Rate ($/hr)",
        yaxis_title="Jobs"
    )
    fig = apply_chart_styling(fig, height=280)
    st.plotly_chart(fig, use_container_width=True)

# Budget Range Filter
with st.expander("🔍 Filter Jobs by Budget Range"):
    budget_type = st.radio("Type:", ['Fixed', 'Hourly'], horizontal=True, key='bt1')
    
    if budget_type == 'Fixed':
        ranges = ['$0-$100', '$100-$500', '$500-$2,000', '$2,000-$10,000', '$10,000+']
        selected_range = st.select_slider("Budget Range:", options=ranges, value='$100-$500')
        
        range_map = {
            '$0-$100': (0, 100), '$100-$500': (100, 500), '$500-$2,000': (500, 2000),
            '$2,000-$10,000': (2000, 10000), '$10,000+': (10000, float('inf'))
        }
        low, high = range_map[selected_range]
        filtered = fixed_jobs[(fixed_jobs['budget'] >= low) & (fixed_jobs['budget'] < high)]
    else:
        ranges = ['$0-$25/hr', '$25-$50/hr', '$50-$100/hr', '$100+/hr']
        selected_range = st.select_slider("Rate Range:", options=ranges, value='$25-$50/hr')
        
        range_map = {'$0-$25/hr': (0, 25), '$25-$50/hr': (25, 50), '$50-$100/hr': (50, 100), '$100+/hr': (100, float('inf'))}
        low, high = range_map[selected_range]
        filtered = hourly_jobs[(hourly_jobs['hourly_budget_max'] >= low) & (hourly_jobs['hourly_budget_max'] < high)]
    
    st.caption(f"Found {len(filtered):,} jobs in range {selected_range}")
    show_records_table(filtered.sort_values('effective_budget', ascending=False))

st.markdown("""
<div class="insight-box">
    <h4>💡 Budget Insights</h4>
    <ul>
        <li><strong>Fixed Price Median:</strong> ~$150 — Jobs above $500 are top 25%</li>
        <li><strong>Hourly Median:</strong> ~$30/hr — Rates above $75/hr are premium</li>
        <li><strong>Sweet Spot:</strong> Fixed $500-$2K range offers best volume + quality balance</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==================== SECTION 3: LEAD SCORING ====================
st.markdown('<p class="section-header">🏆 Lead Scoring & Whale Detection</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Lead Tier Distribution
    lead_order = ['🔥 TOP 5%', '⭐ TOP 20%', '📋 STANDARD']
    lead_counts = jobs_df['lead_tier'].value_counts().reindex(lead_order).fillna(0)
    
    fig = go.Figure(data=[go.Bar(
        x=lead_order,
        y=lead_counts.values,
        marker_color=[LEAD_COLORS.get(t) for t in lead_order],
        text=[f'{int(v):,}' for v in lead_counts.values],
        textposition='outside',
        textfont=dict(color='#e2e8f0', size=14),
        hovertemplate='<b>%{x}</b><br>Jobs: %{y:,}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(text="🎯 Lead Priority Distribution", font=dict(size=14, color='#f1f5f9')),
        yaxis_title="Number of Jobs"
    )
    fig = apply_chart_styling(fig, height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("🔍 View Jobs by Priority"):
        lead = st.selectbox("Select:", lead_order, key='lead1')
        filtered = jobs_df[jobs_df['lead_tier'] == lead]
        st.caption(f"{len(filtered):,} jobs • Avg Score: {filtered['score_normalized'].mean():.1f}")
        show_records_table(filtered.sort_values('score_normalized', ascending=False))

with col2:
    # Whale Funnel
    outlier_order = ['🐋 Whale', '🐠 Big Fish', '🐟 Above Avg', '➡️ Average', '🦐 Below Avg']
    outlier_counts = jobs_df['outlier_class'].value_counts().reindex(outlier_order).fillna(0)
    
    fig = go.Figure(go.Funnel(
        y=outlier_order,
        x=outlier_counts.values,
        textinfo="value+percent total",
        textfont=dict(color='white'),
        marker_color=[OUTLIER_COLORS.get(o) for o in outlier_order],
        connector=dict(line=dict(color='#334155'))
    ))
    
    fig.update_layout(
        title=dict(text="🐋 Outlier Classification (Z-Score)", font=dict(size=14, color='#f1f5f9'))
    )
    fig = apply_chart_styling(fig, height=300)
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("🔍 View Jobs by Outlier Class"):
        outlier = st.selectbox("Select:", outlier_order, key='out1')
        filtered = jobs_df[jobs_df['outlier_class'] == outlier]
        st.caption(f"{len(filtered):,} jobs • Avg Z: {filtered['z_score'].mean():.2f}")
        show_records_table(filtered.sort_values('z_score', ascending=False))

st.markdown("""
<div class="insight-box">
    <h4>💡 Scoring Formula</h4>
    <div class="formula-box">
        Score = Q × RMS × (1 + max(0, Z))<br>
        <small>Q = Client Quality | RMS = Market Position | Z = Niche Outlier</small>
    </div>
    <table class="tier-table">
        <tr><th>Class</th><th>Z-Score</th><th>Meaning</th></tr>
        <tr><td>🐋 Whale</td><td>Z ≥ 3</td><td>Top 0.1% — Exceptional opportunity</td></tr>
        <tr><td>🐠 Big Fish</td><td>Z ≥ 2</td><td>Top 2% — Very high value</td></tr>
        <tr><td>🐟 Above Avg</td><td>Z ≥ 1</td><td>Top 16% — Good opportunity</td></tr>
    </table>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==================== SECTION 4: NICHE ANALYSIS ====================
st.markdown('<p class="section-header">🎯 Technology Niche Performance</p>', unsafe_allow_html=True)

scanner_display = scanner_stats.dropna(subset=['name']).copy()

col1, col2 = st.columns(2)

with col1:
    # By Budget
    scanner_by_budget = scanner_display.sort_values('niche_mean', ascending=True).tail(15)
    
    fig = go.Figure(data=[go.Bar(
        y=scanner_by_budget['name'],
        x=scanner_by_budget['niche_mean'],
        orientation='h',
        marker_color=COLORS['primary'],
        text=[f'${v:,.0f}' for v in scanner_by_budget['niche_mean']],
        textposition='outside',
        textfont=dict(color='#e2e8f0'),
        hovertemplate='<b>%{y}</b><br>Avg Budget: $%{x:,.0f}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(text="💰 Niches by Avg Budget", font=dict(size=14, color='#f1f5f9')),
        xaxis_title="Average Budget ($)"
    )
    fig = apply_chart_styling(fig, height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # By Volume
    scanner_by_vol = scanner_display.sort_values('job_count', ascending=True).tail(15)
    
    fig = go.Figure(data=[go.Bar(
        y=scanner_by_vol['name'],
        x=scanner_by_vol['job_count'],
        orientation='h',
        marker_color=COLORS['success'],
        text=[f'{int(v):,}' for v in scanner_by_vol['job_count']],
        textposition='outside',
        textfont=dict(color='#e2e8f0'),
        hovertemplate='<b>%{y}</b><br>Jobs: %{x:,}<extra></extra>'
    )])
    
    fig.update_layout(
        title=dict(text="📊 Niches by Job Volume", font=dict(size=14, color='#f1f5f9')),
        xaxis_title="Number of Jobs"
    )
    fig = apply_chart_styling(fig, height=400)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("🔍 Explore Niche Details"):
    scanner_names = scanner_display['name'].tolist()
    selected_scanner = st.selectbox("Select Technology:", scanner_names, key='scan1')
    
    scanner_id = scanner_display[scanner_display['name'] == selected_scanner]['scanner_id'].values[0]
    niche_jobs = jobs_df[jobs_df['scanner_id'] == scanner_id]
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jobs", f"{len(niche_jobs):,}")
    c2.metric("Avg Budget", f"${niche_jobs['effective_budget'].mean():,.0f}")
    c3.metric("Total Value", f"${niche_jobs['effective_budget'].sum():,.0f}")
    c4.metric("Whales", f"{len(niche_jobs[niche_jobs['z_score'] >= 3])}")
    
    show_records_table(niche_jobs.sort_values('effective_budget', ascending=False))

st.markdown("---")

# ==================== SECTION 5: TOP LEADS ====================
st.markdown('<p class="section-header">🔥 Top Opportunities Right Now</p>', unsafe_allow_html=True)

# Top 20 Table
top_leads = jobs_df.nlargest(20, 'score_normalized').copy()
top_leads_display = top_leads[['title', 'effective_budget', 'client_tier', 'z_score', 'score_normalized', 'lead_tier']].copy()
top_leads_display['title'] = top_leads_display['title'].str[:50] + '...'
top_leads_display['effective_budget'] = top_leads_display['effective_budget'].apply(lambda x: f"${x:,.0f}")
top_leads_display['z_score'] = top_leads_display['z_score'].apply(lambda x: f"{x:.1f}")
top_leads_display['score_normalized'] = top_leads_display['score_normalized'].apply(lambda x: f"{x:.0f}")
top_leads_display.columns = ['Job Title', 'Budget', 'Client', 'Z-Score', 'Score', 'Priority']

st.dataframe(top_leads_display, use_container_width=True, hide_index=True, height=400)

# Score vs Budget Scatter
st.subheader("📈 Score vs Budget Analysis")

sample = jobs_df[jobs_df['effective_budget'] > 0].copy()
if len(sample) > 2000:
    sample = sample.sample(2000)

fig = px.scatter(
    sample,
    x='effective_budget',
    y='score_normalized',
    color='lead_tier',
    color_discrete_map=LEAD_COLORS,
    hover_data={'title': True, 'client_tier': True, 'z_score': ':.1f'},
    opacity=0.6,
    category_orders={'lead_tier': ['🔥 TOP 5%', '⭐ TOP 20%', '📋 STANDARD']}
)

fig.update_traces(marker=dict(size=8))
fig.update_layout(
    xaxis_title="Budget ($)",
    yaxis_title="Lead Score",
    xaxis_type='log',
    legend_title="Priority",
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
)
fig = apply_chart_styling(fig, height=400)
st.plotly_chart(fig, use_container_width=True)

with st.expander("🔍 Filter by Score Range"):
    score_range = st.slider("Score Range:", 0, 100, (80, 100), key='sr1')
    filtered = jobs_df[(jobs_df['score_normalized'] >= score_range[0]) & (jobs_df['score_normalized'] <= score_range[1])]
    st.caption(f"Found {len(filtered):,} jobs with score {score_range[0]}-{score_range[1]}")
    show_records_table(filtered.sort_values('score_normalized', ascending=False))

st.markdown("---")

# ==================== SECTION 6: TIME TRENDS ====================
st.markdown('<p class="section-header">📈 Time Trends</p>', unsafe_allow_html=True)

jobs_time = jobs_df.dropna(subset=['posted_at']).copy()
jobs_time['date'] = jobs_time['posted_at'].dt.date
jobs_time['day_of_week'] = jobs_time['posted_at'].dt.day_name()

daily = jobs_time.groupby('date').agg({'id': 'count', 'effective_budget': 'mean'}).reset_index()
daily.columns = ['date', 'job_count', 'avg_budget']
daily['date'] = pd.to_datetime(daily['date'])
daily['job_count_7d'] = daily['job_count'].rolling(7, min_periods=1).mean()

col1, col2 = st.columns(2)

with col1:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily['date'], y=daily['job_count'],
        mode='lines', line=dict(color=COLORS['primary'], width=1),
        opacity=0.4, name='Daily',
        hovertemplate='%{x}<br>Jobs: %{y}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=daily['date'], y=daily['job_count_7d'],
        mode='lines', line=dict(color=COLORS['danger'], width=3),
        name='7-Day Avg',
        hovertemplate='%{x}<br>7D Avg: %{y:.0f}<extra></extra>'
    ))
    fig.update_layout(
        title=dict(text="📊 Daily Job Volume", font=dict(size=14, color='#f1f5f9')),
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    fig = apply_chart_styling(fig, height=280)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_counts = jobs_time['day_of_week'].value_counts().reindex(day_order).fillna(0)
    colors = [COLORS['primary'] if d not in ['Saturday', 'Sunday'] else COLORS['standard'] for d in day_order]
    
    fig = go.Figure(data=[go.Bar(
        x=day_order,
        y=dow_counts.values,
        marker_color=colors,
        text=[f'{int(v):,}' for v in dow_counts.values],
        textposition='outside',
        textfont=dict(color='#e2e8f0'),
        hovertemplate='%{x}<br>Jobs: %{y:,}<extra></extra>'
    )])
    fig.update_layout(
        title=dict(text="📅 Jobs by Day of Week", font=dict(size=14, color='#f1f5f9'))
    )
    fig = apply_chart_styling(fig, height=280)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("🔍 Filter Jobs by Day"):
    day = st.selectbox("Select Day:", day_order, key='day1')
    filtered = jobs_time[jobs_time['day_of_week'] == day]
    st.caption(f"{len(filtered):,} jobs posted on {day}s")
    show_records_table(filtered.sort_values('posted_at', ascending=False))

st.markdown("""
<div class="insight-box">
    <h4>💡 Timing Strategy</h4>
    <ul>
        <li><strong>Best Days:</strong> Tuesday-Thursday have highest volume</li>
        <li><strong>Weekend Dip:</strong> 30-40% less activity on weekends</li>
        <li><strong>Pro Tip:</strong> Submit proposals early Monday for best visibility</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==================== FORMULA REFERENCE ====================
with st.expander("📚 Formula Reference Card"):
    st.markdown("""
    ### Client Quality Score (Q)
    ```
    Q = ln((Total_Spent / (Total_Hires + 1)) + 1)
    ```
    
    ### Relative Market Score (RMS)
    ```
    Fixed:  RMS = Budget / Global_Median
    Hourly: RMS = (Max_Rate / Median) × (1 + Spread_Bonus)
    ```
    
    ### Z-Score (Niche Outlier)
    ```
    Z = (Budget - Niche_Mean) / Niche_StdDev
    ```
    
    ### Unified Lead Score
    ```
    Score = Q × RMS × (1 + max(0, Z))
    Normalized = (Score / 99th_Percentile) × 100
    ```
    """)

# ==================== FOOTER ====================
st.markdown("---")
st.caption(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Built with Streamlit")