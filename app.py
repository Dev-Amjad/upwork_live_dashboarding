# 🚀 Upwork Jobs Analytics - Executive Dashboard
# Enhanced Version with All Charts, Job Links & Metadata Tooltips

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

# ==================== ENHANCED CSS ====================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    .stApp { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main .block-container {
        padding: 1rem 2rem 2rem 2rem;
        max-width: 100%;
    }
    
    .section-header {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 1.5rem 0 0.5rem 0;
    }
    
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
    
    .insight-box h4 { color: #a5b4fc !important; margin: 0 0 0.5rem 0; font-size: 1rem; font-weight: 600; }
    .insight-box p, .insight-box li, .insight-box span { color: #cbd5e1 !important; }
    .insight-box strong { color: #f1f5f9 !important; }
    .insight-box ul { margin: 0.5rem 0; padding-left: 1.2rem; }
    .insight-box li { margin: 0.3rem 0; }
    
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
    
    .tier-table { width: 100%; border-collapse: collapse; margin: 0.5rem 0; font-size: 0.85rem; }
    .tier-table th { background: #1e293b; color: #a5b4fc !important; padding: 0.5rem; text-align: left; border-bottom: 2px solid #4f46e5; }
    .tier-table td { padding: 0.5rem; border-bottom: 1px solid #334155; color: #cbd5e1 !important; }
    
    .live-badge {
        display: inline-flex; align-items: center; gap: 6px;
        background: linear-gradient(90deg, #dc2626, #ef4444);
        padding: 4px 12px; border-radius: 20px;
        font-size: 0.75rem; font-weight: 600; color: white;
        animation: pulse-badge 2s infinite;
    }
    .live-dot { width: 8px; height: 8px; background: white; border-radius: 50%; animation: pulse-dot 1.5s infinite; }
    @keyframes pulse-badge { 0%, 100% { opacity: 1; } 50% { opacity: 0.8; } }
    @keyframes pulse-dot { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.2); opacity: 0.7; } }
    
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
    
    .streamlit-expanderHeader { background: #1e293b !important; border-radius: 8px !important; }
    
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #1e293b; }
    ::-webkit-scrollbar-thumb { background: #4f46e5; border-radius: 4px; }
    
    .stButton > button {
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        color: white; border: none; border-radius: 8px; padding: 0.5rem 1rem; font-weight: 600;
    }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4); }
    
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background: #1e293b; border-radius: 8px 8px 0 0; padding: 8px 16px; color: #94a3b8; }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, #6366f1, #8b5cf6); color: white !important; }
    
    hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #334155, transparent); margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ==================== COLORS ====================
COLORS = {
    'primary': '#2E86AB', 'secondary': '#A23B72', 'success': '#27AE60', 'warning': '#F18F01',
    'danger': '#C73E1D', 'info': '#3498DB', 'platinum': '#9B59B6', 'gold': '#F1C40F',
    'silver': '#BDC3C7', 'bronze': '#E67E22', 'standard': '#95A5A6'
}

TIER_COLORS = {'💎 Platinum': COLORS['platinum'], '🥇 Gold': COLORS['gold'], '🥈 Silver': COLORS['silver'], '🥉 Bronze': COLORS['bronze'], '📦 Standard': COLORS['standard']}
LEAD_COLORS = {'🔥 TOP 5%': COLORS['danger'], '⭐ TOP 20%': COLORS['warning'], '📋 STANDARD': COLORS['standard']}
OUTLIER_COLORS = {'🐋 Whale': COLORS['platinum'], '🐠 Big Fish': COLORS['primary'], '🐟 Above Avg': COLORS['success'], '➡️ Average': COLORS['standard'], '🦐 Below Avg': COLORS['silver']}

def apply_chart_styling(fig, height=400):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e2e8f0', family='Inter'), height=height,
        margin=dict(t=50, b=50, l=60, r=40),
        legend=dict(bgcolor='rgba(30,41,59,0.8)', bordercolor='#334155', font=dict(color='#e2e8f0')),
        hoverlabel=dict(bgcolor='#1e293b', font_size=12, font_family='Inter')
    )
    fig.update_xaxes(gridcolor='#334155', linecolor='#475569', tickfont=dict(color='#94a3b8'), title_font=dict(color='#cbd5e1'))
    fig.update_yaxes(gridcolor='#334155', linecolor='#475569', tickfont=dict(color='#94a3b8'), title_font=dict(color='#cbd5e1'))
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
        default = {'client_country': None, 'client_total_spent': 0, 'client_total_hires': 0, 'client_jobs_posted': 0, 'client_reviews_count': 0}
        if ci is None: return pd.Series(default)
        if isinstance(ci, str):
            try: ci = json.loads(ci)
            except: return pd.Series(default)
        return pd.Series({
            'client_country': ci.get('country'),
            'client_total_spent': float(ci.get('total_spent', 0) or 0),
            'client_total_hires': int(ci.get('total_hires', 0) or 0),
            'client_jobs_posted': int(ci.get('jobs_posted', 0) or 0),
            'client_reviews_count': int(ci.get('reviews_count', 0) or 0)
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
        return '📦 Standard'
    df['client_tier'] = df['quality_score_Q'].apply(get_tier)
    
    scanner_stats = df.groupby('scanner_id')['effective_budget'].agg(['mean', 'std', 'count', 'sum']).reset_index()
    scanner_stats.columns = ['scanner_id', 'niche_mean', 'niche_std', 'job_count', 'total_value']
    scanner_stats['niche_std'] = scanner_stats['niche_std'].fillna(1).replace(0, 1)
    scanner_stats = scanner_stats.merge(scanners_df[['id', 'name']], left_on='scanner_id', right_on='id', how='left')
    
    scanner_quality = df.groupby('scanner_id')['quality_score_Q'].mean().reset_index()
    scanner_quality.columns = ['scanner_id', 'avg_client_quality']
    scanner_stats = scanner_stats.merge(scanner_quality, on='scanner_id', how='left')
    
    df = df.merge(scanner_stats[['scanner_id', 'niche_mean', 'niche_std']], on='scanner_id', how='left')
    df['z_score'] = (df['effective_budget'] - df['niche_mean']) / df['niche_std']
    df['z_score'] = df['z_score'].fillna(0)
    
    def get_outlier_class(z):
        if z >= 3: return '🐋 Whale'
        elif z >= 2: return '🐠 Big Fish'
        elif z >= 1: return '🐟 Above Avg'
        elif z >= -1: return '➡️ Average'
        return '🦐 Below Avg'
    df['outlier_class'] = df['z_score'].apply(get_outlier_class)
    
    fixed_median = df[df['is_fixed'] & (df['budget'] > 0)]['budget'].median() or 1
    hourly_median = df[df['is_hourly'] & (df['hourly_budget_max'] > 0)]['hourly_budget_max'].median() or 1
    
    def calc_rms(row):
        if row['is_fixed']:
            return row['budget'] / fixed_median if row['budget'] > 0 else 0
        if row['hourly_budget_max'] > 0:
            base = row['hourly_budget_max'] / hourly_median
            spread = row['hourly_budget_max'] - row['hourly_budget_min']
            spread_bonus = 1 + spread / row['hourly_budget_max'] if row['hourly_budget_max'] > 0 else 1
            return base * spread_bonus
        return 0
    
    df['rms_score'] = df.apply(calc_rms, axis=1)
    df['unified_score'] = df['quality_score_Q'] * df['rms_score'] * (1 + np.maximum(0, df['z_score']))
    df['unified_score'] = df['unified_score'].replace([np.inf, -np.inf], np.nan).fillna(0)
    max_score = df['unified_score'].quantile(0.99) or 1
    df['score_normalized'] = (df['unified_score'] / max_score * 100).clip(0, 100)
    
    p95, p80 = df['score_normalized'].quantile(0.95), df['score_normalized'].quantile(0.80)
    def get_lead_tier(s):
        if s >= p95: return '🔥 TOP 5%'
        elif s >= p80: return '⭐ TOP 20%'
        return '📋 STANDARD'
    df['lead_tier'] = df['score_normalized'].apply(get_lead_tier)
    
    return df, scanner_stats, fixed_median, hourly_median

def show_records_table(df, max_rows=15):
    """Display enhanced table with job links and metadata"""
    if len(df) == 0:
        st.info("No records found")
        return
    display_df = df.head(max_rows).copy()
    
    # Create clickable job links if url exists
    if 'url' in display_df.columns:
        display_df['🔗'] = display_df['url'].apply(lambda x: x if pd.notna(x) else None)
    
    cols_to_show = ['title', 'effective_budget', 'client_tier', 'lead_tier', 'z_score', 'score_normalized', 'client_country', 'posted_at']
    if 'url' in display_df.columns:
        cols_to_show.append('🔗')
    
    cols_available = [c for c in cols_to_show if c in display_df.columns]
    result_df = display_df[cols_available].copy()
    
    if 'title' in result_df.columns:
        result_df['title'] = result_df['title'].str[:45] + '...'
    if 'effective_budget' in result_df.columns:
        result_df['effective_budget'] = result_df['effective_budget'].apply(lambda x: f"${x:,.0f}")
    if 'z_score' in result_df.columns:
        result_df['z_score'] = result_df['z_score'].apply(lambda x: f"{x:.1f}")
    if 'score_normalized' in result_df.columns:
        result_df['score_normalized'] = result_df['score_normalized'].apply(lambda x: f"{x:.0f}")
    if 'posted_at' in result_df.columns:
        result_df['posted_at'] = result_df['posted_at'].apply(lambda x: x.strftime('%m/%d %H:%M') if pd.notna(x) else 'N/A')
    
    col_names = {'title': 'Title', 'effective_budget': 'Budget', 'client_tier': 'Client', 'lead_tier': 'Priority', 'z_score': 'Z', 'score_normalized': 'Score', 'client_country': 'Country', 'posted_at': 'Posted'}
    result_df.columns = [col_names.get(c, c) for c in result_df.columns]
    
    column_config = {}
    if '🔗' in result_df.columns:
        column_config['🔗'] = st.column_config.LinkColumn("🔗", display_text="View")
    
    st.dataframe(result_df, use_container_width=True, hide_index=True, height=min(450, 38*len(result_df)+40), column_config=column_config)

def show_detailed_table(df, max_rows=20):
    """Show detailed Plotly table with more metadata"""
    if len(df) == 0:
        st.info("No records found")
        return
    display_df = df.head(max_rows).copy()
    
    display_df['title_short'] = display_df['title'].str[:50] + '...'
    display_df['budget_fmt'] = display_df['effective_budget'].apply(lambda x: f'${x:,.0f}')
    display_df['z_fmt'] = display_df['z_score'].apply(lambda x: f'{x:.1f}')
    display_df['score_fmt'] = display_df['score_normalized'].apply(lambda x: f'{x:.0f}')
    display_df['posted_fmt'] = display_df['posted_at'].apply(lambda x: x.strftime('%m/%d %H:%M') if pd.notna(x) else 'N/A')
    display_df['spent_fmt'] = display_df['client_total_spent'].apply(lambda x: f'${x:,.0f}')
    display_df['hires_fmt'] = display_df['client_total_hires'].apply(lambda x: f'{int(x)}')
    
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['<b>Job Title</b>', '<b>Budget</b>', '<b>Client</b>', '<b>Z</b>', '<b>Score</b>', '<b>Priority</b>', '<b>Country</b>', '<b>Posted</b>', '<b>Client $</b>', '<b>Hires</b>'],
            fill_color=COLORS['primary'],
            font=dict(color='white', size=11),
            align='left', height=32
        ),
        cells=dict(
            values=[display_df['title_short'], display_df['budget_fmt'], display_df['client_tier'], display_df['z_fmt'], display_df['score_fmt'], display_df['lead_tier'], display_df['client_country'], display_df['posted_fmt'], display_df['spent_fmt'], display_df['hires_fmt']],
            fill_color=[['#1e293b', '#0f172a'] * (len(display_df)//2 + 1)][:len(display_df)],
            font=dict(color='#e2e8f0', size=10),
            align='left', height=28
        )
    )])
    fig.update_layout(height=min(500, 32*len(display_df)+60), margin=dict(t=10,b=10,l=10,r=10), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

# ==================== LOAD DATA ====================
with st.spinner("🔄 Loading data..."):
    raw_jobs, scanners_df = load_data()
    jobs_df, scanner_stats, fixed_median, hourly_median = process_data(raw_jobs, scanners_df)

# ==================== HEADER ====================
col_title, col_live, col_refresh = st.columns([6, 1, 1])
with col_title:
    st.markdown("# 🚀 Upwork Jobs Analytics")
    st.markdown("### Visual Storytelling with Data")
with col_live:
    st.markdown('<div class="live-badge"><span class="live-dot"></span>LIVE</div>', unsafe_allow_html=True)
with col_refresh:
    if st.button("🔄", help="Refresh Data"):
        st.cache_data.clear()
        st.rerun()

date_min, date_max = jobs_df['posted_at'].min(), jobs_df['posted_at'].max()
st.caption(f"📅 {date_min.strftime('%b %d')} - {date_max.strftime('%b %d, %Y')} • {len(jobs_df):,} opportunities • {len(scanners_df)} niches")
st.markdown("---")

# ==================== KPI INDICATORS ====================
st.markdown('<p class="section-header">📈 Key Performance Indicators</p>', unsafe_allow_html=True)

total_jobs = len(jobs_df)
total_value = jobs_df['effective_budget'].sum()
avg_budget = jobs_df['effective_budget'].mean()
fixed_count = jobs_df['is_fixed'].sum()
hourly_count = jobs_df['is_hourly'].sum()

fig = make_subplots(rows=1, cols=4, specs=[[{'type': 'indicator'}]*4], horizontal_spacing=0.05)
fig.add_trace(go.Indicator(mode="number", value=total_jobs, title={"text": "<b>Total Jobs</b><br><span style='font-size:11px;color:#94a3b8'>Opportunities</span>"}, number={"font": {"size": 42, "color": COLORS['primary']}}), row=1, col=1)
fig.add_trace(go.Indicator(mode="number", value=total_value, number={"prefix": "$", "font": {"size": 42, "color": COLORS['success']}, "valueformat": ",.0f"}, title={"text": "<b>Market Value</b><br><span style='font-size:11px;color:#94a3b8'>Sum of Budgets</span>"}), row=1, col=2)
fig.add_trace(go.Indicator(mode="number", value=avg_budget, number={"prefix": "$", "font": {"size": 42, "color": COLORS['warning']}, "valueformat": ",.0f"}, title={"text": "<b>Avg Budget</b><br><span style='font-size:11px;color:#94a3b8'>Per Job</span>"}), row=1, col=3)
fig.add_trace(go.Indicator(mode="number", value=len(scanners_df), title={"text": "<b>Scanners</b><br><span style='font-size:11px;color:#94a3b8'>Tech Niches</span>"}, number={"font": {"size": 42, "color": COLORS['secondary']}}), row=1, col=4)
fig = apply_chart_styling(fig, height=180)
fig.update_layout(margin=dict(t=60, b=20))
st.plotly_chart(fig, use_container_width=True)

st.markdown("""<div class="insight-box"><h4>💡 What This Tells Us</h4><ul>
<li><strong>Total Jobs</strong> — Opportunities discovered by your scanners</li>
<li><strong>Market Value</strong> — Combined worth of all budgets</li>
<li><strong>Avg Budget</strong> — A typical job pays this amount</li>
<li><strong>Scanners</strong> — Technology niches being monitored</li></ul></div>""", unsafe_allow_html=True)

st.markdown("---")

# ==================== SECTION 1: JOB TYPES ====================
st.markdown('<p class="section-header">📊 Section 1: The Big Picture</p>', unsafe_allow_html=True)
st.markdown("**What you'll learn:** Job types and overall market size.")

col1, col2 = st.columns(2)
with col1:
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'pie'}, {'type': 'bar'}]], subplot_titles=('<b>Payment Types</b>', '<b>Job Count</b>'))
    fig.add_trace(go.Pie(labels=['Fixed Price', 'Hourly'], values=[fixed_count, hourly_count], hole=0.5, marker_colors=[COLORS['primary'], COLORS['warning']], textinfo='percent+label', textfont_size=11), row=1, col=1)
    fig.add_trace(go.Bar(x=['Fixed', 'Hourly'], y=[fixed_count, hourly_count], marker_color=[COLORS['primary'], COLORS['warning']], text=[f'{fixed_count:,}', f'{hourly_count:,}'], textposition='outside', textfont=dict(color='#e2e8f0')), row=1, col=2)
    fig.add_annotation(text=f'<b>{total_jobs:,}</b><br>Total', x=0.18, y=0.5, font=dict(size=14, color='#e2e8f0'), showarrow=False)
    fig.update_layout(showlegend=False)
    fig = apply_chart_styling(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    with st.expander("🔍 View Jobs by Type", expanded=False):
        job_type = st.radio("Select:", ['Fixed Price', 'Hourly'], horizontal=True, key='jt1')
        filtered = jobs_df[jobs_df['is_fixed']] if job_type == 'Fixed Price' else jobs_df[jobs_df['is_hourly']]
        c1, c2, c3 = st.columns(3)
        c1.metric("Jobs", f"{len(filtered):,}")
        c2.metric("Avg Budget", f"${filtered['effective_budget'].mean():,.0f}")
        c3.metric("Total Value", f"${filtered['effective_budget'].sum():,.0f}")
        show_records_table(filtered.sort_values('effective_budget', ascending=False))

st.markdown("""<div class="insight-box"><h4>💡 What This Tells Us</h4>
<p><strong>Fixed Price dominates!</strong> ~67% clients prefer fixed amount.</p>
<ul><li><strong>Fixed</strong> = Client knows budget upfront (easier to close)</li>
<li><strong>Hourly</strong> = Ongoing work or unclear scope</li>
<li><strong>Strategy:</strong> Focus on clear deliverables for fixed-price</li></ul></div>""", unsafe_allow_html=True)

st.markdown("---")

# ==================== SECTION 2: CLIENT QUALITY ====================
st.markdown('<p class="section-header">👤 Section 2: Who Are the Best Clients?</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    tier_order = ['💎 Platinum', '🥇 Gold', '🥈 Silver', '🥉 Bronze', '📦 Standard']
    tier_colors = [COLORS['platinum'], COLORS['gold'], COLORS['silver'], COLORS['bronze'], COLORS['standard']]
    tier_counts = jobs_df['client_tier'].value_counts().reindex(tier_order).fillna(0)
    
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'bar'}, {'type': 'pie'}]], subplot_titles=('<b>Jobs by Client Quality</b>', '<b>Quality Mix</b>'))
    fig.add_trace(go.Bar(x=tier_order, y=tier_counts.values, marker_color=tier_colors, text=[f'{int(v):,}' for v in tier_counts.values], textposition='outside', textfont=dict(color='#e2e8f0')), row=1, col=1)
    fig.add_trace(go.Pie(labels=tier_order, values=tier_counts.values, marker_colors=tier_colors, textinfo='percent', hole=0.4), row=1, col=2)
    fig.update_layout(showlegend=False)
    fig = apply_chart_styling(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    with st.expander("🔍 View Jobs by Client Tier", expanded=False):
        tier = st.selectbox("Select Tier:", tier_order, key='tier1')
        filtered = jobs_df[jobs_df['client_tier'] == tier]
        c1, c2, c3 = st.columns(3)
        c1.metric("Jobs", f"{len(filtered):,}")
        c2.metric("Avg Budget", f"${filtered['effective_budget'].mean():,.0f}")
        c3.metric("Client Avg $", f"${filtered['client_total_spent'].mean():,.0f}")
        show_records_table(filtered.sort_values('client_total_spent', ascending=False))

st.markdown("""<div class="insight-box"><h4>💡 Understanding Client Tiers</h4>
<table class="tier-table"><tr><th>Tier</th><th>Meaning</th><th>Action</th></tr>
<tr><td>💎 Platinum</td><td>Top 5%</td><td><strong>Priority #1</strong></td></tr>
<tr><td>🥇 Gold</td><td>Top 10%</td><td>High priority</td></tr>
<tr><td>🥈 Silver</td><td>Top 25%</td><td>Good opportunities</td></tr>
<tr><td>🥉 Bronze</td><td>Top 50%</td><td>Consider if fit</td></tr>
<tr><td>📦 Standard</td><td>Bottom 50%</td><td>Be selective</td></tr></table></div>""", unsafe_allow_html=True)

# Client Spending Histogram
st.subheader("📊 Client Lifetime Spending")
col1, col2 = st.columns([2, 1])
with col1:
    spent_data = jobs_df[jobs_df['client_total_spent'] > 0]['client_total_spent']
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=spent_data.clip(upper=100000), nbinsx=50, marker_color=COLORS['primary'], opacity=0.7))
    for p, c in [(50, COLORS['success']), (75, COLORS['warning']), (90, COLORS['danger'])]:
        v = spent_data.quantile(p/100)
        if v <= 100000:
            fig.add_vline(x=v, line_dash='dash', line_color=c, annotation_text=f'P{p}: ${v:,.0f}', annotation_font_color='#e2e8f0')
    fig.update_layout(title=dict(text='<b>Client Spending Distribution</b>', x=0.5), xaxis_title='Total Spent ($)', yaxis_title='Count')
    fig = apply_chart_styling(fig, height=320)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    with st.expander("🔍 Filter by Spending", expanded=False):
        spend_range = st.selectbox("Range:", ['$0-$1K', '$1K-$10K', '$10K-$100K', '$100K+'], key='sp1')
        range_map = {'$0-$1K': (0, 1000), '$1K-$10K': (1000, 10000), '$10K-$100K': (10000, 100000), '$100K+': (100000, float('inf'))}
        low, high = range_map[spend_range]
        filtered = jobs_df[(jobs_df['client_total_spent'] >= low) & (jobs_df['client_total_spent'] < high)]
        st.metric("Clients", f"{len(filtered):,}")
        show_records_table(filtered.sort_values('client_total_spent', ascending=False))

