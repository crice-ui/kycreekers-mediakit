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
| `logo.png` | Brand bottle logo |
| `*.webp` | Photo assets (bottle finds, JMS Photography field shots) |
| `og-image.svg` | Social share preview card |
| `.claude/launch.json` | Local preview server config (Python http.server, port 5500) |

---

## Update the page

### Stats (followers, top video, episode count)

Edit `stats.json` directly. Page updates on next load. Refresh the deployment when ready.

### Featured products

1. Edit the `FEATURED` list at the top of `update_products.py` to swap which products appear
2. Run: `python update_products.py`
3. Refresh the deployment

To see every product slug currently in the store: `python update_products.py --list`

---

## Auto-refresh

A Windows Task Scheduler entry (`KyCreekers-Products-Daily`) runs `update_products.py` every night at 3 AM. It refreshes `products.json` from the live Wix store.

To get nightly updates onto the deployed site, the project is connected to Netlify via this repo — any commit triggers a redeploy.

---

## Preview locally

```bash
python -m http.server 5500
```

Then open `http://localhost:5500/`.
