# Performance & Security Fixes — June 2026

## What Was Fixed

### 🔴 context_processors.py — 3 Uncached DB Queries on Every Request
**Before:** `NavbarSetting.objects.first()`, `FooterSetting.objects.first()`, `StatsSetting.objects.filter(...)` ran on **every single page request** with no caching.

**After:** All 3 are cached with `django.core.cache` for 1 hour. DB hit only once per hour.

**Impact:** Removes 3 DB queries from every page across the entire site.

---

### 🔴 home() view — Banner Double-Query Bug
**Before:** If no banners existed, the view queried `BannerSetting` twice (check → create → re-fetch). Also `StatsSetting` was queried separately even though context_processor already loaded it.

**After:** Banners cached for 10 minutes. Stats uses the shared cache key.

---

### 🔴 settings.py — Secrets Exposed in Repo
**Before:** `SECRET_KEY`, `RAZORPAY_KEY_SECRET`, `DROPBOX_REFRESH_TOKEN` were hardcoded in settings.py and committed to GitHub.

**After:** All secrets read from environment variables via `os.environ.get()`.

**Action required:** Add these to Railway environment variables:
```
SECRET_KEY=<your-secret-key>
DEBUG=False
RAZORPAY_KEY_ID=rzp_test_RaygzMDa8nwFFP
RAZORPAY_KEY_SECRET=<your-secret>
DROPBOX_APP_KEY=wgg2fsw5pf16x8q
DROPBOX_APP_SECRET=<your-secret>
DROPBOX_REFRESH_TOKEN=<your-token>
```

> ⚠️ **Rotate your Razorpay and Dropbox credentials** — they were exposed in the public repo.

---

### 🟡 index.html — Poppins Font Weights Reduced
**Before:** 6 weights loaded: 300, 400, 500, 600, 700, 800 (~200KB)

**After:** 3 weights: 400, 600, 700 (~100KB saved)

---

### 🟡 .gitignore — Improved
Added: `.env`, `media/`, `staticfiles/`, `venv/`, IDE folders.

> Run `git rm --cached db.sqlite3` locally to stop tracking the database file.

---

## Remaining Recommendations (Manual Steps)

1. **Move media/images to a CDN** (Cloudinary free tier) — banner and product images currently served via Django/disk on Railway which is slow.
2. **Remove db.sqlite3 from git history:** `git filter-branch` or `git-filter-repo --invert-paths --path db.sqlite3`
3. **Move 14KB of inline CSS in index.html** to `style.css` for browser caching.
