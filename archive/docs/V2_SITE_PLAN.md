# 🚀 Puckcast V2.0 Site Plan - Massive Upgrade

**Created:** November 20, 2025
**Target Launch:** 4 weeks
**Goal:** Transform from internal dashboard → Professional prediction platform

---

## 🎯 Vision

Build a **best-in-class NHL prediction platform** that combines:
- Real-time predictions with live confidence intervals
- Professional analytics and visualizations
- Betting intelligence tools
- User accounts and subscription management
- Mobile-first responsive design
- **60.89% accuracy** (beating Vegas baseline)

---

## 📊 Current State Assessment

### What Exists Now ✅

**Backend:**
- 204 features, 60.89% accuracy model
- Expected Goals (xG) model (94.8% accuracy)
- Elo ratings, goalie tracking, schedule analysis
- NHL API integration with caching
- Python prediction pipeline

**Frontend:**
1. **Streamlit Dashboard** (dashboard.py)
   - Model performance metrics
   - Feature importance
   - Basic predictions view
   - Internal tool, not public-ready

2. **Next.js Web App** (web/)
   - Homepage with predictions
   - 6 pages (predictions, betting, performance, leaderboards, analytics, goalies)
   - Static JSON data updates
   - Basic Tailwind styling
   - Vercel deployment ready

### What's Missing ❌

**Critical Gaps:**
- No user authentication/accounts
- No subscription/payment system
- No historical prediction tracking
- No bet tracking/portfolio management
- No mobile app
- No real-time updates (WebSockets)
- No email notifications
- No API for partners
- Limited betting tools
- No model explainability for users
- No social features (leaderboards, contests)

---

## 🏗️ V2.0 Architecture

### Tech Stack

**Frontend:**
- **Framework:** Next.js 14 (App Router) ← Keep existing
- **Styling:** Tailwind CSS v4 + shadcn/ui components ← Upgrade
- **State:** React Query for server state
- **Charts:** Recharts + D3.js for advanced viz
- **Real-time:** WebSockets (Socket.io)
- **Mobile:** React Native (Phase 2)

**Backend:**
- **API:** Next.js API Routes + FastAPI Python service
- **Database:** PostgreSQL (Supabase)
- **Cache:** Redis for predictions
- **Auth:** Clerk or Supabase Auth
- **Payments:** Stripe
- **Hosting:** Vercel (frontend) + Railway (Python)
- **Email:** Resend

**Infrastructure:**
- **CI/CD:** GitHub Actions
- **Monitoring:** Vercel Analytics + Sentry
- **CDN:** Vercel Edge Network
- **Cron:** GitHub Actions daily predictions

---

## 📱 V2.0 Site Structure

### Public Pages (No Auth)

#### 1. **Landing Page** (/)
**Purpose:** Convert visitors → sign-ups

**Sections:**
- Hero with live accuracy metrics ticking up
- "Tonight's Game" preview (top 3 picks)
- Model credibility (backtest results, feature showcase)
- Pricing tiers
- Social proof (testimonials, media mentions)
- Feature comparison table
- FAQ
- Email capture CTA

**Key Improvements:**
- Animated accuracy counter
- Live prediction confidence meters
- "Beat the House" ROI calculator
- Interactive feature importance demo
- Mobile-optimized cards

#### 2. **About** (/about)
- Model methodology
- Feature engineering deep dive
- Team/founder story
- Academic references
- Accuracy history chart

#### 3. **Pricing** (/pricing)
- Free tier (3 predictions/day, ads)
- Pro tier ($19.99/mo) - Unlimited predictions, bet tracker, alerts
- Elite tier ($49.99/mo) - API access, early access, Discord
- Annual discounts (20% off)
- "What's included" comparison

#### 4. **Blog** (/blog)
- Model performance updates
- Feature spotlights
- Betting strategy guides
- NHL analytics insights
- SEO-optimized content

### Protected Pages (Auth Required)

#### 5. **Dashboard** (/dashboard)
**Purpose:** Daily prediction hub

**Sections:**
- Today's Games (card grid)
  - Live odds comparison (if available)
  - Confidence indicator
  - Key factors (rest, goalie, momentum)
  - "Why this pick?" explainability
