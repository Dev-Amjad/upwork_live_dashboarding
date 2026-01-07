# 🚀 Upwork Jobs - Live Dashboard

Real-time analytics dashboard for Upwork job leads with automatic scoring and prioritization.

## Features

- 🔴 **Live Updates**: Auto-refreshes every 30-60 seconds
- 🐋 **Whale Detection**: Instant alerts for exceptional opportunities
- 📊 **Interactive Charts**: Click-to-filter functionality
- 🎯 **Lead Scoring**: Unified score combining Q, RMS, Z-Score
- 🔍 **Advanced Filters**: Client tier, lead priority, budget range, date

## Quick Deploy to Streamlit Cloud (FREE)

### Step 1: Push to GitHub

```bash
# Create new repo on GitHub, then:
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/upwork-dashboard.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub account
4. Select your repository
5. Set main file path: `app.py`
6. Click "Deploy"

### Step 3: Add Secrets

In Streamlit Cloud dashboard:
1. Go to your app settings
2. Click "Secrets"
3. Add:
```toml
DATABASE_URL = "postgresql://analytics_user:Rahnuma824630*@46.62.227.215:54321/postgres"
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create secrets file
mkdir -p .streamlit
cp secrets.toml.example .streamlit/secrets.toml

# Run app
streamlit run app.py
```

## Scoring Formulas

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

## Client Tiers

| Tier | Percentile | Meaning |
|------|------------|---------|
| 💎 Platinum | Top 5% | Premium clients |
| 🥇 Gold | Top 10% | High spenders |
| 🥈 Silver | Top 25% | Reliable clients |
| 🥉 Bronze | Top 50% | Average clients |
| 📦 Standard | Bottom 50% | New/low spenders |

## Lead Priorities

| Priority | Percentile | Action |
|----------|------------|--------|
| 🔥 TOP 5% | Score ≥ P95 | Apply immediately |
| ⭐ TOP 20% | Score ≥ P80 | High priority |
| 📋 STANDARD | Below P80 | Review if fit |

## Outlier Classes

| Class | Z-Score | Rarity |
|-------|---------|--------|
| 🐋 Whale | Z ≥ 3 | Top 0.1% |
| 🐠 Big Fish | Z ≥ 2 | Top 2% |
| 🐟 Above Avg | Z ≥ 1 | Top 16% |
| ➡️ Average | -1 < Z < 1 | Middle 68% |
| 🦐 Below Avg | Z ≤ -1 | Bottom 16% |

## License

MIT License
