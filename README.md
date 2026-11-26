# Outlier Lab · AI Simple

Track top short-form outliers across creators in your niche, break down every video with full **Sandcastles-style frameworks** (beat-by-beat transcript, idea analysis, hook mad-lib, storytelling format & scriptwriting tactics, visual layout) plus **Dan Kennedy Magnetic Story Selling & Marketing Secrets** character audits, and generate remixed scripts in your brand voice.

**Zero required keys, zero cloud setup, zero AI subscriptions to get started.** Everything runs locally out of the box with `./setup.sh`. Optional scrapers (Apify / TokScript) and optional cloud hosting ("Go Live" on Vercel + Clerk) can be layered in whenever you want — never required.

![Setup](https://img.shields.io/badge/setup-1_command_local_start-ffc71d)
![No AI key](https://img.shields.io/badge/AI_key_required-no-brightgreen)
![Go Live](https://img.shields.io/badge/go_live-100%25_optional-1f1f1f)

## 60-Second Local Quickstart (No Accounts or Keys Required)

```bash
git clone https://github.com/Vibe-Marketer/outlier-lab.git
cd outlier-lab
./setup.sh
```

That's it. `./setup.sh` checks Python 3, builds the dashboard with full Sandcastles + Dan Kennedy breakdowns, starts the local studio server on `http://localhost:4747`, and opens it in your browser.

Out of the box (with **$0 spend and zero logins**), you immediately get:
- **Multi-Workspace Studio** (`AI Simple`, `Clickable Impact`, `All Workspaces`, plus unlimited custom workspaces)
- **Full 6-Tab Video Breakdown Studio** on every reel (Paragraph & Beat-by-Beat Transcript, Idea Analysis, Hook Mad-Lib & Alignment, Storytelling Format & Tactics, Visual Layout, Dan Kennedy 6-Dimension Magnetic Audit) + instant single-video URL/transcript analyzer
- **Ideas & Hooks Vault** (Shortlist, Viral Hook Vault, live Hook Genius Pre-Flight Checker, Curated Frameworks, Projects)
- **Content Strategy Audit & 4-Step AI Script Builder** (with Draft Fixer & workspace voice injection)
- **Dan Kennedy Character & Offer Builder** (5 Archetypes, 7 Magnetic Elements, James Bond Test, PROFITS bank)
- **Portable JSON Backup / Import** & CSV exports

## Optional Add-Ons (Never Required)

| Add-on | What it unlocks | Required? |
|---|---|---|
| **Python 3.10+** | Local studio + instant breakdowns | Built into macOS/Linux |
| **ffmpeg** (`brew install ffmpeg`) | Auto-extracting 3-sec muted autoplay hook clips | Optional |
| **Apify account** | Automated 28-day Instagram reel stats & creator profile scrapes | Optional |
| **TokScript API key** | Bulk spoken-word transcripts via MCP (no OpenAI/Claude key needed) | Optional |
| **GitHub Actions** | Scheduled background refreshes | Optional |
| **Vercel + Clerk ("Go Live")** | Publish static dashboard to a custom domain like `outlier.aisimple.co` | Optional |

## Optional: Enable Live Scraping & "Go Live" Hosting

Only do these steps when you want automated channel scrapes or a hosted URL.

### A. Enable local Admin scraping (optional)
Run `./setup.sh` (or `python3 serve.py`) and open `http://localhost:4747/admin`:
- Paste an **Apify token** (optional — only needed to scrape live creator stats) and/or **TokScript API key** (optional — for bulk transcripts).
- Add creator handles or single videos, pick a schedule, and click **Run refresh now**.

### B. Go Live on GitHub + Vercel (optional)
```bash
git add config.json .github/workflows/refresh.yml
git commit -m "My setup"
git push

# Optional: enable scheduled cloud refreshes in GitHub Actions
gh secret set APIFY_TOKEN
gh secret set TOKSCRIPT_API_KEY

# Optional: publish live to Vercel
vercel --prod
```

Vercel runs `export_site.py` to publish only `index.html`, `thumbs/`, and `clips/`. The local admin server (`serve.py`) never deploys publicly.

## How the cost stays low

The pipeline uses a **two-pass** approach:
- **Pass 1** (cheap, no transcripts): refreshes plays/likes/comments stats for all reels in your 28-day window
- **Pass 2**: fills transcripts through `https://api.tokscript.com/mcp`, reusing existing library exports first. Apify transcription is disabled; there is no paid transcription fallback.

The installed refresh limits stats to 40 Reels per creator, with Apify run caps of $1.50 for stats and $0.10 for profiles. Transcript usage is governed by the configured TokScript account. The installed Pro account includes unlimited transcripts; a free account is limited by TokScript. No purchases or plan upgrades happen in this application. Refresh scheduling starts in manual mode.

### TokScript transcripts and backfills

Create an API key in TokScript → Settings → API Keys, then set `TOKSCRIPT_API_KEY` in the private, gitignored `.env` file or process environment. Keep it server side. Add the same key as the GitHub Actions secret `TOKSCRIPT_API_KEY` for cloud refreshes.

In Admin, choose a list and click **Fill missing transcripts · TokScript**. This skips the stats scrape and rebuilds the local dashboard after the batch. Publishing that update to the public Vercel dashboard still requires committing and pushing it.

Or run the CLI:

```bash
python tokscript_backfill.py --build
# Small scoped batch:
python tokscript_backfill.py --handles kallaway tenfoldmarc --limit 10 --build
```

Backfills process outliers first, match transcripts by exact Instagram Reel ID, and preserve existing statistics and list memberships. Existing library transcripts are reused before submitting new jobs. Batches contain up to 50 URLs, with at most two retries for unavailable videos. Photo/carousel failures are not retried. Job IDs and JSON exports are cached under gitignored `.cache/tokscript/`; rerunning resumes known in-flight jobs and reimports saved exports. If a submit response is lost before a job ID is confirmed, the next run reconciles the library and blocks duplicate submissions until the uncertain request is resolved. The admin rejects overlapping transcript workers. Stats merges and transcript writes share a file lock and atomic JSON writes.

TokScript WEBVTT/SRT output is converted into readable spoken text. The dashboard labels the transcript provider, distinguishes spoken hooks from caption fallbacks, and counts ready transcripts by creator and list. Transcripts are machine generated and may contain recognition errors; music-only or visual-only Reels may have no usable spoken transcript.

Vercel runs `export_site.py` to publish only `index.html`, `thumbs/`, and `clips/`. The admin runs locally via `start.command` (or `.venv/bin/python serve.py`); it is not part of the hosted static dashboard.

## Managing your creator list

### Add creators without waiting for a scraper

Paste exact Instagram handles (or profile URLs) into **Add handles now**, up to 25 at once. Saving is immediate and does not require Apify to finish, or even an API token. Duplicate handles are merged into the selected list. Profile names, photos, and follower counts load in one background batch, with progress shown in the admin.

Name discovery uses **Find profiles** or Enter; typing no longer launches paid searches. The server returns a job immediately and the page polls for progress, so a slow scrape does not hold an HTTP connection open or block the admin. Cached results are reused for 24 hours. Interrupted background jobs resume their saved Apify run ID after a server restart; run submissions with uncertain outcomes are not blindly retried.

Profile batches are capped at $0.10 and name searches at $0.03. A separate rolling 24-hour cap reserves at most $0.50 for these admin lookups, including queued and failed submissions. Reaching this cap does **not** prevent saving handles. These limits are separate from the existing Reel-refresh stage caps. Refresh scheduling remains manual.

### Saved niche lists

The admin and dashboard offer **AI × DTC ecommerce**, **DTC agencies / creative**, **DTC ecommerce**, **AI broadly**, and **Marketing & sales**. The last list keeps broader copywriting, coaching, offers, and entrepreneurship content separate from ecommerce and technical AI. Choose a list in the admin before adding a creator; use the membership checkboxes to include the same creator in additional lists. Shared creators remain a single account in `config.json` and are scraped once per refresh.

Each list has its own dashboard view, creator chips, metrics, and research notes. Share a view with `?scope=ai-dtc`, `?scope=dtc-agencies`, `?scope=dtc-ecommerce`, or `?scope=ai`. The original sample creators remain in **All creators / demo**.

Turn off **Include in refreshes** to pause spending on an account while preserving its cached data. **Rebuild dashboard · free** applies membership changes without running an Apify actor. A local rebuild does not publish to Vercel; commit and push to publish it, as with other local changes.

**Run refresh now** refreshes only tracked creators in the selected list. The GitHub Actions manual workflow has the same list picker. From the terminal:

```bash
OUTLIER_SCOPE=ai-dtc .venv/bin/python refresh.py
```

The creator review separates topical fit and useful content from Instagram identity and recent Reel activity. The initial check used a maximum of five Reels per account in a 28-day window; zero results are inconclusive. Collaboration posts owned by another account are linked as evidence but excluded from personal outlier baselines. See [CREATOR-REVIEW.md](CREATOR-REVIEW.md) for the dated review and sources.

Run `python3 serve.py` anytime. The admin remembers everything — search and add new ones, remove old ones, change the schedule. Then `git add config.json && git commit && git push` to propagate the changes to GitHub Actions.

If you prefer the terminal, `python3 configure.py` also works.

## Architecture

```mermaid
flowchart LR
    Admin[Local Admin] --> Refresh[Refresh pipeline]
    Actions[Manual or scheduled GitHub Action] --> Refresh
    Apify[Apify: stats and profiles only] --> Refresh
    TokScript[TokScript MCP: library and transcripts] --> Refresh
    Refresh --> Data[Saved data and preview clips]
    Data --> Build[build.py]
    Build --> HTML[index.html]
    HTML --> Push[Commit and push]
    Push --> Vercel[Public dashboard on Vercel]
```

## Hosted sign-in

The hosted dashboard is configured for `https://outlier.aisimple.co` with the same production Clerk instance as `life.aisimple.co`. Vercel middleware checks a valid Clerk session on every dashboard and media request, then checks the user's verified primary email against the same three-account allowlist in `auth.js`. Missing credentials or Clerk errors fail closed. Deployment aliases redirect to the custom domain; direct `index.html` and media URLs are also protected, and authenticated content is not publicly cached.

Set `CLERK_SECRET_KEY` and `CLERK_PUBLISHABLE_KEY` in the Vercel production environment. The export embeds only the publishable key and a session-refresh client; the secret stays on the server. Local Python admin access remains through its existing localhost / private BB connection. The custom domain requires the DNS-only CNAME provided by Vercel in the Cloudflare zone before promotion.

Run `npm ci` and `npm run test:auth` for the hosted authorization checks. `vercel build --prod` builds the static export and middleware together.

## Files

| File | What it is |
|---|---|
| **`serve.py`** | Local admin server — run this to get the UI |
| **`admin.html`** | The admin UI (single page, no framework, served by serve.py) |
| `configure.py` | CLI alternative to the web admin (same job) |
| `refresh.py` | The pipeline orchestrator |
| `build.py` | Renders `index.html` from scraped data |
| `extract_clips.py` | ffmpeg helper for the 3-sec hook clips |
| `config.json` | Your creator list (committed; managed by the admin) |
| `tokscript.py` | Authenticated MCP client for TokScript |
| `tokscript_backfill.py` | Library reuse, bulk transcript jobs, and exports |
| `.env` | Apify and TokScript credentials (gitignored) |
| `.github/workflows/refresh.yml` | The cron job — edited by the admin's schedule picker |
| `vercel.json` | Vercel hosting config |
| `data/`, `thumbs/`, `clips/` | Generated content (committed so Vercel can serve it) |
| `index.html` | The dashboard (welcome page until first refresh runs) |

## Troubleshooting

**A scheduled run failed.** Check repo → Actions → click the failed run → look at "Run refresh pipeline" step. Most common cause:
- `APIFY_TOKEN` or `TOKSCRIPT_API_KEY` not set as a secret → set both, pasting only the credential at each prompt
- A handle in your config went private mid-week → remove via admin

**Apify returned 502.** Transient. `refresh.py` retries with exponential backoff automatically. If it still fails, trigger the workflow again.

**The dashboard shows old data.** Check that GitHub Actions actually committed + pushed (look at the latest commit on the repo). If yes, Vercel should auto-redeploy within seconds.

**My profile pictures aren't loading on the admin search results.** Instagram CDN sometimes blocks hotlinked images. The dashboard fixes this by downloading them locally on each refresh; the admin search shows them live so they occasionally 403. Click "Add" anyway — the lookup-and-store happens server-side.

## License

MIT — do what you want with this. Credit appreciated but not required.