- My Tracked Bets (if tracking enabled)
- Recent Performance (your picks vs model)
- Quick Stats (accuracy, ROI, streak)

**Features:**
- Filter by confidence threshold
- Sort by edge over Vegas
- Toggle between ML/OL/Totals
- Export to CSV
- Share individual predictions

#### 6. **Predictions** (/predictions)
**Purpose:** Full game analysis

**For Each Game:**
- **Overview Card**
  - Teams, time, venue
  - Prediction: Home 65% | Away 35%
  - Vegas line comparison
  - Edge calculation

- **Key Factors** (Visual breakdown)
  - Top 5 features driving prediction
  - Bar chart showing feature contributions
  - Plain English explanations

- **Head-to-Head Stats**
  - Recent form (last 10 games)
  - Season stats comparison
  - Injury reports
  - Starting goalies

- **Historical Matchups**
  - Last 5 meetings
  - Model accuracy on these teams

- **Betting Recommendation**
  - Kelly Criterion bet size
  - Risk level (Low/Med/High)
  - Confidence interval

#### 7. **Analytics** (/analytics)
**Purpose:** Deep dive into model performance

**Sections:**
- **Model Performance**
  - Accuracy over time (line chart)
  - ROC-AUC curve
  - Calibration plot
  - Confusion matrix
  - Brier score

- **Feature Importance**
  - Top 50 features ranked
  - Interactive feature explorer
  - Category breakdown (Schedule/Goalie/Momentum)
  - Feature correlation heatmap

- **Team Analysis**
  - Accuracy by team
  - Hardest teams to predict
  - Home vs away performance
  - Conference/division breakdowns

- **Situational Accuracy**
  - Back-to-back games
  - Rest advantages
  - Rivalry games
  - Playoff implications

#### 8. **Betting Tools** (/betting)
**Purpose:** Bankroll management and strategy

**Tools:**
- **Bet Tracker**
  - Log bets (manual or auto from predictions)
  - Track: Date, teams, odds, stake, result
  - P&L dashboard
  - ROI by month/season
  - Win rate vs expected

- **Kelly Calculator**
  - Input: Probability, odds, bankroll
  - Output: Optimal bet size
  - Fractional Kelly options

- **Bankroll Manager**
  - Set starting bankroll
  - Track growth over time
  - Drawdown analysis
  - Risk of ruin calculator

- **Strategy Simulator**
  - Backtest different staking strategies
  - Compare flat stake vs Kelly vs Martingale
  - See historical performance

#### 9. **Leaderboards** (/leaderboards)
**Purpose:** Community and gamification

**Boards:**
- **Model Accuracy Leaderboard**
  - Best performing picks this week/month/season
  - Sorted by confidence * accuracy

- **User Leaderboard** (if tracking bets)
  - Top users by ROI
  - Top by win rate
  - Longest streak

- **Team Power Rankings**
  - Puckcast power index
  - Recent form (3/5/10 games)
  - Strength of schedule
  - Movement from last week

- **Goalie Rankings**
  - GSAx leaders
  - Save % leaders
  - Recent form
  - Starts vs backup

#### 10. **Goalies** (/goalies)
**Purpose:** Goalie-specific insights

**Features:**
- **Goalie Pulse Cards**
  - Starter confirmation status
  - Recent performance (L5 games)
  - Season stats
  - vs Opponent history
  - Rest days

- **Starter Alerts**
  - Real-time notifications when starter confirmed
  - Email/SMS/Discord integration

- **Goalie Matchup Matrix**
  - Best goalie matchups tonight
  - Expected saves
  - Over/under recommendations

#### 11. **Performance** (/performance)
**Purpose:** Track your usage of the model

**Metrics:**
- Your prediction accuracy
- Picks by confidence level
- Best/worst days
- ROI if you bet $100 per pick
- Compared to model baseline
- Compared to other users

#### 12. **Settings** (/settings)
- Account info
- Subscription management
- Notification preferences
- Betting unit size
- API keys (Elite tier)
- Email preferences
- Discord connection

---

## 🎨 Design Principles

### Visual Identity