# Top Countries
st.subheader("🌍 Top Countries by Client Quality")
country_stats = jobs_df.groupby('client_country').agg({'quality_score_Q': 'mean', 'effective_budget': 'mean', 'id': 'count'}).reset_index()
country_stats.columns = ['Country', 'Avg_Q', 'Avg_Budget', 'Jobs']
country_stats = country_stats[country_stats['Jobs'] >= 20]
top_countries = country_stats.nlargest(15, 'Avg_Q')

col1, col2 = st.columns([2, 1])
with col1:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=top_countries['Country'], y=top_countries['Avg_Q'], marker_color=COLORS['primary'], text=[f'Q={q:.1f}' for q in top_countries['Avg_Q']], textposition='outside', textfont=dict(color='#e2e8f0', size=9)))
    fig.update_layout(title=dict(text='<b>Best Client Countries</b>', x=0.5), xaxis_tickangle=-45)
    fig = apply_chart_styling(fig, height=380)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    with st.expander("🔍 View by Country", expanded=False):
        country = st.selectbox("Country:", top_countries['Country'].tolist(), key='c1')
        filtered = jobs_df[jobs_df['client_country'] == country]
        st.metric("Jobs", f"{len(filtered):,}")
        show_records_table(filtered.sort_values('effective_budget', ascending=False))

