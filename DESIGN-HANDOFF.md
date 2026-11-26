# Outlier Lab — AI Simple Studio, Sandcastles Breakdown & Dan Kennedy Handoff

This document maps the **AI Simple Outlier Lab v2** frontend (`build.py` → `index.html`, `admin.html`, `auth.js`), local studio server (`serve.py`), and zero-friction launcher (`setup.sh`) so any collaborating engineer/agent can extend real-time scraping or OAuth without disturbing the visual system or built-in deterministic breakdown engine.

## Brand System Tokens (`:root` in `build.py` & `admin.html`)

- **Display font**: `Sora` (`font-weight: 400`, `letter-spacing: -0.05em`)
- **UI / Body font**: `Manrope` (`font-weight: 400–800`)
- **Mono font**: `Space Mono`
- **Primary Brand Yellow**: `--yellow: #ffc71d` (hover `--yellow-hover: #f0b800`, soft `--yellow-soft: #fff2ba`, tint `--yellow-tint: #fff8da`, accessible ink `--yellow-ink: #856000`)
- **Surfaces**: `--paper: #f5f4ef`, `--surface: #ffffff`, `--charcoal: #1f1f1f`
- **Signature AI Simple Card Tones**: `--lavender: #f0e5ff`, `--sage: #eaf3e3`, `--cream: #f9f3e5`, `--yellow-soft: #fff2ba`
- **Outlier Bands**:
  - Breakout (`≥15×`): `#d4276b` on `#fce8f0`
  - Replicable (`5–15×`): `#151515` on `#ffc71d`
  - Working (`2–5×`): `#2e7d52` on `#eaf3e3`
  - Normal (`<2×`): `#686469` on `#f5f4ef`

## Navigation & 6-Tab Studio Architecture

URL query params are synced automatically: `?workspace=<id>&tab=<today|feed|ideas|strategy|character|channels>&scope=<scope-id>`

| Tab ID | Panel ID | Purpose |
|---|---|---|
| `today` | `#panel-today` | Landing briefing: active workspace + Character/Offer badge, **Top 5 applicable outliers** (`[data-slot="top-outliers"]`), **The Success Formula** shuffler, 5 KPIs, dual quick-action banners |
| `feed` | `#panel-feed` | Full searchable/sortable Outlier Feed (Table + 9:16 Grid), niche list pills, creator chips, band + **Hook Format + Storytelling Format + Topic** dropdown filters, studied/hidden toggles, CSV export |
| `ideas` | `#panel-ideas` | Sandcastles-style **Ideas Inbox & Shortlist**, **Viral Hook Vault** + **Hook Genius Pre-Flight Checker** (live 5-point scoring), **Curated Collections & Frameworks**, and **Projects** folders |
| `strategy` | `#panel-strategy` | **Content Strategy Audit** (Topics / Hooks / Storytelling Formats / Scriptwriting Tactics / Dan Kennedy Elements breakdown charts + drilldowns) + **4-Step AI Script Builder & Draft Fixer** + Saved Scripts library |
| `character` | `#panel-character` | **Dan Kennedy Magnetic Story Selling & Marketing Secrets** workspace profile: 2-Minute Offer Clarity, 5 Archetypes, Superhero Identity, Mighty Theme, Stand FOR/AGAINST, **7 Magnetic Elements**, **James Bond Test (7 repeatable traits)**, **PROFITS** language bank, Writing Style |
| `channels` | `#panel-channels` | **Add Single Video** (URL + optional transcript → instant 6-tab breakdown) + **Track Entire Channel**, Tracked Channel Roster, **Connect My Socials & Own Outliers**, **Zero-Friction Setup & Optional Go-Live** guide, and Portable JSON Backup/Import |

## Full 6-Tab Video Breakdown Studio (`<dialog id="reel-dialog">`)

Every reel in `index.html` (including all 410 scraped reels + any user-pasted single video) carries a deterministic `breakdown` payload generated at build time by `analyze_reel()` in `build.py` (or pre-populated from `p["breakdown"]` if supplied by an LLM/API):

