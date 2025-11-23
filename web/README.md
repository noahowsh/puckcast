# Web App (Next.js)

## Run locally
```bash
cd web
npm install
npm run dev  # http://localhost:3000
```

## Data feeds (statically imported)
- `src/data/todaysPredictions.json`
- `src/data/currentStandings.json`
- `src/data/goaliePulse.json`
- `src/data/modelInsights.json`

## API routes
- `/api/next-games` — fetches upcoming games (server-side) for the power board.
- `/api/predictions` — exposes predictions payload.

## Assets
- `public/social-card.png` — social sharing card
- `public/puckcastai.png` — favicon/base logo

## Components of note
- `components/TeamCrest.tsx` — renders team logos
- `components/PowerBoardClient.tsx` — client-side power board rendering

