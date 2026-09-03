# KyCreekers — Media Kit

Static landing page / media kit for [KyCreekers](https://www.kycreekers.com), an antique bottle and history-hunting brand from West Kentucky.

**Live**: [kycreekers-mediakit.netlify.app](https://kycreekers-mediakit.netlify.app)

---

## What's in here

| File | Purpose |
|---|---|
| `index.html` | The page itself — single-file HTML/CSS/JS |
| `stats.json` | Hero stats + platform follower counts (hand-edited) |
| `products.json` | Featured Products section data (auto-generated, do not hand-edit) |
| `update_products.py` | Fetches kycreekers.com/shop, writes `products.json`. Skips out-of-stock and 404 items. |
| `.github/workflows/refresh.yml` | Nightly GitHub Action that runs the refresh in the cloud |
| `refresh-and-push.ps1` | Legacy local Task Scheduler wrapper (superseded by the Action, kept for reference) |
| `logo.png` | Brand bottle logo |
| `*.webp` | Photo assets (bottle finds, JMS Photography field shots) |
| `og-image.jpg` | Social share card (1200×630) — the file `og:image` actually points at |
| `og-image.svg` | Vector source for the share card |
| `.claude/launch.json` | Local preview server config (Python http.server, port 5500) |

---

## How deploys work

```
GitHub Action (08:00 UTC daily)
  └─ runs update_products.py → rewrites products.json
     └─ commits + pushes if anything changed
        └─ Netlify auto-builds from main → live site
```

Any push to `main` — automated or manual — triggers a Netlify rebuild.

> **This repo is public on purpose.** Netlify's free plan allows only *one* Git
> contributor on private repos, so the `github-actions[bot]` commits from the
> nightly job were silently blocked (every build from 2026-05-25 to 2026-09-02
> failed with "unrecognized Git contributor" while the live site kept serving a
> stale May build). Making the repo public lifts that limit. There are no
> secrets here — every file is already served publicly from the live site.
> If this ever goes private again, the nightly deploys will break the same way.

---

## Update the page

### Stats (followers, top video, episode count)

1. Edit `stats.json`
2. **Also update the matching hardcoded fallbacks in `index.html`** — the
   `data-stat="…"` and `data-platform-followers/extra="…"` elements, plus the
   `description` / `og:description` / `twitter:description` meta tags. JS
   overwrites the elements at runtime, but link-preview scrapers and crawlers
   don't run JS, so stale fallbacks leak into search results and social cards.
3. Commit + push

### Featured products

1. Edit the `FEATURED` list at the top of `update_products.py`
2. Run `python update_products.py`
3. Commit + push

To see every product slug currently in the store: `python update_products.py --list`

Products deleted from Wix return 404 and are skipped automatically, so a stale
`FEATURED` entry silently shrinks the grid — re-check the list when curating.

### Social share image

`og-image.jpg` is generated from `about-hero.webp` + `logo.png` with Pillow.
Regenerate it if the branding or headline stats change; keep it at 1200×630.

---

## Preview locally

```bash
python -m http.server 5500
```

Then open `http://localhost:5500/`.