**Color Palette:**
- Primary: Deep Blue (#1E3A8A) - Trust, intelligence
- Secondary: Ice Blue (#3B82F6) - Action, energy
- Accent: Bright Orange (#F97316) - Highlights, alerts
- Success: Green (#10B981) - Wins, positive
- Warning: Yellow (#FBBF24) - Caution
- Danger: Red (#EF4444) - Losses, high risk
- Dark: Charcoal (#1F2937) - Text, backgrounds
- Light: Off-white (#F9FAFB) - Backgrounds

**Typography:**
- Headings: Inter Bold
- Body: Inter Regular
- Monospace: JetBrains Mono (stats, odds)

**Components:**
- Card-based layout (shadcn/ui)
- Glassmorphism for premium features
- Smooth animations (Framer Motion)
- Loading skeletons for all data
- Toast notifications for actions

### Mobile-First

- Touch-friendly tap targets
- Swipe gestures for game cards
- Bottom navigation on mobile
- Pull-to-refresh
- Offline mode (cached predictions)

---

## 💰 Monetization Strategy

### Pricing Tiers

#### Free Tier
- 3 predictions per day
- Basic accuracy metrics
- Ads displayed
- Limited historical data (7 days)
- No bet tracking

#### Pro Tier ($19.99/month)
- Unlimited predictions
- Bet tracker & bankroll manager
- Email alerts (daily digest)
- Historical data (full season)
- No ads
- Kelly calculator
- Discord access

#### Elite Tier ($49.99/month)
- Everything in Pro
- API access (100 calls/day)
- Real-time starter alerts (SMS)
- Early access to features
- Priority support
- Model ensemble (multiple models)
- Custom confidence thresholds

#### Annual Discount
- Pro: $199/year (17% off)
- Elite: $499/year (17% off)

### Revenue Targets
- **Month 1:** 50 users → $1,000 MRR
- **Month 3:** 200 users → $4,000 MRR
- **Month 6:** 500 users → $10,000 MRR
- **Year 1:** 2,000 users → $40,000 MRR

---

## 🚀 Development Phases

### Phase 1: Foundation (Week 1-2)

**Goals:**
- Set up database schema
- Implement authentication
- Build core UI components
- Migrate existing pages to new design

**Tasks:**
1. Set up Supabase (PostgreSQL + Auth)
2. Define database schema:
   - users
   - predictions (historical)
   - bets (user tracking)
   - model_performance
   - goalie_confirmations
3. Install shadcn/ui components
4. Create design system (colors, fonts, spacing)
5. Build reusable components:
   - PredictionCard v2
   - StatsBar
   - ConfidenceMeter
   - FeatureBreakdown
   - BettingWidget
6. Implement auth flow (sign up, login, password reset)
7. Migrate existing pages to new design
8. Set up Stripe integration

### Phase 2: Core Features (Week 3-4)

**Goals:**
- Implement bet tracking
- Build analytics dashboards
- Add real-time updates
- Launch leaderboards

**Tasks:**
1. Build bet tracker CRUD
2. Implement bankroll manager
3. Create Kelly calculator
4. Build analytics dashboards:
   - Model performance over time
   - Feature importance
   - Team-specific accuracy
5. Add WebSocket support for live updates
6. Implement email notifications (Resend)
7. Build user leaderboards
8. Add goalie confirmation alerts
9. Create API endpoints for Elite users
10. Build admin panel for content management

### Phase 3: Polish & Launch (Week 5-6)

**Goals:**
- Testing and bug fixes
- Performance optimization
- SEO and content
- Soft launch

**Tasks:**
1. Comprehensive testing (E2E with Playwright)
2. Performance optimization:
   - Image optimization
   - Code splitting
   - Database query optimization
   - Redis caching
3. SEO optimization:
   - Meta tags
   - Sitemap
   - Blog content
   - Schema markup
4. Content creation:
   - About page
   - Methodology docs
   - Blog posts (5 initial)
   - FAQ
5. Email templates (welcome, alerts, digests)
6. Soft launch (beta users)
7. Collect feedback
8. Iterate

### Phase 4: Growth (Post-Launch)

**Goals:**
- User acquisition
- Feature expansion
- Mobile app

**Tasks:**
1. Marketing:
   - Reddit (r/sportsbook)
   - Twitter/X presence
   - YouTube explainer videos
   - Affiliate program
2. Feature additions:
   - Player prop predictions
   - Parlay builder
   - Live in-game updates
   - Discord bot
3. Mobile app (React Native):
   - iOS + Android
   - Push notifications
   - Simplified UI
4. Partnership opportunities:
   - Betting platforms
   - Media outlets
   - NHL content creators

---

## 📊 Success Metrics

### Technical KPIs
- **Uptime:** 99.9%
- **Page Load:** < 2s (p95)
- **API Response:** < 500ms (p95)
- **Prediction Accuracy:** 60%+ (maintain)
- **Data Freshness:** < 1 hour

### Business KPIs
- **User Growth:** 20% MoM
- **Conversion Rate:** 5% (free → paid)
- **Churn Rate:** < 10% monthly
- **MRR Growth:** 30% MoM
- **CAC:** < $50
- **LTV:CAC Ratio:** > 3:1

### Engagement KPIs
- **DAU/MAU:** > 30%
- **Session Duration:** > 5 min avg
- **Predictions Viewed:** > 10 per session
- **Return Rate:** > 60% (7-day)
- **NPS Score:** > 40

---

## 🔐 Data & Privacy

### Data Collection
- User account info (email, name)
- Betting history (if tracking enabled)
- Usage analytics (anonymous)
- Model performance metrics

### Privacy Commitments
- GDPR compliant
- No selling user data
- Opt-in for marketing emails
- Data export on request
- Account deletion support
- Secure payment processing (PCI compliant via Stripe)

---

## 🎯 Competitive Advantages

### vs MoneyPuck
- Real-time predictions (they're historical only)
- Betting tools integration
- User accounts and tracking
- Mobile app
- Better UX

### vs Vegas Lines
- Transparent methodology
- Explainable predictions
- Higher accuracy on select games
- No house edge

### vs Other NHL Models
- Custom xG model (94.8% accuracy)
- 204 engineered features
- Goalie-specific tracking
- Schedule intelligence
- Community features

---

## 🛠️ Technical Implementation Notes

### Database Schema (PostgreSQL)

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  tier TEXT DEFAULT 'free', -- free, pro, elite
  stripe_customer_id TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Predictions (historical)
CREATE TABLE predictions (
  id SERIAL PRIMARY KEY,
  game_id TEXT NOT NULL,
  game_date DATE NOT NULL,
  home_team TEXT NOT NULL,
  away_team TEXT NOT NULL,
  home_win_prob FLOAT NOT NULL,
  vegas_line FLOAT,
  edge FLOAT,
  actual_home_win BOOLEAN,
  correct BOOLEAN,
  confidence TEXT, -- low, medium, high
  top_features JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- User Bets
CREATE TABLE bets (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  prediction_id INT REFERENCES predictions(id),
  bet_type TEXT, -- ml, spread, total
  stake FLOAT NOT NULL,
  odds FLOAT NOT NULL,
  result TEXT, -- pending, win, loss, push
  profit FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Goalie Confirmations
CREATE TABLE goalie_confirmations (
  id SERIAL PRIMARY KEY,
  game_id TEXT NOT NULL,
  team TEXT NOT NULL,
  goalie_name TEXT NOT NULL,
  confirmed_at TIMESTAMP NOT NULL,
  source TEXT -- nhl_api, twitter, manual
);

-- User Notifications
CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  type TEXT, -- goalie_confirmed, daily_digest, bet_result
  content JSONB,
  read BOOLEAN DEFAULT FALSE,
  sent_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints (FastAPI)

```python
# Predictions
GET  /api/v2/predictions/today
GET  /api/v2/predictions/{game_id}
GET  /api/v2/predictions/historical?start_date={date}&end_date={date}

# Model
GET  /api/v2/model/performance
GET  /api/v2/model/features
GET  /api/v2/model/accuracy?team={abbrev}

# Betting
POST /api/v2/bets
GET  /api/v2/bets?user_id={id}
GET  /api/v2/betting/kelly?prob={p}&odds={o}&bankroll={b}
GET  /api/v2/betting/portfolio?user_id={id}

# Goalies
GET  /api/v2/goalies/confirmations?date={date}
GET  /api/v2/goalies/{player_id}/stats

# Leaderboards
GET  /api/v2/leaderboards/users?metric={roi|accuracy|streak}
GET  /api/v2/leaderboards/teams/power
GET  /api/v2/leaderboards/goalies

# User
GET  /api/v2/user/profile
PUT  /api/v2/user/settings
GET  /api/v2/user/stats
```

### Caching Strategy (Redis)

```
# Today's predictions (TTL: 1 hour)
predictions:today:{date}

# Model performance (TTL: 24 hours)
model:performance:{season}

# Goalie confirmations (TTL: 30 min)
goalies:confirmations:{date}

# User profile (TTL: 5 min)
user:profile:{user_id}

# Leaderboards (TTL: 15 min)
leaderboard:{type}:{period}
```

---

## 📝 Content Strategy

### Blog Post Ideas
1. "How Puckcast Beats Vegas: A Deep Dive"
2. "The Science of Expected Goals (xG)"
3. "Why Schedule Rest Matters More Than You Think"
4. "Top 10 Features Predicting NHL Games"
5. "Kelly Criterion for Beginners"
6. "Goalie Performance Metrics Explained"
7. "Back-to-Back Games: The Hidden Edge"
8. "2024-25 Season Predictions Review"
9. "Building an NHL Prediction Model from Scratch"
10. "Betting Bankroll Management 101"

### Video Content
- Model explainer (3 min)
- Site walkthrough (5 min)
- How to track bets (2 min)
- Kelly calculator tutorial (3 min)
- Weekly picks show (10 min episodes)

---

## 🚦 Go-Live Checklist

### Pre-Launch
- [ ] All pages responsive (mobile/tablet/desktop)
- [ ] Auth flow tested (sign up, login, reset)
- [ ] Payment integration tested (Stripe test mode)
- [ ] Database backups configured
- [ ] Monitoring set up (Sentry, Vercel Analytics)
- [ ] Email templates created
- [ ] API rate limiting implemented
- [ ] Terms of Service written
- [ ] Privacy Policy written
- [ ] FAQ populated
- [ ] 5 blog posts published
- [ ] SEO meta tags added
- [ ] Sitemap generated
- [ ] Google Analytics configured
- [ ] Error pages (404, 500)

### Launch Day
- [ ] Switch Stripe to live mode
- [ ] Enable email notifications
- [ ] Announce on Twitter/Reddit
- [ ] Post in Discord communities
- [ ] Monitor errors closely
- [ ] Respond to user feedback
- [ ] Track conversion funnel
- [ ] Monitor server load

### Post-Launch (Week 1)
- [ ] Daily accuracy check
- [ ] User feedback survey
- [ ] Bug fixes as needed
- [ ] Performance optimization
- [ ] Content marketing push
- [ ] Influencer outreach
- [ ] Media pitches

---

## 🎓 Learning & Iteration

### User Research
- Conduct user interviews (10 users)
- Track heatmaps (Hotjar)
- A/B test pricing page
- Survey conversion drop-offs
- Monitor support tickets

### Model Improvements
- Add 6 seasons of data (2018-2024)
- Re-enable H2H matchup features
- Integrate real-time goalie confirmations
- Add player injury impact
- Implement model ensemble

---

## 💡 Future Expansion Ideas

### Phase 5+ (6-12 months)
- **Player Props:** Goals, assists, shots predictions
- **Live Betting:** In-game prediction updates
- **Parlay Builder:** Optimal combination finder
- **Discord Bot:** Predictions in your server
- **Telegram Bot:** Instant alerts
- **Chrome Extension:** Overlay on betting sites
- **API for Partners:** White-label predictions
- **Multi-Sport:** NBA, MLB, NFL models
- **Social Features:** Follow other users, contests
- **Custom Models:** Let users weight features

---

## 📞 Support & Community

### Support Channels
- Email: support@puckcast.ai
- Discord: discord.gg/puckcast
- Twitter: @puckcast_ai
- Help Center: docs.puckcast.ai

### Community Guidelines
- No spam or self-promotion
- Respectful betting discussion
- Share wins AND losses
- Help other users
- Report bugs/issues

---

## 🎯 Success Vision (1 Year)

**By November 2026:**
- 2,000+ paying users
- $40K+ MRR
- 62%+ prediction accuracy (with more data)
- Mobile apps on iOS & Android
- Featured in sports media
- Partnership with betting platform
- Active Discord community (5K+ members)
- Recognized as best NHL prediction tool

---

**Ready to build the future of NHL predictions! 🏒**
