# X/Twitter Post Types Reference

Complete guide to all available post types for maximum engagement.

## 📅 Daily Scheduled Posts (Automatic)

### Morning Preview (8:00 AM ET)
**Command**: `--post-type morning_preview`

Shows today's top picks with probabilities and team hashtags.
- 3 variants (A/B testing)
- Auto-tags both teams
- Displays win probabilities

### Afternoon Update (2:00 PM ET)
**Command**: `--post-type afternoon_update`

Game count and high-confidence picks.
- 2 variants
- Highlights A/B grade games

### Evening Recap (8:00 PM ET)
**Command**: `--post-type evening_recap`

Tomorrow preview tease.
- 2 variants
- Builds anticipation

---

## 🎯 High-Engagement Posts (Manual/Strategic)

### 1. Game of the Night 🔥
**Command**: `--post-type game_of_night`

**Example Output:**
```
🔥 Game of the Night
Puckcast Model Confidence: 71%

NYR @ CAR — 7:00 PM
Key Factors:
• xG Differential last 5: +0.43
• Goaltending edge: CAR
• Shot share: NYR trending down

Full slate → puckcast.ai

#NYR #Canes #NHL
```

**When to use**: 1x daily, highlight the best matchup

---

### 2. Upset Watch 🚨
**Command**: `--post-type upset_watch`

**Example Output:**
```
🚨 Upset Watch
Our model gives WPG a 41% chance vs COL tonight.

The market sees Colorado as heavy favorites — but…
• Rest advantage
• xG trend spike
• Goaltending matchup

We're watching this one closely.

puckcast.ai

#GoJetsGo #GoAvsGo #NHL
```

**When to use**: When underdog has 35-45% win probability
**Why it works**: Controversy drives comments

---

### 3. Team Surging 📈
**Command**: `--post-type team_surging`

**Example Output:**
```
📈 Surging Team: Florida Panthers

Puckcast Power Index last 10 games:
74 → 81 (+7)

• Strong 5v5 play
• Shots against trending down
• Goaltending stabilizing

puckcast.ai

#FlaPanthers #NHL
```

**When to use**: When team's power score increases 5+ points
**Why it works**: Fans love positive team content

---

### 4. Team Dropping 📉
**Command**: `--post-type team_dropping`

**Example Output:**
```
📉 Team in Decline: Colorado Avalanche

Power Index drop: -8 in 7 games

• High-danger chances allowed climbing
• Penalty kill collapsing
• Goalie form inconsistent

puckcast.ai

#GoAvsGo #NHL
```

**When to use**: When team's power score drops 5+ points
**Why it works**: Fans get defensive → massive engagement

---

### 5. Bold Predictions 🔮
**Command**: `--post-type bold_predictions`

**Example Output:**
```
🔮 5 Bold Predictions for the Week

Most underrated: Detroit Red Wings
Dark horse: Seattle Kraken
Most likely upset: CHI over CAR
Going 3-0: Florida Panthers
Most likely to disappoint: Colorado Avalanche

Full analysis: puckcast.ai

#NHL #HockeyTwitter
```

**When to use**: Monday mornings
**Why it works**: Builds personality and authority

---

### 6. Team Spotlight 🔍
**Command**: `--post-type team_spotlight`

**Example Output:**
```
🔍 Team Spotlight: Detroit Red Wings

• Puckcast Rank: #11
• Power Index: 73
• Last 10 Accuracy: 7-3
• Trend: Upward

The model says: Detroit is better than their record.

puckcast.ai

#LGRW #NHL
```

**When to use**: Rotate through all 32 teams (1 per day)
**Why it works**: Targets specific fanbases

---

### 7. Yesterday's Surprises 🎲
**Command**: `--post-type yesterdays_surprises`

**Example Output:**
```
Last night's surprises according to our model:

• NYI beat FLA (42% win prob)
• CHI beat MIN (39% win prob)
• DAL over CAR (48% win prob)

NHL chaos never dies. 🏒

puckcast.ai

#NHL #HockeyTwitter
```

**When to use**: Every morning with results
**Why it works**: Low-effort, always performs

---

### 8. Weekly Power Index 📊
**Command**: `--post-type weekly_power_index`

**Example Output:**
```
📊 Weekly Power Index

Top 5:
1️⃣ Colorado Avalanche
2️⃣ Tampa Bay Lightning
3️⃣ Carolina Hurricanes
4️⃣ Florida Panthers
5️⃣ Dallas Stars

Full 32-team rankings: puckcast.ai

#NHL #HockeyTwitter
```

**When to use**: Mondays
**Why it works**: Flagship weekly content

---

### 9. Overrated Poll 🗳️
**Command**: `--post-type overrated_poll`

**Example Output:**
```
Who's the most overrated team right now?

⬜ Toronto Maple Leafs
⬜ Edmonton Oilers
⬜ New York Rangers
⬜ Dallas Stars

Reply with your pick 👇

puckcast.ai

#NHL #HockeyTwitter
```

**When to use**: 2-3x per week
**Why it works**: Polls drive wild engagement

---

### 10. Model Accountability ✅
**Command**: `--post-type model_accountability`

**Example Output:**
```
Did the model get it right?

We had:
NYR 59% over PIT

Final score:
NYR 4 – 2 PIT

We'll take that W. 😎

puckcast.ai

#NYR #LetsGoPens #NHL
```

**When to use**: After big games with results
**Why it works**: Fans love accountability

---

## 🎨 Bonus Quick-Hit Posts

### Micro-Insights 💡
**Command**: `--post-type micro_insights`

Auto-generates insights:
- High confidence picks
- Big edges detected
- Heavy favorites/underdogs
- Power index rankings

**When to use**: Fill gaps between scheduled posts

---

### Fun Fact 🎯
**Command**: `--post-type fun_fact`

**Example Output:**
```
Fun Fact:
The Rangers have outshot opponents in 13 of their last 15 games.

puckcast.ai

#NYR #NHL
```

**When to use**: Anytime for quick engagement

---

## 📆 Recommended Posting Schedule

**Daily:**
- 8:00 AM: Morning Preview (auto)
- 9:00 AM: Yesterday's Surprises
- 11:00 AM: Micro-Insight or Fun Fact
- 2:00 PM: Afternoon Update (auto)
- 5:00 PM: Game of the Night
- 7:00 PM: Upset Watch (if applicable)
- 8:00 PM: Evening Recap (auto)

**Weekly:**
- Monday: Bold Predictions + Weekly Power Index
- Tuesday-Sunday: Team Spotlight (rotate teams)
- 2-3x/week: Overrated Poll

**As Needed:**
- Team Surging: When +5 power score change
- Team Dropping: When -5 power score change
- Model Accountability: After marquee games

---

## 🚀 Usage

### Manual Posting
```bash
python scripts/post_to_twitter.py --post-type game_of_night --site-url https://puckcast.ai
```

### Via GitHub Actions
1. Go to **Actions** tab
2. **X/Twitter Posting Automation** → **Run workflow**
3. Select post type from dropdown
4. Click **Run workflow**

---

## 💡 Pro Tips

1. **Team hashtags drive discovery** - Every team-specific post gets seen by that fanbase
2. **Controversy = engagement** - "Team Dropping" and "Overrated Poll" posts blow up
3. **Accountability builds trust** - "Did the Model Get It Right?" posts show transparency
4. **Consistency matters** - Stick to the schedule, fans will expect your posts
5. **Timing is everything** - Post "Game of Night" 2-3 hours before puck drop

---

Ready to dominate X/Twitter! 🚀