st.markdown("---")

# ==================== SECTION 3: BUDGET ANALYSIS ====================
st.markdown('<p class="section-header">💰 Section 3: Budget Deep Dive</p>', unsafe_allow_html=True)

fixed_jobs = jobs_df[jobs_df['is_fixed'] & (jobs_df['budget'] > 0)]
hourly_jobs = jobs_df[jobs_df['is_hourly'] & (jobs_df['hourly_budget_max'] > 0)]

fig = make_subplots(rows=2, cols=2, subplot_titles=(f'<b>Fixed Price</b> (n={len(fixed_jobs):,})', f'<b>Hourly Rates</b> (n={len(hourly_jobs):,})', '<b>Budget Percentiles</b>', '<b>Hourly Spread</b>'), vertical_spacing=0.12)

fig.add_trace(go.Histogram(x=fixed_jobs['budget'].clip(upper=5000), nbinsx=50, marker_color=COLORS['primary']), row=1, col=1)
fig.add_vline(x=fixed_jobs['budget'].median(), line_dash='dash', line_color=COLORS['danger'], row=1, col=1)

fig.add_trace(go.Histogram(x=hourly_jobs['hourly_budget_max'].clip(upper=150), nbinsx=30, marker_color=COLORS['warning']), row=1, col=2)
fig.add_vline(x=hourly_jobs['hourly_budget_max'].median(), line_dash='dash', line_color=COLORS['danger'], row=1, col=2)

