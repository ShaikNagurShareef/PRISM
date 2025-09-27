# PRISM Frontend (React)

Enterprise-grade React frontend for PRISM with Chakra UI, Framer Motion, and full integration to the existing backends.

## Prerequisites
- Node.js 18+
- PRISM backend running at http://127.0.0.1:8000
- AutoRAG backend running at http://127.0.0.1:8001

## Setup
```bash
cd frontend
cp .env.local.example .env.local # or edit .env.local
npm install
npm run start
```

Update `.env.local` if your backend URLs differ:
```
VITE_PRISM_BACKEND_URL=http://127.0.0.1:8000
VITE_AUTORAG_API_BASE_URL=http://127.0.0.1:8001
```

## Scripts
- `npm run start` - dev server
- `npm run build` - production build
- `npm run preview` - preview production build

## Structure
- `src/api` - axios clients
- `src/state` - zustand store for app session state
- `src/pages` - Insights, Modeling, AutoRAG pages
- `src/components` - Sidebar (sources manager)
- `src/theme` - Chakra theme

## Notes
- The app mirrors Streamlit flows and calls the same endpoints, no Python files were changed.
- Session state persists locally in browser storage.

