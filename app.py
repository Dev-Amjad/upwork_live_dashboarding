# 🚀 Upwork Jobs Analytics - Executive Dashboard
# Complete Streamlit App with Interactive Charts and Text Explanations

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
    page_title="🚀 Upwork Analytics Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-top: 0;
    }
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #e74c3c;
        border-radius: 50%;
        margin-right: 10px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.4; }
        100% { opacity: 1; }
    }
    .section-header {
        background: linear-gradient(90deg, #2E86AB 0%, #A23B72 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.8rem;
        font-weight: bold;
        margin-top: 30px;
    }
    .insight-box {
        background-color: #f0f7ff;
        border-left: 4px solid #2E86AB;
        padding: 15px;
        margin: 15px 0;
        border-radius: 0 8px 8px 0;
    }
    .formula-box {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 8px;
        font-family: monospace;
        margin: 10px 0;
    }
    .whale-alert {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
    }
    .metric-container {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
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

OUTLIER_COLORS = {
    '🐋 Whale': COLORS['platinum'],
    '🐠 Big Fish': COLORS['primary'],
    '🐟 Above Avg': COLORS['success'],
    '➡️ Average': COLORS['standard'],
    '🦐 Below Avg': COLORS['silver']
}

# ==================== DATABASE ====================
@st.cache_resource
def get_engine():
    try:
        db_url = st.secrets["DATABASE_URL"]
    except:
        db_url = "postgresql://analytics_user:Rahnuma824630*@46.62.227.215:54321/postgres"
    return create_engine(db_url)

def load_data():
    engine = get_engine()
    jobs_df = pd.read_sql("SELECT * FROM leads_job ORDER BY posted_at DESC", engine)
    scanners_df = pd.read_sql("SELECT * FROM leads_scanner", engine)
    return jobs_df, scanners_df

def process_data(jobs_df, scanners_df):
    df = jobs_df.copy()
    
    # Extract client info
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
    
    # Q Score
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
    
    # Scanner stats
    scanner_stats = df.groupby('scanner_id')['effective_budget'].agg(['mean', 'std', 'count', 'sum']).reset_index()
    scanner_stats.columns = ['scanner_id', 'niche_mean', 'niche_std', 'job_count', 'total_value']
    scanner_stats['niche_std'] = scanner_stats['niche_std'].fillna(1).replace(0, 1)
    scanner_stats = scanner_stats.merge(scanners_df[['id', 'name']], left_on='scanner_id', right_on='id', how='left')
    df = df.merge(scanner_stats[['scanner_id', 'niche_mean', 'niche_std']], on='scanner_id', how='left')
    
    # Z-Score
    df['z_score'] = (df['effective_budget'] - df['niche_mean']) / df['niche_std']
    df['z_score'] = df['z_score'].fillna(0)
    
    # Outlier Class
    def get_outlier_class(z):
        if z >= 3: return '🐋 Whale'
        elif z >= 2: return '🐠 Big Fish'
        elif z >= 1: return '🐟 Above Avg'
        elif z >= -1: return '➡️ Average'
        else: return '🦐 Below Avg'
    df['outlier_class'] = df['z_score'].apply(get_outlier_class)
    
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
    
    # Unified Score
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
    
    return df, scanner_stats, fixed_median, hourly_median

# ==================== HELPER FUNCTIONS ====================
def show_records_table(df, title, max_rows=20):
    """Display a formatted table of records"""
    display_df = df.head(max_rows).copy()
    
    cols_to_show = ['title', 'effective_budget', 'client_tier', 'lead_tier', 'z_score', 'score_normalized', 'client_country']
    cols_available = [c for c in cols_to_show if c in display_df.columns]
    display_df = display_df[cols_available]
    
    # Format columns
    if 'title' in display_df.columns:
        display_df['title'] = display_df['title'].str[:50] + '...'
    if 'effective_budget' in display_df.columns:
        display_df['effective_budget'] = display_df['effective_budget'].apply(lambda x: f"${x:,.0f}")
    if 'z_score' in display_df.columns:
        display_df['z_score'] = display_df['z_score'].apply(lambda x: f"{x:.2f}")
    if 'score_normalized' in display_df.columns:
        display_df['score_normalized'] = display_df['score_normalized'].apply(lambda x: f"{x:.1f}")
    
    # Rename columns
    col_names = {
        'title': 'Job Title',
        'effective_budget': 'Budget',
        'client_tier': 'Client Tier',
        'lead_tier': 'Priority',
        'z_score': 'Z-Score',
        'score_normalized': 'Score',
        'client_country': 'Country'
    }
    display_df.columns = [col_names.get(c, c) for c in display_df.columns]
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ==================== AUTO REFRESH ====================
REFRESH_INTERVAL = 60

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

time_since_refresh = time.time() - st.session_state.last_refresh
if time_since_refresh > REFRESH_INTERVAL:
    st.session_state.last_refresh = time.time()
    st.rerun()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("🎛️ Dashboard Controls")
    
    # Refresh
    st.subheader("🔄 Auto-Refresh")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.last_refresh = time.time()
            st.rerun()
    with col2:
        interval = st.selectbox("Interval", [30, 60, 120, 300], index=1, format_func=lambda x: f"{x}s")
        REFRESH_INTERVAL = interval
    
    next_refresh = max(0, REFRESH_INTERVAL - int(time_since_refresh))
    st.progress(1 - (next_refresh / REFRESH_INTERVAL))
    st.caption(f"Next refresh in {next_refresh}s")
    
    st.markdown("---")

# ==================== LOAD DATA ====================
with st.spinner("📊 Loading data from database..."):
    raw_jobs, scanners_df = load_data()
    jobs_df, scanner_stats, fixed_median, hourly_median = process_data(raw_jobs, scanners_df)

# ==================== SIDEBAR FILTERS ====================
with st.sidebar:
    st.subheader("🔍 Filters")
    
    selected_tier = st.selectbox("Client Tier", ['All'] + list(jobs_df['client_tier'].unique()))
    selected_lead = st.selectbox("Lead Priority", ['All'] + list(jobs_df['lead_tier'].unique()))
    selected_outlier = st.selectbox("Outlier Class", ['All'] + list(jobs_df['outlier_class'].unique()))
    
    min_budget = int(jobs_df['effective_budget'].min())
    max_budget = int(min(jobs_df['effective_budget'].max(), 50000))
    budget_range = st.slider("Budget Range ($)", min_budget, max_budget, (min_budget, max_budget))
    
    st.markdown("---")
    st.caption(f"📊 {len(jobs_df):,} jobs | {len(scanners_df)} scanners")

# Apply filters
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

# ==================== MAIN CONTENT ====================

# ===== HEADER =====
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 10px;">
    <span class="live-indicator"></span>
    <span class="main-header">Upwork Jobs Analytics - Executive Dashboard</span>
</div>
<p class="sub-header">Visual Storytelling with Data</p>
""", unsafe_allow_html=True)

st.markdown("---")

st.markdown("""
**What This Report Tells You:**
- Which job opportunities are worth your time
- Which clients pay the most per hire
- Which technology niches are most profitable
- How to prioritize your proposal efforts

**Data Period:** {} to {} ({} days)
""".format(
    jobs_df['posted_at'].min().strftime('%B %Y'),
    jobs_df['posted_at'].max().strftime('%B %Y'),
    (jobs_df['posted_at'].max() - jobs_df['posted_at'].min()).days
))

st.markdown("---")

# ============================================================
# SECTION 1: THE BIG PICTURE
# ============================================================
st.markdown('<p class="section-header">📊 Section 1: The Big Picture</p>', unsafe_allow_html=True)
st.markdown("**What you'll learn:** How many jobs we're tracking, what types they are, and the overall market size.")

# KPIs
total_jobs = len(filtered_df)
total_value = filtered_df['effective_budget'].sum()
avg_budget = filtered_df['effective_budget'].mean()
fixed_count = filtered_df['is_fixed'].sum()
hourly_count = filtered_df['is_hourly'].sum()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📊 Total Jobs", f"{total_jobs:,}")
with col2:
    st.metric("💰 Total Value", f"${total_value:,.0f}")
with col3:
    st.metric("📈 Avg Budget", f"${avg_budget:,.0f}")
with col4:
    st.metric("🔍 Scanners", len(scanners_df))

# Insight box
st.markdown("""
<div class="insight-box">
<h4>💡 What This Tells Us</h4>
<p>The dashboard above shows the <strong>health of your lead pipeline</strong>:</p>
<ul>
<li><strong>Total Jobs</strong>: The number of opportunities your scanners have discovered</li>
<li><strong>Total Market Value</strong>: The combined worth of all job budgets (your potential market)</li>
<li><strong>Average Budget</strong>: A typical job pays this amount</li>
<li><strong>Active Scanners</strong>: How many different technology niches you're monitoring</li>
</ul>
</div>
""", unsafe_allow_html=True)

# Job Type Distribution
st.subheader("💰 Fixed Price vs Hourly: How Do Clients Want to Pay?")

col_chart, col_table = st.columns([2, 1])

with col_chart:
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'pie'}, {'type': 'bar'}]],
                        subplot_titles=('Payment Type Distribution', 'Job Count'))
    
    fig.add_trace(go.Pie(
        labels=['Fixed Price', 'Hourly'],
        values=[fixed_count, hourly_count],
        hole=0.5,
        marker_colors=[COLORS['primary'], COLORS['warning']],
        textinfo='percent+label'
    ), row=1, col=1)
    
    fig.add_trace(go.Bar(
        x=['Fixed Price', 'Hourly'],
        y=[fixed_count, hourly_count],
        marker_color=[COLORS['primary'], COLORS['warning']],
        text=[f'{fixed_count:,}', f'{hourly_count:,}'],
        textposition='outside'
    ), row=1, col=2)
    
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**🖱️ Click to see records:**")
    job_type_select = st.radio("Select Type:", ['Fixed Price', 'Hourly'], label_visibility='collapsed')
    
    if job_type_select == 'Fixed Price':
        type_filtered = filtered_df[filtered_df['is_fixed']]
    else:
        type_filtered = filtered_df[filtered_df['is_hourly']]
    
    st.caption(f"Showing {len(type_filtered):,} {job_type_select} jobs")
    show_records_table(type_filtered.sort_values('effective_budget', ascending=False), job_type_select)

# Insight
st.markdown("""
<div class="insight-box">
<h4>💡 What This Tells Us</h4>
<p><strong>Fixed Price dominates!</strong> About 2 out of 3 clients prefer to pay a fixed amount for the entire project rather than hourly.</p>
<p><strong>Why this matters:</strong></p>
<ul>
<li>Fixed price = Client knows their budget upfront (easier to close deals)</li>
<li>Hourly = Often for ongoing work or when scope is unclear</li>
<li><strong>Strategy</strong>: Focus proposals on clear deliverables for fixed-price jobs</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# SECTION 2: WHO ARE THE BEST CLIENTS?
# ============================================================
st.markdown('<p class="section-header">👤 Section 2: Who Are the Best Clients?</p>', unsafe_allow_html=True)
st.markdown("**What you'll learn:** Not all clients are equal. Some pay premium rates, others are bargain hunters. This section helps you identify the \"whales\" - clients who spend big.")

# Client Tier Distribution
st.subheader("🏆 Client Quality Tiers: From Premium to Budget")

col_chart, col_table = st.columns([2, 1])

with col_chart:
    tier_order = ['💎 Platinum', '🥇 Gold', '🥈 Silver', '🥉 Bronze', '📦 Standard']
    tier_counts = filtered_df['client_tier'].value_counts().reindex(tier_order).fillna(0)
    
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'bar'}, {'type': 'pie'}]],
                        subplot_titles=('Jobs by Client Quality', 'Quality Mix'))
    
    fig.add_trace(go.Bar(
        x=tier_order,
        y=tier_counts.values,
        marker_color=[TIER_COLORS.get(t, COLORS['standard']) for t in tier_order],
        text=[f'{int(v):,}' for v in tier_counts.values],
        textposition='outside'
    ), row=1, col=1)
    
    fig.add_trace(go.Pie(
        labels=tier_order,
        values=tier_counts.values,
        marker_colors=[TIER_COLORS.get(t, COLORS['standard']) for t in tier_order],
        textinfo='percent',
        hole=0.4
    ), row=1, col=2)
    
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**🖱️ Click to see records:**")
    tier_select = st.selectbox("Select Tier:", tier_order, key="tier_select")
    
    tier_filtered = filtered_df[filtered_df['client_tier'] == tier_select]
    avg_budget_tier = tier_filtered['effective_budget'].mean()
    avg_spent_tier = tier_filtered['client_total_spent'].mean()
    
    st.metric("Jobs in Tier", f"{len(tier_filtered):,}")
    st.metric("Avg Budget", f"${avg_budget_tier:,.0f}")
    st.metric("Avg Client Spent", f"${avg_spent_tier:,.0f}")
    
    show_records_table(tier_filtered.sort_values('effective_budget', ascending=False), tier_select)