pcts = [25, 50, 75, 90, 95]
fixed_pct = [fixed_jobs['budget'].quantile(p/100) for p in pcts]
hourly_pct = [hourly_jobs['hourly_budget_max'].quantile(p/100) for p in pcts]
fig.add_trace(go.Bar(name='Fixed $', x=[f'P{p}' for p in pcts], y=fixed_pct, marker_color=COLORS['primary'], text=[f'${v:,.0f}' for v in fixed_pct], textposition='outside', textfont=dict(color='#e2e8f0', size=9)), row=2, col=1)
fig.add_trace(go.Bar(name='Hourly', x=[f'P{p}' for p in pcts], y=hourly_pct, marker_color=COLORS['warning'], text=[f'${v:.0f}' for v in hourly_pct], textposition='outside', textfont=dict(color='#e2e8f0', size=9)), row=2, col=1)

if len(hourly_jobs) > 0:
    sample_hourly = hourly_jobs.sample(min(500, len(hourly_jobs)))
    fig.add_trace(go.Scatter(x=sample_hourly['hourly_budget_min'], y=sample_hourly['hourly_budget_max'], mode='markers', marker=dict(size=6, color=COLORS['secondary'], opacity=0.5)), row=2, col=2)
    fig.add_trace(go.Scatter(x=[0, 150], y=[0, 150], mode='lines', line=dict(dash='dash', color='#475569')), row=2, col=2)

