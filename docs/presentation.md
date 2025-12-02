# Puckcast: Turning Hockey Chaos into Signal

Story-first outline for a <10 minute deck. Copy is ready to paste; visuals are described with quick prompts. This is tailored for a sports analytics class: emphasize the process, modeling decisions, and the product impact. Keep URLs out of main slides; use clean visuals.

---

### Slide 1 — Why We Built Puckcast
**Copy:**  
Hockey is noisy. Odds swing with goalies, travel, and back-to-backs. We built Puckcast to turn daily chaos into clean, trustworthy probabilities.

**Visual prompt:**  
Hero image: goalie in crease with a subtle overlay of data bars/nodes.

---

### Slide 2 — Our Signal
**Copy:**  
Behind every prediction: 206 engineered features—rest, travel, rolling xG, special teams, goalie form, Elo. Trained on the last 3 seasons, calibrated to match real outcomes.

**Visual prompt:**  
Minimal flow: Data → Features → Model (LogReg + calibration) → JSON/API → Site.

---

### Slide 3 — Performance, Right Now
**Copy:**  
Holdout accuracy: 59.3% (vs 53.7% baseline). Log loss: 0.676, Brier: 0.240. Average edge: 16.1 pts over a coin flip.

**Visual prompt:**  
Three small cards: Accuracy vs Baseline, Log loss, Avg edge bar.

---

### Slide 4 — Daily Slate Experience
**Copy:**  
Clean, fast, scannable. We strip the clutter: updated timestamp, refined bars, 1–2 badges max (rest/goalie/injury).

**Visual prompt:**  
Mock prediction card: matchup, win % bars, tiny badges, updated time.

---

### Slide 5 — Explainability Where It Matters (Power v2)
**Copy:**  
Power Index v2 pairs movement arrows with 1–2 sentences on why: recent form, special teams, injuries, shot quality, strength of schedule.

**Visual prompt:**  
Ranked list with ↑/↓ arrows and a short one-line explanation per team.

---

### Slide 6 — Season Storylines (Sim Engine)
**Copy:**  
Daily simulations (5k–20k runs) give playoff/division/conference/Cup odds. One page, last-updated stamp, and probability bars you can trust.

**Visual prompt:**  
Table snippet with teams + playoff/division/Cup bars and tiny trend arrows.

---

### Slide 7 — Goalies: The Swing Factor
**Copy:**  
We pull expected/confirmed starters, rest, and inject goalie strength into the model. Light badges show “Confirmed” or “Likely” so edges aren’t blind to the crease.

**Visual prompt:**  
Goalie badge examples on a card: “Confirmed: Shesterkin” / “Likely: Saros”.

---

### Slide 8 — Performance Receipts
**Copy:**  
7-day and season accuracy at a glance. A hits/misses strip for the last 20–30 games. One calibration/reliability glimpse—no black boxes.

**Visual prompt:**  
Small chart/card: 7-day accuracy, season accuracy, simple calibration mini-plot.

---

### Slide 9 — Stability Under the Hood
**Copy:**  
Anti-stale checks. Timestamp validation. Retry logic on ingest. JSON completeness checks. We hardened the pipeline so you get fresh data, not surprises.

**Visual prompt:**  
Checklist graphic with green ticks.

---

### Slide 10 — Next Up (v7.1 Targets)
**Copy:**  
Goalie Page MVP. Past Slate Archive. Extra trend indicators for Power Index. Minor UX polish.

**Visual prompt:**  
Roadmap bar with “Now” (v7), “Next” (v7.1), “Later” (v8+).

---

### Slide 11 — Impact in Plain Language
**Copy:**  
For fans: faster, clearer edges.  
For analysts: calibrated probabilities with traceable factors.  
For the product: reliability + richer season context (sim engine + Power v2).

**Visual prompt:**  
Three benefit cards.

---

### Slide 12 — Close
**Copy:**  
Hockey is chaos; Puckcast makes it legible. Daily edges, honest receipts, and season odds that update with reality.

**Visual prompt:**  
Hero image echoing Slide 1 with a simple “puckcast.ai” tag.

---

## Visual Stubs (lightweight markdown “images” you can drop in slides)

**Slide 2 — Flow diagram:**
```
Data (MoneyPuck, Goalie pulls) → Features (rest/travel/xG/special teams/goalie/Elo) → Model (LogReg + isotonic) → JSON/API → Site
```

**Slide 3 — Performance cards:**
```
| Accuracy | Baseline |
| 59.3%    | 53.7%    |

| Log loss | Brier | Avg edge |
| 0.676    | 0.240 | 16.1 pts |
```

**Slide 4 — Prediction card (clean slate):**
```
DAL @ SEA   Updated 7:05 PM
Home 44%  | Away 56%
Badges: [Rest +1] [Confirmed: Oettinger]
```

**Slide 5 — Power v2 row:**
```
2. Rangers  ↑
Why: strong 5v5 form, PK > league, shot quality edge vs SOS.
```

**Slide 6 — Season sims table snippet:**
```
Team   Playoff   Division   Conf   Cup   Trend
NYR    88%       34%        18%    7%    ↑
DAL    84%       42%        15%    6%    →
TOR    81%       28%        14%    5%    ↓
(last updated: HH:MM ET, sims: 10k)
```

**Slide 8 — Performance snippet:**
```
7-day: 61.5%   Season: 59.3%
Hits (last 5): NYR>CAR, PIT>BUF, TOR>CBJ, DAL>SEA, CGY>TBL
Misses (last 5): STL<NJD, VAN<ANA, OTT<VGK, PHI<FLA, MIN<CHI
Calibration: points near diagonal (mini-plot placeholder)
```

**Slide 9 — Stability checklist:**
- ✅ Anti-stale timestamps
- ✅ Retry on ingest
- ✅ JSON completeness validation
- ✅ Freshness checks before publish

## Presenter notes (to weave the “story”)
- Start with the pain (“Hockey is noisy”), then the signal (features/model), then receipts (performance), then the experience (slate/power/sims), then the reliability (stability), then the near future (v7.1).
- Keep it conversational: “Here’s what we saw; here’s how we fixed it; here’s what you get.”
- Time budget: ~45–60 seconds per slide; skip live demos to stay under 10 minutes.


**Slide 10 — Roadmap bar:**
```
Now (v7): Sims, Power v2, Perf page, Goalie pipeline, Model refresh, Slate UX
Next (v7.1): Goalie Page MVP, Past Slate Archive, Power trend tweaks, Minor UX
Later (v8+): Matchup deep dive, Explainability chips, Team hubs, PP/PK dashboard, Rink effects, Ensembles
```
**Slide 11 — Impact cards:**
```
Fans: Faster, clearer edges
Analysts: Calibrated probs + traceable factors
Product: Reliable slate + season context (sims + Power v2)
```
