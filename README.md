# NiftyLens AI

AI-assisted research dashboard for Indian equities (NSE/BSE), powered by the community [Screener MCP](https://github.com/ashu017/screener-mcp).

> Independent research tool; not affiliated with Screener.in. Not investment advice and does not promise real-time quotes. Verify source data and comply with Screener.in terms.

## Features
- Screener fundamentals, typed ratios, financial statements, peer comparisons and quarterly results.
- Anonymous market screening via the MCP `screen_stocks` tool.
- Optional LangGraph + Gemini research workflow (server-side API key only).
- Responsive browser dashboard; no local LLM required.

## Architecture
Browser → FastAPI → Python MCP client → `npx screener-mcp` (stdio) → Screener.in.

## Local setup
Requirements: Python 3.11+, Node.js 18+, npm.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```
Open http://127.0.0.1:8000. First MCP startup downloads the npm package.

## Deploy
Dockerfile and Render blueprint are included. Connect this repo as a Render Web Service using Docker. Configure `GEMINI_API_KEY` optionally. The host needs outbound access to npm and Screener.in; check current Render plan limits. Deployment is not automatic until a hosting service is connected and configured.

## API
- `GET /api/health`, `GET /api/mcp/status`
- `GET /api/stocks/{symbol}` (fundamentals + ratios)
- `GET /api/stocks/{symbol}/financials`, `/peers`, `/quarters`
- `GET /api/stocks/{symbol}/chart?metric=Price&days=365`
- `POST /api/screen` body: `{"query":"Return on capital employed > 15 AND Market Capitalization > 10000","limit":25}`
- `POST /api/research/{symbol}` (requires Gemini key)

## MCP details
Uses the community `ashu017/screener-mcp` npm package (pinned by env var, default 0.2.0). Anonymous tools include fundamentals, financials, peers, charts and `screen_stocks`; `run_screen` requires Screener sign-in and is not exposed here.

## Responsible use
Screener MCP scrapes Screener.in. Respect its terms, rate limits and robots guidance; avoid frequent refreshes. Market data may be delayed, incomplete or unavailable. Do not use AI summaries as trading instructions.

MIT for this project's code. Third-party tools and source-site terms remain applicable.