fig.update_layout(showlegend=False, barmode='group')
fig = apply_chart_styling(fig, height=520)
st.plotly_chart(fig, use_container_width=True)

with st.expander("🔍 Filter by Budget Range", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Fixed Price**")
        fixed_range = st.select_slider("Budget:", ['$0-100', '$100-500', '$500-2K', '$2K-10K', '$10K+'], value='$100-500', key='fr1')
        range_map = {'$0-100': (0,100), '$100-500': (100,500), '$500-2K': (500,2000), '$2K-10K': (2000,10000), '$10K+': (10000, float('inf'))}
        low, high = range_map[fixed_range]
        filtered = fixed_jobs[(fixed_jobs['budget'] >= low) & (fixed_jobs['budget'] < high)]
        st.caption(f"{len(filtered):,} jobs")
        show_records_table(filtered.sort_values('budget', ascending=False), max_rows=10)
    with col2:
        st.markdown("**Hourly**")
        hourly_range = st.select_slider("Rate:", ['$0-25/hr', '$25-50/hr', '$50-100/hr', '$100+/hr'], value='$25-50/hr', key='hr1')
        range_map = {'$0-25/hr': (0,25), '$25-50/hr': (25,50), '$50-100/hr': (50,100), '$100+/hr': (100, float('inf'))}
        low, high = range_map[hourly_range]
        filtered = hourly_jobs[(hourly_jobs['hourly_budget_max'] >= low) & (hourly_jobs['hourly_budget_max'] < high)]
        st.caption(f"{len(filtered):,} jobs")
        show_records_table(filtered.sort_values('hourly_budget_max', ascending=False), max_rows=10)

st.markdown("""<div class="insight-box"><h4>💡 Budget Insights</h4><ul>
<li><strong>Fixed Median:</strong> ~$150 — Jobs above $500 are top 25%</li>
<li><strong>Hourly Median:</strong> ~$30/hr — $75+/hr is premium</li>
<li><strong>Spread Chart:</strong> Points far from diagonal = negotiation room!</li></ul></div>""", unsafe_allow_html=True)

st.markdown("---")

# ==================== SECTION 4: NICHE PERFORMANCE ====================
st.markdown('<p class="section-header">🎯 Section 4: Which Niches Pay Best?</p>', unsafe_allow_html=True)

scanner_display = scanner_stats.dropna(subset=['name']).copy()

col1, col2 = st.columns(2)
with col1:
    scanner_by_budget = scanner_display.sort_values('niche_mean', ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=scanner_by_budget['name'], x=scanner_by_budget['niche_mean'], orientation='h', marker_color=COLORS['primary'], text=[f'${v:,.0f}' for v in scanner_by_budget['niche_mean']], textposition='outside', textfont=dict(color='#e2e8f0', size=9)))
    fig.update_layout(title=dict(text='<b>Avg Budget by Niche</b>', x=0.5))
    fig = apply_chart_styling(fig, height=450)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    scanner_by_vol = scanner_display.sort_values('job_count', ascending=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(y=scanner_by_vol['name'], x=scanner_by_vol['job_count'], orientation='h', marker_color=COLORS['success'], text=[f'{int(v):,}' for v in scanner_by_vol['job_count']], textposition='outside', textfont=dict(color='#e2e8f0', size=9)))
    fig.update_layout(title=dict(text='<b>Job Volume by Niche</b>', x=0.5))
    fig = apply_chart_styling(fig, height=450)
    st.plotly_chart(fig, use_container_width=True)

