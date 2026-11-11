# Autopilot — Moinho Digital (Instagram + Facebook)

## Status (11 Nov 2026)
- ✅ `client.yaml`: brand colours, Instagram handle `moinhodigital`
- ✅ Content loaded: **8 posts**, 11–27 Nov (6 Reels + 2 carousels) in `content/calendar.csv`, media in `content/media/posts/`
- ✅ Reels have their own cover image (new optional `cover` column; the publisher sends it as `cover_url`)
- ✅ Music credits: `content/credits/musica_pixabay.txt`
- ⬜ `client.yaml`: replace `REPLACE_GITHUB_USER` with your GitHub username
- ⬜ Steps A, B, C and E below (Meta token, repo, secrets, test)

| Date | Time | Post |
|---|---|---|
| Wed 11 Nov | 21:00 | Reel: O seu sobrinho faz-lhe o site? |
| Fri 13 Nov | 19:30 | Reel: Carga Certa antes/depois |
| Sun 15 Nov | 10:00 | Carousel: 5 sinais de que o seu site está a perder clientes |
| Tue 17 Nov | 19:30 | Reel: tutorial WhatsApp na bio |
| Thu 19 Nov | 19:30 | Reel: menu em PDF (restaurant demo) |
| Sun 22 Nov | 10:00 | Carousel: 4 coisas para o perfil Google |
| Tue 24 Nov | 19:30 | Reel: Bubble Up antes/depois |
| Fri 27 Nov | 19:30 | Reel: Black Friday (shop demo) |

A post that is due while the setup isn't finished goes out at the first run after it (up to 2 days late); older than that it is skipped.

Copy of the `social-autopilot` template. Only `publish_meta` is switched on.

## Checklist

### A. Accounts (Meta) — ~20 min
- [ ] Facebook Page "Moinho Digital" exists
- [ ] Instagram account is **Professional (Business)**: Instagram → Settings → Account type
- [ ] Instagram is **linked to the Facebook Page** (Meta Business Suite → Settings → Linked accounts)
- [ ] Page + Instagram are in your **Meta Business portfolio** (business.facebook.com → Settings → Accounts)

### B. Token (never expires) — ~15 min
1. developers.facebook.com → use your **existing app** (same as other clients) or create one (type Business)
2. Business Settings → Users → **System users** → your system user (or Add → Admin)
3. **Assign assets**: the Moinho Page (full control) + the Moinho Instagram account
4. **Generate token** → app = your app, expiry = **Never**, permissions:
   `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
   `instagram_basic`, `instagram_content_publish`, `business_management`
5. `python get_meta_ids.py <token>` → prints the 4 secrets

### C. GitHub — ~10 min
- [ ] New repo `autopilot-moinho`, **public** (Instagram must be able to download the media)
- [ ] Upload all files of this folder (incl. hidden `.github/`)
- [ ] `client.yaml`: replace `REPLACE_GITHUB_USER` (handle is already set)
- [ ] Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|---|---|
| `IG_USER_ID` | from get_meta_ids.py |
| `IG_ACCESS_TOKEN` | the system user token |
| `FB_PAGE_ID` | from get_meta_ids.py |
| `FB_PAGE_TOKEN` | from get_meta_ids.py |

### D. Content — your existing material
- Media → `content/media/posts/` (e.g. `01.jpg`, `02.mp4`, `03a.jpg`)
- One row per post in `content/calendar.csv` (times = Lisbon time):

```
date,time,type,caption,media,platforms,cover
2026-11-17,19:00,image,"Texto do post…",posts/01.jpg,ig+fb
2026-11-19,19:00,reel,"Texto do reel…",posts/02.mp4,ig+fb
2026-11-21,12:30,carousel,"Texto…",posts/03a.jpg|posts/03b.jpg|posts/03c.jpg,ig+fb
```

- Captions with commas or line breaks: keep them inside "double quotes"
- `platforms`: `ig+fb`, `ig` or `fb`
- Facebook gets the first image of a carousel

**Media rules**
| Type | Format | Size |
|---|---|---|
| image | JPG | 1080×1350 (4:5) or 1080×1080 |
| carousel | 2–10 JPGs, same ratio | as image |
| reel | MP4 (H.264), 9:16, 3–90 s | 1080×1920, < 100 MB (GitHub limit) |

### E. Test — 5 min
- [ ] Add one row with a time 5 minutes from now → Actions → **Social Autopilot** → **Run workflow** → `daily`
- [ ] Check the post on Instagram + Facebook; green ✓ in Actions
- [ ] Done. It checks every 30 min (07:00–22:30) and posts what is due. A post can go out up to ~30 min after its time.

## Later (switch on in client.yaml, no new code)
`monthly_report`, `google_posts`, `review_replies`, `review_to_post`, `holiday_hours`, `link_page`.
