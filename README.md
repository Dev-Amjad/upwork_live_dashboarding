# 🚀 Upwork Jobs Analytics - Live Dashboard

Interactive real-time dashboard for Upwork job lead analytics with click-to-see-records functionality.

## ✨ Features

### 📊 7 Comprehensive Sections
1. **The Big Picture** - KPIs, job type distribution
2. **Who Are the Best Clients?** - Client tier analysis, spending patterns
3. **Budget Deep Dive** - Fixed vs hourly, percentiles, spread analysis
4. **Which Niches Pay Best?** - Scanner performance comparison
5. **Lead Scoring Results** - Priority tiers, whale detection
6. **Time Trends** - Daily volume, day of week, hourly patterns
7. **Top Opportunities** - Highest scoring leads, score vs budget scatter

### 🖱️ Interactive Click-to-Filter
Every chart has a selection menu that shows:
- Detailed records table for selected segment
- Key metrics (count, avg budget, etc.)
- Sorted by most relevant field

### 💡 Text Explanations
- Each section includes "What This Tells Us" insights
- Formula explanations for all metrics
- Strategy recommendations
- Tier classification tables

### 🔄 Real-Time Updates
- Auto-refresh every 60 seconds (configurable)
- Manual refresh button
- Live indicator shows dashboard is active

## 🚀 Quick Deploy

### Option 1: Streamlit Cloud (FREE)

1. **Push to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/upwork-dashboard.git
git push -u origin main
```

2. **Deploy:**
- Go to [share.streamlit.io](https://share.streamlit.io)
- Click "New app"
- Connect your GitHub repo
- Set main file: `app.py`
- Deploy!

3. **Add Secrets:**
In Streamlit Cloud settings → Secrets:
```toml
DATABASE_URL = "postgresql://analytics_user:Rahnuma824630*@46.62.227.215:54321/postgres"
```

### Option 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create secrets
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Run
streamlit run app.py
```

## 📐 Scoring Formulas

### Client Quality (Q)
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
Normalized to 0-100 scale
```

## 🎨 Dashboard Structure

```
┌─────────────────────────────────────────────────┐
│ 🔴 LIVE  Upwork Analytics Dashboard             │
├─────────────────────────────────────────────────┤
│ [KPI] [KPI] [KPI] [KPI]                         │
├────────────────────────┬────────────────────────┤
│                        │ 🖱️ Click to filter:   │
│     📊 CHART           │ [Dropdown]             │
│                        │ ┌──────────────────┐   │
│                        │ │ Records Table    │   │
│                        │ └──────────────────┘   │
├────────────────────────┴────────────────────────┤
│ 💡 What This Tells Us                           │
│ [Insight box with explanation]                  │
├─────────────────────────────────────────────────┤
│ 📚 Formula Reference Card                       │
└─────────────────────────────────────────────────┘
```

## 📁 File Structure

```
upwork-dashboard/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── .streamlit/
    └── secrets.toml       # Database credentials
```

## License

MIT License