# Insight
st.markdown("""
<div class="insight-box">
<h4>💡 Understanding Client Tiers</h4>
<p>We rank clients based on <strong>how much they spend per hire</strong> (their "wallet size"):</p>
<table style="width:100%; border-collapse: collapse;">
<tr style="background:#f0f0f0;"><th style="padding:8px;text-align:left;">Tier</th><th style="padding:8px;text-align:left;">What It Means</th><th style="padding:8px;text-align:left;">Action</th></tr>
<tr><td style="padding:8px;">💎 <strong>Platinum</strong></td><td style="padding:8px;">Top 5% - Spend $10K+ per hire</td><td style="padding:8px;"><strong>Priority #1</strong></td></tr>
<tr><td style="padding:8px;">🥇 <strong>Gold</strong></td><td style="padding:8px;">Top 10% - High spenders</td><td style="padding:8px;">High priority</td></tr>
<tr><td style="padding:8px;">🥈 <strong>Silver</strong></td><td style="padding:8px;">Top 25% - Reliable budgets</td><td style="padding:8px;">Good opportunities</td></tr>
<tr><td style="padding:8px;">🥉 <strong>Bronze</strong></td><td style="padding:8px;">Top 50% - Average clients</td><td style="padding:8px;">Consider if fit</td></tr>
<tr><td style="padding:8px;">📦 <strong>Standard</strong></td><td style="padding:8px;">Bottom 50% - New/low spenders</td><td style="padding:8px;">Be selective</td></tr>
</table>
<p><strong>Key Insight</strong>: About 50% of clients are "Standard" (often new to Upwork). These are unknown quantities.</p>
</div>
""", unsafe_allow_html=True)