# Strategy Matrix
st.subheader("📊 Strategy Matrix: Budget vs Volume")
median_budget = scanner_display['niche_mean'].median()
median_volume = scanner_display['job_count'].median()

def get_quadrant_color(row):
    if row['niche_mean'] >= median_budget and row['job_count'] >= median_volume: return COLORS['success']
    elif row['niche_mean'] >= median_budget: return COLORS['warning']
    elif row['job_count'] >= median_volume: return COLORS['info']
    return COLORS['standard']

scanner_display['quadrant_color'] = scanner_display.apply(get_quadrant_color, axis=1)

fig = go.Figure()
fig.add_trace(go.Scatter(x=scanner_display['job_count'], y=scanner_display['niche_mean'], mode='markers+text', marker=dict(size=scanner_display['total_value']/scanner_display['total_value'].max()*50+15, color=scanner_display['quadrant_color'], line=dict(width=2, color='white')), text=scanner_display['name'], textposition='top center', textfont=dict(size=9, color='#e2e8f0')))
fig.add_hline(y=median_budget, line_dash='dash', line_color='#475569')
fig.add_vline(x=median_volume, line_dash='dash', line_color='#475569')
fig.add_annotation(x=scanner_display['job_count'].max()*0.85, y=scanner_display['niche_mean'].max()*0.9, text='⭐ SWEET SPOT', font=dict(color=COLORS['success'], size=12), showarrow=False)
fig.add_annotation(x=scanner_display['job_count'].min()*1.5, y=scanner_display['niche_mean'].max()*0.9, text='💎 PREMIUM', font=dict(color=COLORS['warning'], size=12), showarrow=False)
fig.update_layout(title=dict(text='<b>Niche Strategy Matrix</b>', x=0.5), xaxis_title='Job Volume', yaxis_title='Avg Budget ($)')
fig = apply_chart_styling(fig, height=420)
st.plotly_chart(fig, use_container_width=True)

with st.expander("🔍 Explore Niche Details", expanded=False):
    selected = st.selectbox("Select Niche:", scanner_display['name'].tolist(), key='scan1')
    scanner_id = scanner_display[scanner_display['name'] == selected]['scanner_id'].values[0]
    niche_jobs = jobs_df[jobs_df['scanner_id'] == scanner_id]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Jobs", f"{len(niche_jobs):,}")
    c2.metric("Avg Budget", f"${niche_jobs['effective_budget'].mean():,.0f}")
    c3.metric("Total Value", f"${niche_jobs['effective_budget'].sum():,.0f}")
    c4.metric("🐋 Whales", f"{len(niche_jobs[niche_jobs['z_score'] >= 3])}")
    show_records_table(niche_jobs.sort_values('effective_budget', ascending=False))

