# 🏒 Puckcast V2.0 Site Plan - REVISED (Focused MVP)

**Created:** November 20, 2025
**Target Launch:** 2-3 weeks
**Goal:** Get a working prediction site live with core features only

---

## 🎯 Vision (Simplified)

Build a **clean NHL prediction site** that shows:
- Today's predictions with confidence levels
- Model performance/accuracy
- Automated X/Twitter content
- Basic analytics dashboard

**NO:** Payments, complex betting tools, multiple channels, user accounts (yet)
**YES:** Core predictions, clean UX, X automation, transparent methodology

---

## 📊 What We're Removing from Original Plan

### ❌ **Removed (Too Early)**
- User authentication/accounts
- Subscription tiers (Free/Pro/Elite)
- Stripe payments
- Complex betting tools (Kelly calculator, bankroll manager, strategy simulator)
- User leaderboards
- Email notifications
- API for partners
- Mobile app
- Discord bot
- Advanced bet tracking

### ⏳ **Deprioritized (Later Phases)**
- Betting integration (wait until we have odds data)
- H2H matchup history (need more seasons first)
- Injury impact features
- Real-time goalie confirmations
- Advanced analytics

---

## ✅ V2.0 MVP - What We're Actually Building

### **Core Pages (6 Total)**

#### 1. **Landing Page** (/)
**Purpose:** Show today's predictions immediately

**Sections:**
- Hero: "NHL Predictions Powered by Machine Learning"
- Current accuracy badge (60.89% or current)
- Today's Games (3-5 cards with predictions)
  - Team matchup
  - Home win probability
  - Confidence level (Low/Med/High)
  - Key factors (2-3 bullet points: "Back-to-back", "Goalie advantage", etc.)
- "How It Works" (3 simple steps)
- "Model Performance" (simple chart: accuracy over time)
- Footer with links

**Design:**
- Clean, minimal (like MoneyPuck or FiveThirtyEight)
- Mobile-friendly cards
- Fast loading

#### 2. **Today's Predictions** (/predictions)
**Purpose:** Full game breakdown for today

**For Each Game:**
- Matchup header (logos, teams, time)
- **Prediction:** Home 65% | Away 35%
- **Confidence:** High/Medium/Low
- **Key Factors** (5 max):
  - Back-to-back situation
  - Rest advantage
  - Goalie performance (recent GSAx)
  - Momentum (recent form)
  - Home ice advantage
- **Stats Comparison** (simple table):
  - Record, Goals/game, Goals against/game, PP%, PK%
- Toggle to show "How we calculated this" (feature breakdown)

**Features:**
- Filter by confidence level
- Sort by probability
- Collapsible details

#### 3. **Model Performance** (/performance)
**Purpose:** Show accuracy and build trust

**Sections:**
- **Overall Stats:**
  - Current season accuracy: 55.97% (updates live)
  - Historical accuracy: 60.89%
  - Total predictions made
  - Edge over baseline (always pick home team)

- **Accuracy Chart:**
  - Line chart: accuracy by month
  - Bar chart: accuracy by team

- **Calibration:**
  - "When we say 70%, we're right 70% of the time"
  - Calibration curve visualization

- **Recent Predictions:**
  - Last 20 games (table)
  - Prediction vs Actual
  - Filter: Correct/Incorrect/All

#### 4. **How It Works** (/methodology)
**Purpose:** Explain the model (transparency builds trust)

**Sections:**
- **Overview:**
  - "We use 204 features and machine learning"
  - Trained on 6 seasons of NHL data
  - Updated daily with new games

- **Key Features (Top 10):**
  - Each feature explained in plain English
  - Why it matters
  - Visual example

- **Data Sources:**
  - NHL API (play-by-play data)
  - Custom Expected Goals (xG) model
  - Goalie performance tracking

- **Model Details:**
  - Logistic Regression (explain why)
  - Training process
  - Validation approach

- **Limitations:**
  - Doesn't have betting odds yet
  - Doesn't account for late lineup changes
  - Injuries may not be reflected

#### 5. **Analytics** (/analytics)
**Purpose:** Deep dive for hockey nerds

**Sections:**
- **Feature Importance:**
  - Top 20 features ranked
  - Interactive chart
  - Explanation for each