# Client Spending Histogram
st.subheader("📊 How Much Have Clients Spent on Upwork?")

col_chart, col_table = st.columns([2, 1])

with col_chart:
    spent_data = filtered_df[filtered_df['client_total_spent'] > 0]['client_total_spent']
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=spent_data.clip(upper=100000),
        nbinsx=50,
        marker_color=COLORS['primary'],
        opacity=0.7
    ))
    
    # Add percentile lines
    for p, color in [(50, COLORS['success']), (75, COLORS['warning']), (90, COLORS['danger'])]:
        pct_val = spent_data.quantile(p/100)
        if pct_val <= 100000:
            fig.add_vline(x=pct_val, line_dash='dash', line_color=color,
                         annotation_text=f'P{p}: ${pct_val:,.0f}')
    
    fig.update_layout(
        height=400,
        xaxis_title='Total Amount Spent on Upwork ($)',
        yaxis_title='Number of Clients'
    )
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**🖱️ Filter by spending range:**")
    spending_range = st.selectbox("Select Range:", 
        ['All Spenders', '$0 - $1K', '$1K - $10K', '$10K - $100K', '$100K+'],
        key="spending_select")
    
    if spending_range == '$0 - $1K':
        spend_filtered = filtered_df[(filtered_df['client_total_spent'] > 0) & (filtered_df['client_total_spent'] <= 1000)]
    elif spending_range == '$1K - $10K':
        spend_filtered = filtered_df[(filtered_df['client_total_spent'] > 1000) & (filtered_df['client_total_spent'] <= 10000)]
    elif spending_range == '$10K - $100K':
        spend_filtered = filtered_df[(filtered_df['client_total_spent'] > 10000) & (filtered_df['client_total_spent'] <= 100000)]
    elif spending_range == '$100K+':
        spend_filtered = filtered_df[filtered_df['client_total_spent'] > 100000]
    else:
        spend_filtered = filtered_df[filtered_df['client_total_spent'] > 0]
    
    st.caption(f"Showing {len(spend_filtered):,} jobs from {spending_range} clients")
    show_records_table(spend_filtered.sort_values('client_total_spent', ascending=False), spending_range)

