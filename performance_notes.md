# BoosterNotes — Performance Optimization Notes

## Changes Made (views.py)

### 1. ❌ N+1 Query Bug Fixed — `_build_cart_items`
**Before:** For each cart item, it ran a separate DB query (`ELibraryModel.objects.get(...)` inside a loop).
**After:** Batched into 2 queries total — one `filter(id__in=pdf_ids)` and one `filter(id__in=book_ids)`.
**Impact:** Cart with 5 items = was 10+ queries → now 2 queries.

### 2. ❌ Repeated Settings Queries Fixed
**Before:** `NavbarSetting.objects.first()`, `FooterSetting.objects.first()`, `AboutSetting.objects.first()` were called on EVERY page load in multiple views.
**After:** Cached with `cache.set(..., 3600)` — 1-hour TTL. Cache is busted when admin saves settings.
**Impact:** Saves 3-6 DB hits per page request.

### 3. ❌ `home` view query count reduced
**Before:** ~14 DB queries on every homepage load.
**After:** ~7-8 queries (categories cached 10 min, settings cached 1 hr, `.only()` on heavy models).

### 4. ❌ `select_related` / `prefetch_related` Added
- `elibrary_dashboard`: added `select_related('category')`
- `search`: added `.only(...)` + `Prefetch` to limit image queries
- `category_courses_view`: added `.only(...)` to elibrary query
- `elibrary_detail`: PDFs are prefetched once, not re-queried in template
- `hard_book_detail`: single prefetch for images

### 5. ❌ `my_purchases` Fixed
Was returning empty list `[]`. Now queries `Order.objects.filter(user=..., is_paid=True).prefetch_related('items')`.

### 6. ❌ `dashboard` Optimized
Added `.only(...)` to User queryset to avoid loading password hashes + unnecessary fields.

---

## Manual Steps Required

### Add to `settings.py`

```python
# --- Caching (LocMemCache for single-server / Railway) ---
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'boosternotes-cache',
    }
}

# --- WhiteNoise for fast static files ---
# pip install whitenoise
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # <-- add here (2nd position)
    ...rest of your middleware...
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- GZip compression ---
# Add to MIDDLEWARE (can be combined with whitenoise):
# 'django.middleware.gzip.GZipMiddleware',   # add before SecurityMiddleware

# --- Session engine (faster than DB sessions) ---
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
```

### Add to HTML `<img>` tags
Add `loading="lazy"` to all product/thumbnail images:
```html
<img src="{{ course.thumbnail.url }}" loading="lazy" alt="...">
```
This defers off-screen images and speeds up initial page load significantly.

### Database Indexes (add to models.py)
These are already included via Meta ordering but add explicit indexes for heavy filters:
```python
# In ELibraryModel Meta:
indexes = [
    models.Index(fields=['is_active', 'category']),
    models.Index(fields=['is_active', '-created_at']),
]
# In Order Meta:
indexes = [
    models.Index(fields=['user', 'is_paid']),
    models.Index(fields=['status']),
]
```

### Run after deploying
```bash
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
```