- **Team Profiles:**
  - Select a team
  - Model's accuracy predicting their games
  - Strengths/weaknesses identified by model
  - Home vs away performance

- **Trends:**
  - Back-to-back impact (how much does it hurt?)
  - Rest days analysis
  - Goalie performance correlation
  - Home ice advantage by team

#### 6. **About** (/about)
**Purpose:** Build credibility

**Content:**
- Project origin story (brief)
- Methodology philosophy (transparent, data-driven)
- Results history
- Future roadmap
- Contact/feedback

---

## 🎨 Design System

### **Visual Identity**
- **Colors:**
  - Primary: Deep Navy (#0F172A)
  - Accent: Electric Blue (#3B82F6)
  - Success: Green (#10B981)
  - Warning: Orange (#F97316)
  - Background: White/Light Gray (#F9FAFB)

- **Typography:**
  - Headings: Inter Bold
  - Body: Inter Regular
  - Data/Stats: JetBrains Mono

### **Components**
- **Game Card:**
  - Team logos (get from NHL API or simple abbreviations)
  - Probability meter (visual bar)
  - Confidence badge
  - Key factors (icons + text)

- **Stat Card:**
  - Metric name
  - Big number
  - Trend indicator (↑ ↓)

- **Chart:**
  - Use Recharts library
  - Simple, clean style
  - Tooltips for details

---

## 🤖 X/Twitter Automation

### **Daily Content Strategy**

#### **Morning Post (9 AM ET)**
```
🏒 Tonight's NHL Predictions (Nov 20)

BOS @ TOR: 62% TOR ⭐ (High confidence)
EDM @ VAN: 58% VAN
NYR @ PHI: 51% NYR

Model: 55.97% accuracy this season
Details: puckcast.ai

#NHL #NHLPredictions #HockeyTwitter
```

#### **Post-Game Updates (After each game)**
```
✅ BOS @ TOR: Predicted TOR 62% → TOR wins 4-2

Key factors we identified:
• Rest advantage (TOR fresh, BOS back-to-back)
• Goalie performance (Samsonov GSAx edge)

Season accuracy: 56.1% (179/318)

#NHL #LeafsNation
```

#### **Weekly Recap (Sunday)**
```
📊 Week 8 Prediction Results

Accuracy: 58.3% (14/24 games)
Best calls:
• VGK over COL (78% confidence) ✅
• BUF over MTL (71% confidence) ✅

Biggest miss:
• EDM over ARI (67% confidence) ❌

Model learning and improving daily.
```

### **Automation Setup**

**Tools:**
- Python script using `tweepy` library
- GitHub Actions for scheduling
- Store predictions in database/JSON
- Post automatically at set times

**Cron Schedule:**
```yaml
- name: Daily predictions
  cron: '0 14 *  * *'  # 9 AM ET

- name: Post-game updates
  cron: '0 * * * *'  # Every hour (check for finished games)

- name: Weekly recap
  cron: '0 18 * * 0'  # Sunday 1 PM ET
```

---

## 🛠️ Tech Stack (Simplified)

### **Frontend**
- **Framework:** Next.js 14 (App Router) ← Keep existing
- **Styling:** Tailwind CSS
- **Charts:** Recharts
- **Deployment:** Vercel

### **Backend**
- **API:** Next.js API Routes (for simple endpoints)
- **Database:** JSON files in repo (for now, no DB needed)
- **Python:** Generate predictions → export JSON
- **Hosting:** Vercel

### **Data Pipeline**
- **Daily Update:** GitHub Actions runs `predict_tonight.py`
- **Export:** Writes `web/src/data/todaysPredictions.json`
- **Commit:** Auto-commit and push
- **Deploy:** Vercel auto-deploys on push

**No complex backend needed!** Just Python scripts + JSON + Vercel.

---

## 📁 Site Structure (Simplified)

```
puckcast/
├── web/                           # Next.js app
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Landing (today's predictions)
│   │   │   ├── predictions/       # Full predictions page
│   │   │   ├── performance/       # Model performance
│   │   │   ├── methodology/       # How it works
│   │   │   ├── analytics/         # Deep dive analytics
│   │   │   └── about/             # About page
│   │   │
│   │   ├── components/
│   │   │   ├── GameCard.tsx
│   │   │   ├── StatCard.tsx
│   │   │   ├── ProbabilityMeter.tsx
│   │   │   ├── AccuracyChart.tsx
│   │   │   └── FeatureBreakdown.tsx
│   │   │
│   │   ├── data/
│   │   │   ├── todaysPredictions.json      # ← Updated daily
│   │   │   ├── modelPerformance.json       # Historical accuracy
│   │   │   ├── featureImportance.json      # Top features
│   │   │   └── teamProfiles.json           # Team-specific stats
│   │   │
│   │   └── lib/
│   │       ├── data.ts            # Data loading utils
│   │       └── predictions.ts     # Prediction utils
│   │
│   ├── public/
│   │   └── (images, logos, etc.)
│   │
│   └── package.json
│
├── scripts/                       # Python automation
│   ├── generate_predictions.py    # Daily predictions
│   ├── update_performance.py      # Update model stats
│   ├── post_to_twitter.py         # X automation
│   └── fetch_results.py           # Get actual results
│
└── .github/workflows/
    └── daily-update.yml           # Auto-update predictions
```

---

## 🚀 Development Phases

### **Phase 1: Core Site (Week 1)**
**Goal:** Get basic site live with today's predictions

- [ ] Set up Next.js app structure
- [ ] Create 6 pages (landing, predictions, performance, methodology, analytics, about)
- [ ] Build core components (GameCard, StatCard, charts)
- [ ] Design system implementation
- [ ] Connect to JSON data files
- [ ] Mobile responsive
- [ ] Deploy to Vercel

**Deliverable:** Live site showing predictions

### **Phase 2: Automation (Week 2)**
**Goal:** Auto-update predictions daily

- [ ] Create `generate_predictions.py` script
- [ ] Set up GitHub Actions for daily runs
- [ ] Auto-commit JSON updates
- [ ] Vercel auto-deploy on push
- [ ] Test full pipeline

**Deliverable:** Self-updating prediction site

### **Phase 3: X Integration (Week 3)**
**Goal:** Automated social media presence

- [ ] Set up X Developer account
- [ ] Create `post_to_twitter.py` script
- [ ] Implement content templates
- [ ] Schedule posts via GitHub Actions
- [ ] Test automation

**Deliverable:** Automated X posts 3x/day

### **Phase 4: Analytics & Polish (Week 4+)**
**Goal:** Rich analytics and refinements

- [ ] Feature importance page
- [ ] Team profiles
- [ ] Calibration charts
- [ ] Performance history
- [ ] SEO optimization
- [ ] Analytics tracking

**Deliverable:** Complete, polished site

---

## 📊 Success Metrics (Simple)

### **Launch Metrics (Month 1)**
- [ ] Site live and loading fast (< 2s)
- [ ] Daily predictions updating automatically
- [ ] X posts going out on schedule
- [ ] 100+ unique visitors/day
- [ ] 50+ X followers

### **Growth Metrics (Month 3)**
- [ ] 500+ unique visitors/day
- [ ] 300+ X followers
- [ ] 60%+ accuracy maintained
- [ ] Featured on r/hockey or hockey twitter

---

## 🎯 What Comes After MVP

**Once MVP is live and working:**

1. **Add Betting Odds** (when we get a data source)
   - Compare our predictions to Vegas lines
   - Show "edge" opportunities
   - Basic betting recommendations

2. **User Accounts** (if demand exists)
   - Save favorite teams
   - Track personal record
   - Get email alerts

3. **API** (if partners interested)
   - Let others use our predictions
   - Charge for API access

4. **Monetization** (if site gets traction)
   - Ads (non-intrusive)
   - Premium tier (more features)
   - Affiliate links

**But NOT NOW!** Focus on the core product first.

---

## 💡 Key Principles

1. **Simple First:** Get core functionality working before adding complexity
2. **Transparent:** Show how the model works, what it gets right/wrong
3. **Automated:** Use GitHub Actions + Python scripts, not complex backend
4. **Mobile-First:** Most users will view on phone
5. **Fast:** Site should load in < 2 seconds
6. **Data-Driven:** Let the numbers speak for themselves

---

## 🚧 NOT Building (Yet)

- ❌ User accounts/authentication
- ❌ Payment processing
- ❌ Complex betting tools
- ❌ Email notifications
- ❌ Mobile app
- ❌ API for partners
- ❌ Discord/Telegram bots
- ❌ Injury tracking
- ❌ Real-time odds integration
- ❌ Advanced bet tracking
- ❌ User leaderboards
- ❌ Multi-sport expansion

These are all good ideas for LATER. But first: **get the core working**.

---

## 📝 Content for X Automation

### **Template Library**

**Daily Predictions:**
```
🏒 [DATE] NHL Predictions

[GAME 1]: [PRED]% [TEAM] [CONFIDENCE EMOJI]
[GAME 2]: [PRED]% [TEAM]
[GAME 3]: [PRED]% [TEAM]

Model: [ACCURACY]% this season
Details: puckcast.ai

#NHL #NHLPredictions
```

**Prediction Result:**
```
[✅/❌] [AWAY] @ [HOME]: Predicted [TEAM] [PROB]% → [RESULT]

Key factors:
• [FACTOR 1]
• [FACTOR 2]

Season: [CORRECT]/[TOTAL] ([ACC]%)
```

**Feature Spotlight:**
```
📊 Feature Spotlight: [FEATURE NAME]

Why it matters:
[EXPLANATION]

Impact on predictions: [IMPORTANCE RANK]

#NHLStats #HockeyAnalytics
```

**Milestone:**
```
🎯 Milestone: [ACHIEVEMENT]

Model has now:
• Predicted [N] games this season
• [ACC]% accuracy
• [EDGE] better than baseline

Thanks for following!
```

---

## ✅ Launch Checklist

**Before Going Live:**
- [ ] All 6 pages working
- [ ] Mobile responsive
- [ ] Fast load times (< 2s)
- [ ] Predictions updating daily
- [ ] X automation tested
- [ ] SEO metadata added
- [ ] Google Analytics added
- [ ] Error handling for edge cases
- [ ] About page explains everything
- [ ] Contact info/feedback form
- [ ] Legal stuff (terms, privacy) - basic versions

---

## 🎨 Example Landing Page (Wireframe)

```
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║   🏒 PUCKCAST                                         ║
║   NHL Predictions Powered by Machine Learning        ║
║                                                       ║
║   [55.97% Accuracy This Season]                      ║
║                                                       ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║   TONIGHT'S PREDICTIONS                               ║
║                                                       ║
║   ┌─────────────────────────────────────────┐       ║
║   │ BOS @ TOR                         62% ⭐ │       ║
║   │ ▓▓▓▓▓▓▓░░░ [Probability Bar]            │       ║
║   │ • Rest advantage                         │       ║
║   │ • Goalie performance edge                │       ║
║   │ • Home ice                               │       ║
║   └─────────────────────────────────────────┘       ║
║                                                       ║
║   ┌─────────────────────────────────────────┐       ║
║   │ EDM @ VAN                         58%    │       ║
║   │ ▓▓▓▓▓▓░░░░ [Probability Bar]            │       ║
║   │ • Momentum advantage                     │       ║
║   │ • Back-to-back (EDM)                    │       ║
║   └─────────────────────────────────────────┘       ║
║                                                       ║
║   [See All Predictions →]                            ║
║                                                       ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║   HOW IT WORKS                                        ║
║                                                       ║
║   1️⃣ Collect Data                                    ║
║   204 features from NHL games                        ║
║                                                       ║
║   2️⃣ Train Model                                     ║
║   6 seasons of historical data                       ║
║                                                       ║
║   3️⃣ Predict Games                                   ║
║   Updated daily with new games                       ║
║                                                       ║
║   [Learn More About Our Methodology →]               ║
║                                                       ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║   MODEL PERFORMANCE                                   ║
║                                                       ║
║   [Chart: Accuracy over time]                        ║
║                                                       ║
║   Current Season: 55.97%                             ║
║   Historical Best: 60.89%                            ║
║   Edge over Baseline: +2.20pp                        ║
║                                                       ║
║   [View Full Performance Stats →]                    ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
```

---

**This is a MUCH more realistic V2.0 plan!**

Focus: Core predictions + X automation + clean UX
Timeline: 2-3 weeks
Complexity: Low (no auth, no payments, no complex backend)
Goal: Get something live that works and provides value

We can add complexity LATER once we prove the concept works.