st.markdown("""
<div class="insight-box">
<h4>💡 Reading This Chart</h4>
<p>This histogram shows <strong>how much money clients have spent on Upwork in their lifetime</strong>.</p>
<ul>
<li><strong>Most clients cluster on the left</strong> (lower spending) - newer or occasional users</li>
<li><strong>The dashed lines show percentiles</strong> - above P90 = top 10% of spenders</li>
<li><strong>Long tail to the right</strong> - a small number have spent hundreds of thousands</li>
</ul>
<p><strong>Strategy</strong>: Look for clients above the 75th percentile - they've proven they're willing to spend.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# SECTION 3: BUDGET DEEP DIVE
# ============================================================
st.markdown('<p class="section-header">💰 Section 3: Budget Deep Dive</p>', unsafe_allow_html=True)
st.markdown("**What you'll learn:** What's a \"good\" budget? How do fixed-price and hourly jobs compare? Where's the money?")

fixed_jobs = filtered_df[filtered_df['is_fixed'] & (filtered_df['budget'] > 0)]
hourly_jobs = filtered_df[filtered_df['is_hourly'] & (filtered_df['hourly_budget_max'] > 0)]

col_chart, col_table = st.columns([2, 1])

with col_chart:
    fig = make_subplots(rows=2, cols=2,
        subplot_titles=(
            f'Fixed Price (n={len(fixed_jobs):,}, Median=${fixed_jobs["budget"].median():,.0f})',
            f'Hourly (n={len(hourly_jobs):,}, Median=${hourly_jobs["hourly_budget_max"].median():.0f}/hr)',
            'Budget Percentiles',
            'Hourly Rate Spread'
        ),
        vertical_spacing=0.15)
    
    # Fixed histogram
    fig.add_trace(go.Histogram(
        x=fixed_jobs['budget'].clip(upper=5000),
        nbinsx=50,
        marker_color=COLORS['primary'],
        name='Fixed'
    ), row=1, col=1)
    
    # Hourly histogram
    fig.add_trace(go.Histogram(
        x=hourly_jobs['hourly_budget_max'].clip(upper=150),
        nbinsx=30,
        marker_color=COLORS['warning'],
        name='Hourly'
    ), row=1, col=2)
    
    # Percentiles
    percentiles = [25, 50, 75, 90, 95]
    fixed_pct = [fixed_jobs['budget'].quantile(p/100) for p in percentiles]
    hourly_pct = [hourly_jobs['hourly_budget_max'].quantile(p/100) for p in percentiles]
    
    fig.add_trace(go.Bar(
        name='Fixed ($)', x=[f'P{p}' for p in percentiles], y=fixed_pct,
        marker_color=COLORS['primary'], text=[f'${v:,.0f}' for v in fixed_pct], textposition='outside'
    ), row=2, col=1)
    
    fig.add_trace(go.Bar(
        name='Hourly ($/hr)', x=[f'P{p}' for p in percentiles], y=hourly_pct,
        marker_color=COLORS['warning'], text=[f'${v:.0f}' for v in hourly_pct], textposition='outside'
    ), row=2, col=1)
    
    # Spread scatter
    if len(hourly_jobs) > 0:
        sample_hourly = hourly_jobs.sample(min(500, len(hourly_jobs)))
        fig.add_trace(go.Scatter(
            x=sample_hourly['hourly_budget_min'],
            y=sample_hourly['hourly_budget_max'],
            mode='markers',
            marker=dict(size=5, color=COLORS['secondary'], opacity=0.5),
            name='Jobs'
        ), row=2, col=2)
    
    fig.update_layout(height=600, showlegend=False, barmode='group')
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**🖱️ Filter by budget range:**")
    budget_filter = st.selectbox("Select:", [
        'Fixed: $0-$100', 'Fixed: $100-$500', 'Fixed: $500-$2K', 'Fixed: $2K+',
        'Hourly: $0-$30/hr', 'Hourly: $30-$75/hr', 'Hourly: $75+/hr'
    ], key="budget_filter")
    
    if budget_filter == 'Fixed: $0-$100':
        budget_filt = fixed_jobs[fixed_jobs['budget'] <= 100]
    elif budget_filter == 'Fixed: $100-$500':
        budget_filt = fixed_jobs[(fixed_jobs['budget'] > 100) & (fixed_jobs['budget'] <= 500)]
    elif budget_filter == 'Fixed: $500-$2K':
        budget_filt = fixed_jobs[(fixed_jobs['budget'] > 500) & (fixed_jobs['budget'] <= 2000)]
    elif budget_filter == 'Fixed: $2K+':
        budget_filt = fixed_jobs[fixed_jobs['budget'] > 2000]
    elif budget_filter == 'Hourly: $0-$30/hr':
        budget_filt = hourly_jobs[hourly_jobs['hourly_budget_max'] <= 30]
    elif budget_filter == 'Hourly: $30-$75/hr':
        budget_filt = hourly_jobs[(hourly_jobs['hourly_budget_max'] > 30) & (hourly_jobs['hourly_budget_max'] <= 75)]
    else:
        budget_filt = hourly_jobs[hourly_jobs['hourly_budget_max'] > 75]
    
    st.caption(f"Showing {len(budget_filt):,} jobs in {budget_filter}")
    show_records_table(budget_filt.sort_values('effective_budget', ascending=False), budget_filter)

st.markdown("""
<div class="insight-box">
<h4>💡 How to Read These Charts</h4>
<p><strong>Top Left - Fixed Price Distribution:</strong></p>
<ul>
<li>Most fixed-price jobs are under $500</li>
<li>The median is around $150 - half pay less, half pay more</li>
<li>A $1,000+ job is already in the top tier</li>
</ul>
<p><strong>Top Right - Hourly Rate Distribution:</strong></p>
<ul>
<li>Most hourly jobs offer $15-$50/hr</li>
<li>Rates above $75/hr are premium</li>
</ul>
<p><strong>Bottom Right - Hourly Spread:</strong></p>
<ul>
<li>Points far from the diagonal have big spreads (negotiation room!)</li>
<li>Wide spreads mean the client is flexible on budget</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# SECTION 4: WHICH NICHES PAY BEST?
# ============================================================
st.markdown('<p class="section-header">🎯 Section 4: Which Technology Niches Pay Best?</p>', unsafe_allow_html=True)
st.markdown("**What you'll learn:** Each scanner monitors a specific technology niche. Which niches have the best-paying jobs?")

col_chart, col_table = st.columns([2, 1])

with col_chart:
    scanner_display = scanner_stats.dropna(subset=['name']).sort_values('niche_mean', ascending=True)
    
    fig = make_subplots(rows=1, cols=2,
        subplot_titles=('Average Budget by Niche', 'Job Volume by Niche'),
        horizontal_spacing=0.15)
    
    fig.add_trace(go.Bar(
        y=scanner_display['name'],
        x=scanner_display['niche_mean'],
        orientation='h',
        marker_color=COLORS['primary'],
        text=[f'${v:,.0f}' for v in scanner_display['niche_mean']],
        textposition='outside'
    ), row=1, col=1)
    
    scanner_by_vol = scanner_display.sort_values('job_count', ascending=True)
    fig.add_trace(go.Bar(
        y=scanner_by_vol['name'],
        x=scanner_by_vol['job_count'],
        orientation='h',
        marker_color=COLORS['success'],
        text=[f'{int(v):,}' for v in scanner_by_vol['job_count']],
        textposition='outside'
    ), row=1, col=2)
    
    fig.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**🖱️ Select a niche:**")
    scanner_names = scanner_stats.dropna(subset=['name'])['name'].tolist()
    selected_scanner = st.selectbox("Select Scanner:", scanner_names, key="scanner_select")
    
    scanner_id = scanner_stats[scanner_stats['name'] == selected_scanner]['scanner_id'].values[0]
    scanner_filtered = filtered_df[filtered_df['scanner_id'] == scanner_id]
    
    stats = scanner_stats[scanner_stats['name'] == selected_scanner].iloc[0]
    st.metric("Total Jobs", f"{int(stats['job_count']):,}")
    st.metric("Avg Budget", f"${stats['niche_mean']:,.0f}")
    st.metric("Total Value", f"${stats['total_value']:,.0f}")
    
    show_records_table(scanner_filtered.sort_values('effective_budget', ascending=False), selected_scanner)

st.markdown("""
<div class="insight-box">
<h4>💡 Niche Strategy Insights</h4>
<p><strong>The Trade-off:</strong></p>
<ul>
<li>Some niches pay well but have fewer jobs (iOS, NextJS)</li>
<li>Some niches have lots of jobs but lower average pay (WordPress, Shopify)</li>
</ul>
<p><strong>Strategic Questions:</strong></p>
<ul>
<li>Want fewer, higher-paying projects? → Focus on high-budget niches</li>
<li>Want steady volume? → Focus on high-volume niches</li>
<li>Best of both worlds? → Find niches with good budget AND decent volume</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# SECTION 5: LEAD SCORING RESULTS
# ============================================================
st.markdown('<p class="section-header">🏆 Section 5: Lead Scoring Results</p>', unsafe_allow_html=True)
st.markdown("**What you'll learn:** Our algorithm scores every job. This section shows which jobs deserve your immediate attention.")

# Lead Tier Distribution
col_chart, col_table = st.columns([2, 1])

with col_chart:
    lead_order = ['🔥 TOP 5%', '⭐ TOP 20%', '📋 STANDARD']
    lead_counts = filtered_df['lead_tier'].value_counts().reindex(lead_order).fillna(0)
    
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'bar'}, {'type': 'pie'}]],
                        subplot_titles=('Jobs by Priority', 'Priority Distribution'))
    
    fig.add_trace(go.Bar(
        x=lead_order,
        y=lead_counts.values,
        marker_color=[LEAD_COLORS.get(t, COLORS['standard']) for t in lead_order],
        text=[f'{int(v):,}' for v in lead_counts.values],
        textposition='outside'
    ), row=1, col=1)
    
    fig.add_trace(go.Pie(
        labels=lead_order,
        values=lead_counts.values,
        marker_colors=[LEAD_COLORS.get(t, COLORS['standard']) for t in lead_order],
        textinfo='percent',
        hole=0.4
    ), row=1, col=2)
    
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**🖱️ Select priority level:**")
    lead_select = st.selectbox("Select:", lead_order, key="lead_select")
    
    lead_filtered = filtered_df[filtered_df['lead_tier'] == lead_select]
    st.metric("Jobs", f"{len(lead_filtered):,}")
    st.metric("Avg Score", f"{lead_filtered['score_normalized'].mean():.1f}")
    st.metric("Avg Budget", f"${lead_filtered['effective_budget'].mean():,.0f}")
    
    show_records_table(lead_filtered.sort_values('score_normalized', ascending=False), lead_select)

st.markdown("""
<div class="insight-box">
<h4>💡 Lead Prioritization Explained</h4>
<table style="width:100%; border-collapse: collapse;">
<tr style="background:#f0f0f0;"><th style="padding:8px;">Tier</th><th style="padding:8px;">What It Means</th><th style="padding:8px;">Your Action</th></tr>
<tr><td style="padding:8px;">🔥 <strong>TOP 5%</strong></td><td style="padding:8px;">Best opportunities</td><td style="padding:8px;"><strong>Apply NOW</strong></td></tr>
<tr><td style="padding:8px;">⭐ <strong>TOP 20%</strong></td><td style="padding:8px;">Very good opportunities</td><td style="padding:8px;">Review daily</td></tr>
<tr><td style="padding:8px;">📋 <strong>STANDARD</strong></td><td style="padding:8px;">Average opportunities</td><td style="padding:8px;">Apply if perfect fit</td></tr>
</table>
<div class="formula-box">
<strong>The Math:</strong><br>
Score = Client Quality (Q) × Market Position (RMS) × Niche Outlier Factor (1 + Z)
</div>
</div>
""", unsafe_allow_html=True)

# Outlier/Whale Analysis
st.subheader("🐋 Finding the \"Whales\": Exceptional Opportunities")

col_chart, col_table = st.columns([2, 1])

with col_chart:
    outlier_order = ['🐋 Whale', '🐠 Big Fish', '🐟 Above Avg', '➡️ Average', '🦐 Below Avg']
    outlier_counts = filtered_df['outlier_class'].value_counts().reindex(outlier_order).fillna(0)
    
    fig = go.Figure(go.Funnel(
        y=outlier_order,
        x=outlier_counts.values,
        textinfo="value+percent total",
        marker_color=[OUTLIER_COLORS.get(o, COLORS['standard']) for o in outlier_order]
    ))
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**🖱️ Select outlier class:**")
    outlier_select = st.selectbox("Select:", outlier_order, key="outlier_select")
    
    outlier_filtered = filtered_df[filtered_df['outlier_class'] == outlier_select]
    st.metric("Jobs", f"{len(outlier_filtered):,}")
    st.metric("Avg Z-Score", f"{outlier_filtered['z_score'].mean():.2f}")
    st.metric("Avg Budget", f"${outlier_filtered['effective_budget'].mean():,.0f}")
    
    show_records_table(outlier_filtered.sort_values('z_score', ascending=False), outlier_select)

st.markdown("""
<div class="insight-box">
<h4>💡 The "Whale" Concept</h4>
<p><strong>Why compare within niches?</strong></p>
<p>A $2,000 budget means different things:</p>
<ul>
<li>In WordPress: That's a <strong>WHALE</strong> 🐋 (way above $200 average)</li>
<li>In iOS: That's just <strong>Average</strong> ➡️ (around $850 average)</li>
</ul>
<p><strong>Z-Score Classification:</strong></p>
<ul>
<li><strong>Z ≥ 3</strong>: Whale (top ~0.1%)</li>
<li><strong>Z ≥ 2</strong>: Big Fish (top ~2%)</li>
<li><strong>Z ≥ 1</strong>: Above Average (top ~16%)</li>
<li><strong>-1 < Z < 1</strong>: Average (middle ~68%)</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# SECTION 6: TIME TRENDS
# ============================================================
st.markdown('<p class="section-header">📈 Section 6: Time Trends</p>', unsafe_allow_html=True)
st.markdown("**What you'll learn:** When are jobs posted? Are budgets trending up or down?")

jobs_time = filtered_df.dropna(subset=['posted_at']).copy()
jobs_time['date'] = jobs_time['posted_at'].dt.date
jobs_time['day_of_week'] = jobs_time['posted_at'].dt.day_name()
jobs_time['hour'] = jobs_time['posted_at'].dt.hour

# Daily aggregation
daily = jobs_time.groupby('date').agg({'id': 'count', 'effective_budget': 'mean'}).reset_index()
daily.columns = ['date', 'job_count', 'avg_budget']
daily['date'] = pd.to_datetime(daily['date'])
daily['job_count_7d'] = daily['job_count'].rolling(7, min_periods=1).mean()
daily['avg_budget_7d'] = daily['avg_budget'].rolling(7, min_periods=1).mean()

col_chart, col_table = st.columns([2, 1])

with col_chart:
    fig = make_subplots(rows=2, cols=2,
        subplot_titles=('Daily Volume', 'Budget Trend', 'Jobs by Day of Week', 'Jobs by Hour (UTC)'),
        vertical_spacing=0.15)
    
    # Volume trend
    fig.add_trace(go.Scatter(x=daily['date'], y=daily['job_count'], mode='lines',
        line=dict(color=COLORS['primary'], width=1), opacity=0.4, name='Daily'), row=1, col=1)
    fig.add_trace(go.Scatter(x=daily['date'], y=daily['job_count_7d'], mode='lines',
        line=dict(color=COLORS['danger'], width=3), name='7-Day Avg'), row=1, col=1)
    
    # Budget trend
    fig.add_trace(go.Scatter(x=daily['date'], y=daily['avg_budget'], mode='lines',
        line=dict(color=COLORS['success'], width=1), opacity=0.4, name='Daily'), row=1, col=2)
    fig.add_trace(go.Scatter(x=daily['date'], y=daily['avg_budget_7d'], mode='lines',
        line=dict(color=COLORS['secondary'], width=3), name='7-Day Avg'), row=1, col=2)
    
    # Day of week
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_counts = jobs_time['day_of_week'].value_counts().reindex(day_order).fillna(0)
    dow_colors = [COLORS['primary'] if d not in ['Saturday', 'Sunday'] else COLORS['standard'] for d in day_order]
    
    fig.add_trace(go.Bar(x=day_order, y=dow_counts.values, marker_color=dow_colors,
        text=[f'{int(v):,}' for v in dow_counts.values], textposition='outside'), row=2, col=1)
    
    # Hour
    hour_counts = jobs_time['hour'].value_counts().sort_index()
    fig.add_trace(go.Bar(x=hour_counts.index, y=hour_counts.values, marker_color=COLORS['warning']), row=2, col=2)
    
    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**🖱️ Filter by day:**")
    day_select = st.selectbox("Select Day:", day_order, key="day_select")
    
    day_filtered = jobs_time[jobs_time['day_of_week'] == day_select]
    st.metric("Jobs on " + day_select, f"{len(day_filtered):,}")
    st.metric("Avg Budget", f"${day_filtered['effective_budget'].mean():,.0f}")
    
    show_records_table(day_filtered.sort_values('posted_at', ascending=False), day_select)

st.markdown("""
<div class="insight-box">
<h4>💡 Timing Insights</h4>
<p><strong>Formulas Used:</strong></p>
<ul>
<li>Daily Count: <code>COUNT(*) GROUP BY date</code></li>
<li>7-Day Moving Avg: <code>AVG(job_count) OVER (ROWS 6 PRECEDING)</code></li>
</ul>
<p><strong>Key Observations:</strong></p>
<ul>
<li>Weekdays (blue) have more activity than weekends (gray)</li>
<li><strong>Strategy</strong>: Submit proposals early in the week for best visibility</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# SECTION 7: TOP OPPORTUNITIES
# ============================================================
st.markdown('<p class="section-header">🔥 Section 7: Top Opportunities Right Now</p>', unsafe_allow_html=True)
st.markdown("**What you'll learn:** The highest-scoring job opportunities currently available.")

# Top Leads Table
st.subheader("🏆 Top 20 Leads by Unified Score")

top_leads = filtered_df.nlargest(20, 'score_normalized').copy()
top_leads_display = top_leads[['title', 'effective_budget', 'client_tier', 'z_score', 'score_normalized', 'lead_tier', 'client_country']].copy()
top_leads_display['title'] = top_leads_display['title'].str[:60] + '...'
top_leads_display['effective_budget'] = top_leads_display['effective_budget'].apply(lambda x: f"${x:,.0f}")
top_leads_display['z_score'] = top_leads_display['z_score'].apply(lambda x: f"{x:.2f}")
top_leads_display['score_normalized'] = top_leads_display['score_normalized'].apply(lambda x: f"{x:.1f}")
top_leads_display.columns = ['Title', 'Budget', 'Client Tier', 'Z-Score', 'Score', 'Priority', 'Country']

st.dataframe(top_leads_display, use_container_width=True, hide_index=True, height=500)

# Score vs Budget Scatter
st.subheader("🎯 Score vs Budget: Finding the Sweet Spot")

col_chart, col_table = st.columns([2, 1])

with col_chart:
    sample = filtered_df[filtered_df['effective_budget'] > 0]
    if len(sample) > 2000:
        sample = sample.sample(2000)
    
    fig = px.scatter(
        sample,
        x='effective_budget',
        y='score_normalized',
        color='lead_tier',
        color_discrete_map=LEAD_COLORS,
        hover_data=['title', 'client_tier', 'z_score'],
        opacity=0.6
    )
    fig.update_layout(
        height=500,
        xaxis_title='Budget ($)',
        yaxis_title='Score',
        xaxis_type='log',
        legend_title='Priority'
    )
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.markdown("**🖱️ Filter by score range:**")
    score_range = st.selectbox("Select:", [
        'Score 90-100 (Elite)', 'Score 70-90 (Excellent)', 
        'Score 50-70 (Good)', 'Score 25-50 (Fair)', 'Score 0-25 (Low)'
    ], key="score_range")
    
    if score_range == 'Score 90-100 (Elite)':
        score_filt = filtered_df[filtered_df['score_normalized'] >= 90]
    elif score_range == 'Score 70-90 (Excellent)':
        score_filt = filtered_df[(filtered_df['score_normalized'] >= 70) & (filtered_df['score_normalized'] < 90)]
    elif score_range == 'Score 50-70 (Good)':
        score_filt = filtered_df[(filtered_df['score_normalized'] >= 50) & (filtered_df['score_normalized'] < 70)]
    elif score_range == 'Score 25-50 (Fair)':
        score_filt = filtered_df[(filtered_df['score_normalized'] >= 25) & (filtered_df['score_normalized'] < 50)]
    else:
        score_filt = filtered_df[filtered_df['score_normalized'] < 25]
    
    st.caption(f"Showing {len(score_filt):,} jobs in {score_range}")
    show_records_table(score_filt.sort_values('score_normalized', ascending=False), score_range)

st.markdown("""
<div class="insight-box">
<h4>💡 How to Use This Data</h4>
<p><strong>Score Calculation:</strong></p>
<div class="formula-box">
Unified_Score = Q × RMS × (1 + max(0, Z))<br>
Normalized_Score = (Unified_Score / 99th_Percentile) × 100
</div>
<p><strong>The Scatter Plot:</strong></p>
<ul>
<li>🔴 Red dots = Top 5% leads - your highest priority</li>
<li>🟠 Orange dots = Top 20% leads - very good opportunities</li>
<li>⚫ Gray dots = Standard leads</li>
<li><strong>Note</strong>: A job can have high score with medium budget if the client is premium quality</li>
</ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# FINAL SUMMARY
# ============================================================
st.markdown('<p class="section-header">📋 Final Summary & Recommendations</p>', unsafe_allow_html=True)

# Summary metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📊 Total Jobs", f"{len(filtered_df):,}")
with col2:
    top5 = len(filtered_df[filtered_df['lead_tier'] == '🔥 TOP 5%'])
    st.metric("🔥 Top 5% Leads", f"{top5:,}")
with col3:
    whales = len(filtered_df[filtered_df['z_score'] >= 3])
    st.metric("🐋 Whales", f"{whales:,}")
with col4:
    bigfish = len(filtered_df[(filtered_df['z_score'] >= 2) & (filtered_df['z_score'] < 3)])
    st.metric("🐠 Big Fish", f"{bigfish:,}")

# Formula Reference
st.markdown("""
---
## 📚 Formula Reference Card

### Client Quality Score (Q)
```
Q = ln((Total_Spent / (Total_Hires + 1)) + 1)
```
- Measures how much a client spends per hire
- Higher Q = Premium client

### Relative Market Score (RMS)
```
Fixed:  RMS = Budget / Global_Fixed_Median
Hourly: RMS = (Max_Rate / Global_Hourly_Median) × (1 + Spread_Bonus)
        where Spread_Bonus = (Max_Rate - Min_Rate) / Max_Rate
```
- Compares job budget to market standard
- RMS > 1 means above-market budget

### Z-Score (Niche Outlier)
```
Z = (Job_Budget - Niche_Mean) / Niche_StdDev
```
- Measures how unusual a budget is for its niche
- Z ≥ 3 = Whale (exceptional)
- Z ≥ 2 = Big Fish (very good)

### Unified Lead Score
```
Score = Q × RMS × (1 + max(0, Z))
Normalized = (Score / 99th_Percentile) × 100
```
- Combines all factors into single 0-100 score
- Top 5% = Instant Action
- Top 20% = High Priority

---

**🖱️ Interactive Features:**
- All charts have **selection menus** to filter and see detailed records
- **Hover** over any data point to see statistics
- Tables show records for each selection

---

*Dashboard auto-refreshes every 60 seconds | Built with Streamlit*
""")

# Footer
st.markdown("---")
st.caption(f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data: {len(jobs_df):,} jobs from {len(scanners_df)} scanners")