1. **Transcript**: Paragraph view + **Beat-by-Beat timestamped cards** (Hook / Context / Proof / Payoff / CTA) with 1-click copy.
2. **Idea Analysis**: Core Concept, Why It Worked, Core Emotion/Driver, Target Audience, plus **Personalized Remixes** tailored to the active workspace's Character & Offer.
3. **Hook**: Exact Spoken Hook, **Mad-Lib Fill-in-the-Blank Formula**, Hook Format classification, 3-Second Alignment Check, Hook Score `/10`, and 1-click Save to Hook Vault.
4. **Storytelling Format**: Primary Format, Structural Arc steps, **Scriptwriting Tactics** chips, Pacing/WPM & Retention Engine analysis.
5. **Visual Layout**: Framing & Shot Structure, Text-on-Screen & B-Roll cues, Editing Cadence, and Production Difficulty.
6. **Dan Kennedy Audit**: 6-Dimension Magnetic Content Audit (`Character vs Plot`, `Polarization`, `Magnification`, `Regis Context Anchor`, `Core Story Advancement`, `Character Deficit Score /12`) + **7 Magnetic Elements** presence matrix + 1-click "Rewrite With My Character".

Keyboard shortcuts inside the modal: `←`/`→` (Prev/Next video), `C` (Create Script), `S` (Shortlist), `A` (Mark Analyzed), `H` (Save Hook), `E` (Mark Executed), `O` (Open Original), `R` (Copy Remix Prompt).

## Local Server Endpoints (`serve.py`) & Zero-Friction Launcher (`setup.sh`)

- Run `./setup.sh` for a 1-command local start (no cloud accounts, DB, Clerk, or AI keys required).
- `serve.py` exposes:
  - `GET /api/state` — returns `config`, `creators`, `scopes`, `workspaces`, `singleVideos`, `schedule`, and status flags.
  - `POST /api/workspaces` — persists custom workspaces (including full Dan Kennedy Character & Offer profiles) into `config.json` under `CONFIG_LOCK`.
  - `POST /api/videos/analyze` — persists single-video submissions into `config.json["singleVideos"]` under `CONFIG_LOCK`.
  - `POST /api/creators/import` — immediate handle import into `config.json`.

## Frontend Integration Hooks (`window.OUTLIER_APP` & `CustomEvent`s)

| Event Name | `event.detail` Payload | Backend Endpoint |
|---|---|---|
| `outlier:add-video` | `{ id, url, platform, workspace, tag, transcript, breakdown, createdAt }` | `POST /api/videos/analyze` (already wired on localhost!) |
| `outlier:add-channel` | `{ id, handles, platform, workspace, scope, status, live, createdAt }` | `POST /api/creators/import` (already wired on localhost!) |
| `outlier:create-workspace` | `{ id, name, initials, accent, accentInk, tagline, scopes, character, socials }` | `POST /api/workspaces` (already wired on localhost!) |
| `outlier:save-character` | `{ workspaceId, character }` | `POST /api/workspaces` (already wired on localhost!) |
| `outlier:connect-social` | `{ workspaceId, platform, handle }` | `POST /api/socials/connect` (optional OAuth) |
| `outlier:sync-social` | `{ workspaceId }` | `POST /api/socials/sync` |
| `outlier:workspace-change` | `{ workspace }` | Optional analytics / server state sync |
| `outlier:tab-change` | `{ tab, workspace }` | Optional lazy fetch |

### Programmatic API on `window.OUTLIER_APP`

- `window.OUTLIER_APP.getState()` — returns current workspace, all workspaces, active tab, scope, shortlist, hook vault, projects, scripts, single videos, and connected social overrides.
- `window.OUTLIER_APP.selectWorkspace(workspaceId)` — switches workspace and re-renders all 6 tabs.
- `window.OUTLIER_APP.setActiveTab(tabId)` — switches between `'today' | 'feed' | 'ideas' | 'strategy' | 'character' | 'channels'`.
- `window.OUTLIER_APP.openQuickAdd('video' | 'channel')` — opens the native `<dialog id="quick-add-dialog">`.
- `window.OUTLIER_APP.openReelModal(shortCode, initialTab?)` — opens the 6-tab `<dialog id="reel-dialog">` breakdown studio.
- `window.OUTLIER_APP.setOwnOutliers(workspaceId, items)` — hydrates **Your Own Top Outliers** once live owned-social analytics are connected.
- `window.OUTLIER_APP.refreshUI()` — re-renders all views.