st.markdown("""<div class="insight-box"><h4>💡 Strategy Matrix</h4>
<table class="tier-table"><tr><th>Quadrant</th><th>Strategy</th></tr>
<tr><td>⭐ Sweet Spot</td><td>High pay + High volume — <strong>Ideal focus</strong></td></tr>
<tr><td>💎 Premium</td><td>High pay, few jobs — Specialize</td></tr>
<tr><td>📦 Volume</td><td>Lower pay, many jobs — Portfolio building</td></tr></table></div>""", unsafe_allow_html=True)

st.markdown("---")

# ==================== SECTION 5: LEAD SCORING ====================
st.markdown('<p class="section-header">🏆 Section 5: Lead Scoring Results</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    lead_order = ['🔥 TOP 5%', '⭐ TOP 20%', '📋 STANDARD']
    lead_counts = jobs_df['lead_tier'].value_counts().reindex(lead_order).fillna(0)
    
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'bar'}, {'type': 'pie'}]], subplot_titles=('<b>Jobs by Priority</b>', '<b>Distribution</b>'))
    fig.add_trace(go.Bar(x=lead_order, y=lead_counts.values, marker_color=[LEAD_COLORS.get(t) for t in lead_order], text=[f'{int(v):,}' for v in lead_counts.values], textposition='outside', textfont=dict(color='#e2e8f0')), row=1, col=1)
    fig.add_trace(go.Pie(labels=['🔥 Instant', '⭐ High', '📋 Standard'], values=lead_counts.values, marker_colors=[LEAD_COLORS.get(t) for t in lead_order], textinfo='percent', hole=0.4), row=1, col=2)
    fig.add_annotation(text=f'<b>{int(lead_counts.iloc[0]):,}</b><br>Top', x=0.82, y=0.5, font=dict(size=12, color='#e2e8f0'), showarrow=False)
    fig.update_layout(showlegend=False)
    fig = apply_chart_styling(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    outlier_order = ['🐋 Whale', '🐠 Big Fish', '🐟 Above Avg', '➡️ Average', '🦐 Below Avg']
    outlier_counts = jobs_df['outlier_class'].value_counts().reindex(outlier_order).fillna(0)
    
    fig = go.Figure(go.Funnel(y=outlier_order, x=outlier_counts.values, textinfo='value+percent total', marker_color=[OUTLIER_COLORS.get(o) for o in outlier_order]))
    fig.update_layout(title=dict(text='<b>🐋 Whale Detection</b>', x=0.5))
    fig = apply_chart_styling(fig, height=350)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("🔍 Filter by Priority / Outlier", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        lead = st.selectbox("Priority:", lead_order, key='lead1')
        filtered = jobs_df[jobs_df['lead_tier'] == lead]
        st.caption(f"{len(filtered):,} jobs • Avg Score: {filtered['score_normalized'].mean():.1f}")
        show_records_table(filtered.sort_values('score_normalized', ascending=False), max_rows=10)
    with col2:
        outlier = st.selectbox("Outlier:", outlier_order, key='out1')
        filtered = jobs_df[jobs_df['outlier_class'] == outlier]
        st.caption(f"{len(filtered):,} jobs • Avg Z: {filtered['z_score'].mean():.2f}")
        show_records_table(filtered.sort_values('z_score', ascending=False), max_rows=10)

st.markdown("""<div class="insight-box"><h4>💡 Lead Prioritization</h4>
<table class="tier-table"><tr><th>Tier</th><th>Action</th></tr>
<tr><td>🔥 TOP 5%</td><td><strong>Apply NOW</strong></td></tr>
<tr><td>⭐ TOP 20%</td><td>Review daily</td></tr>
<tr><td>📋 STANDARD</td><td>Apply if perfect fit</td></tr></table>
<div class="formula-box">Score = Q × RMS × (1 + max(0, Z))</div></div>""", unsafe_allow_html=True)

st.markdown("---")

# ==================== SECTION 6: TIME TRENDS ====================
st.markdown('<p class="section-header">📈 Section 6: Time Trends</p>', unsafe_allow_html=True)

jobs_time = jobs_df.dropna(subset=['posted_at']).copy()
jobs_time['date'] = jobs_time['posted_at'].dt.date
jobs_time['day_of_week'] = jobs_time['posted_at'].dt.day_name()
jobs_time['hour'] = jobs_time['posted_at'].dt.hour

daily = jobs_time.groupby('date').agg({'id': 'count', 'effective_budget': 'mean'}).reset_index()
daily.columns = ['date', 'job_count', 'avg_budget']
daily['date'] = pd.to_datetime(daily['date'])
daily['job_count_7d'] = daily['job_count'].rolling(7, min_periods=1).mean()
daily['avg_budget_7d'] = daily['avg_budget'].rolling(7, min_periods=1).mean()

fig = make_subplots(rows=2, cols=2, subplot_titles=('<b>Daily Volume</b>', '<b>Budget Trend</b>', '<b>By Day of Week</b>', '<b>By Hour (UTC)</b>'), vertical_spacing=0.12)

fig.add_trace(go.Scatter(x=daily['date'], y=daily['job_count'], mode='lines', line=dict(color=COLORS['primary'], width=1), opacity=0.4), row=1, col=1)
fig.add_trace(go.Scatter(x=daily['date'], y=daily['job_count_7d'], mode='lines', line=dict(color=COLORS['danger'], width=3)), row=1, col=1)

fig.add_trace(go.Scatter(x=daily['date'], y=daily['avg_budget'], mode='lines', line=dict(color=COLORS['success'], width=1), opacity=0.4), row=1, col=2)
fig.add_trace(go.Scatter(x=daily['date'], y=daily['avg_budget_7d'], mode='lines', line=dict(color=COLORS['secondary'], width=3)), row=1, col=2)

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dow_counts = jobs_time['day_of_week'].value_counts().reindex(day_order).fillna(0)
colors = [COLORS['primary'] if d not in ['Saturday', 'Sunday'] else COLORS['standard'] for d in day_order]
fig.add_trace(go.Bar(x=day_order, y=dow_counts.values, marker_color=colors, text=[f'{int(v):,}' for v in dow_counts.values], textposition='outside', textfont=dict(color='#e2e8f0', size=9)), row=2, col=1)

hour_counts = jobs_time['hour'].value_counts().sort_index()
fig.add_trace(go.Bar(x=hour_counts.index, y=hour_counts.values, marker_color=COLORS['warning']), row=2, col=2)

fig.update_layout(showlegend=False)
fig = apply_chart_styling(fig, height=500)
st.plotly_chart(fig, use_container_width=True)

with st.expander("🔍 Filter by Day/Hour", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        day = st.selectbox("Day:", day_order, key='day1')
        filtered = jobs_time[jobs_time['day_of_week'] == day]
        st.caption(f"{len(filtered):,} jobs on {day}s")
        show_records_table(filtered.sort_values('posted_at', ascending=False), max_rows=10)
    with col2:
        hour = st.slider("Hour (UTC):", 0, 23, 12, key='hour1')
        filtered = jobs_time[jobs_time['hour'] == hour]
        st.caption(f"{len(filtered):,} jobs at {hour}:00 UTC")
        show_records_table(filtered.sort_values('posted_at', ascending=False), max_rows=10)

st.markdown("""<div class="insight-box"><h4>💡 Timing Insights</h4><ul>
<li><strong>Best Days:</strong> Tuesday-Thursday highest volume</li>
<li><strong>Weekend Dip:</strong> 30-40% less activity</li>
<li><strong>Strategy:</strong> Submit proposals early Monday</li></ul></div>""", unsafe_allow_html=True)

st.markdown("---")

# ==================== SECTION 7: TOP OPPORTUNITIES ====================
st.markdown('<p class="section-header">🔥 Section 7: Top Opportunities</p>', unsafe_allow_html=True)

top_leads = jobs_df.nlargest(20, 'score_normalized').copy()
show_detailed_table(top_leads)

st.subheader("🎯 Score vs Budget Analysis")
sample = jobs_df[jobs_df['effective_budget'] > 0].copy()
if len(sample) > 2000: sample = sample.sample(2000)

fig = px.scatter(sample, x='effective_budget', y='score_normalized', color='lead_tier', color_discrete_map=LEAD_COLORS, hover_data={'title': True, 'client_tier': True, 'z_score': ':.1f', 'client_country': True}, opacity=0.6, category_orders={'lead_tier': ['🔥 TOP 5%', '⭐ TOP 20%', '📋 STANDARD']})
fig.update_traces(marker=dict(size=8))
fig.update_layout(title=dict(text='<b>Score vs Budget</b>', x=0.5), xaxis_title='Budget ($)', yaxis_title='Lead Score', xaxis_type='log', legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5))
fig = apply_chart_styling(fig, height=420)
st.plotly_chart(fig, use_container_width=True)

with st.expander("🔍 Filter by Score Range", expanded=False):
    score_range = st.slider("Score:", 0, 100, (80, 100), key='sr1')
    filtered = jobs_df[(jobs_df['score_normalized'] >= score_range[0]) & (jobs_df['score_normalized'] <= score_range[1])]
    st.caption(f"{len(filtered):,} jobs with score {score_range[0]}-{score_range[1]}")
    show_records_table(filtered.sort_values('score_normalized', ascending=False))

st.markdown("---")

# ==================== FORMULA REFERENCE ====================
st.markdown('<p class="section-header">📚 Formula Reference</p>', unsafe_allow_html=True)

st.markdown("""<div class="insight-box">
<h4>Client Quality (Q)</h4>
<div class="formula-box">Q = ln((Total_Spent / (Total_Hires + 1)) + 1)</div>

<h4>Relative Market Score (RMS)</h4>
<div class="formula-box">Fixed: RMS = Budget / Median<br>Hourly: RMS = (Max/Median) × (1 + Spread_Bonus)</div>

<h4>Z-Score (Niche Outlier)</h4>
<div class="formula-box">Z = (Budget - Niche_Mean) / Niche_StdDev</div>

<h4>Unified Lead Score</h4>
<div class="formula-box">Score = Q × RMS × (1 + max(0, Z))<br>Normalized = (Score / 99th_Pct) × 100</div>
</div>""", unsafe_allow_html=True)

st.markdown("---")
st.caption("Developed by Amjad Ali - Autonomous Technologies")
st.caption(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • {len(jobs_df):,} jobs • {len(scanners_df)} scanners")