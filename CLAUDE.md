# Solar board

Hackathon project (6th Odoo Hackathon, 48h, theme "solarpunk"), demoed on a laptop with no hardware. Working title.

## Concept

A web app meant to run on a small solar-powered server in a solarpunk future of local, renewable-powered servers. It reads its power state (battery %, solar watts, wind watts) and renders its pages accordingly: the less energy, the less it renders. **Functionality never changes, only how things look**, except below 10% battery, where the site rests and sends only a short plain-text "down" message. The site is a message board: messages, news, emergency alerts. No company story.

## Stack (decided)

- Python, Flask, Jinja2, server-side rendering
- SQLite via Flask-SQLAlchemy
- venv + requirements.txt. Docker optional later

## Layout

```
app/
  __init__.py   create_app factory, registers blueprints
  db.py         SQLAlchemy instance, Post and Attachment models, `init-db` (drops, empties uploads, creates, seeds) and `purge-expired` CLI commands
  energy.py     model constants, read_energy, set_energy, choose_tier; before_request + context_processor
  board.py      blueprint: home page (/), feed (/board), post creation with uploads (/post), media files (/media/<filename>)
  demo.py       blueprint: /demo battery/sun/wind controls and PRESETS
  templates/    base.html, home.html, board/, demo/
  static/       css/<tier>.css, css/demo.css, js/, img/board-background.jpg (board page background, full tier only) and board-background-blur.jpg (its frosted copy for the panes), sky.jpg (energy band background by day), home-option-3.jpg and its blurred copy home-option-3-blur.jpg (home page photo, full tier only; a JPG copy of home-option-3.png, the original; home-option-1/2.jpg are unused alternatives)
instance/       SQLite file and uploads/ (gitignored)
docs/           planning notes: IDEAS.md, MEDIA-UPLOAD.md (planned photo/video uploads)
```

## How the tier is chosen

1. `energy.init_app` registers `before_request`: reads energy, `choose_tier()` sets `g.tier`. If the tier is `rest`, it returns `REST_MESSAGE` as plain text with a 503, except for `/demo` and static files, so the battery can be raised again.
2. A `context_processor` injects `tier` and `energy` into every template.
3. `base.html` loads `css/<tier>.css` and includes JS only when the tier is `full`.
4. In `full`, `base.html` starts with the energy band, a rounded card in the page column on a sunset sky photo (`sky.jpg`; plain dusk blue at night) with the title and the readout line stacked in the middle: a line-art sun that rises with `sun` (hidden at sun 0, which switches the band to night with stars), a wind turbine that spins once per `12 / wind_speed` s and stops when `wind_w` is 0 (below cut-in, or `wind_too_strong` above cut-out); the readout line gives the real watts, draw and battery runway. Pure CSS animation, off under `prefers-reduced-motion`.

The `full` look: green line-art pattern photo (`board-background.jpg`) as the page background, the two board columns as frosted glass panes, glossy cards and buttons (white top edge, sheen gradient, soft shadow); all in the "Glass" section at the end of `full.css`. The frost is `static/img/board-background-blur.jpg` (made with `magick board-background.jpg -morphology Erode Disk:2.5 -blur 0x12 -level 0%,100%,0.8 -quality 82 board-background-blur.jpg`: lines thickened then blurred, so the icons stay visible as soft shapes, redo it if the photo changes), fixed to the window like the body background so it lines up behind each pane; not `backdrop-filter`, which some Linux Firefox setups don't render.

One set of templates, one CSS file per page-rendering tier. The CSS file name must equal the tier name. Change tiers in `TIERS` and `choose_tier` together with the CSS files.

## Energy model (`energy.py`, constants at the top, all placeholders)

- Stored state (what `/demo` sets, `set_energy(battery, sun, wind_speed)` clamps): `battery` 0-100 %, `sun` 0-100 % of panel rating, `wind_speed` 0-`WIND_MAX` (30) m/s.
- `read_energy()` returns the stored values plus derived readings: `solar_w = PANEL_RATED_W * sun / 100`; `wind_w` is 0 below `WIND_CUT_IN`, cubic up to `WIND_RATED`, `TURBINE_RATED_W` from there up to `WIND_CUT_OUT` (25 m/s), 0 at or above it (turbine shuts down in storms); `power_in = solar_w + wind_w`, `power_out = DRAW_W`, `stored_wh`, `net_w = power_in - power_out`, `runway_h = stored_wh / -net_w` when draining, else `None` (shown as "charging", also when net is exactly 0).
- `choose_tier`: battery < `REST_BELOW` (10%) gives `rest`, even while charging. Otherwise charging or `runway_h >= RUNWAY_FULL_H` (12 h) gives `full`, else `minimal`.

## Product rules

- Home page `/` (`board.home`, `home.html`): full-screen photo (`home-option-3.jpg`) with a short intro and a "Go to the board" button (styled like the board's Post button) top left in a bright glass card with dark text (same technique as the board panes: `home-option-3-blur.jpg`, made with `magick home-option-3.png -resize 1200x -blur 0x14 -quality 80 home-option-3-blur.jpg`, fixed behind the card). It overrides `base.html`'s `band` block, so no energy band there; the photo is a CSS background in `full.css`, so lower tiers get plain text and the link. The board itself is `/board` (endpoint still `board.index`, so every `url_for` and redirect follows).
- Post kinds: `message`, `news`, `alert`. Alerts are pinned at the top in every tier.
- Author name is optional. No auth.
- Posting is a plain HTML form (POST, redirect, GET), so it works without JS in every tier.
- Every post has a lifetime chosen by the poster: required `days` field, 1 to `MAX_DAYS` (30, in `board.py`), today counts as day 1. Stored as `Post.expires_on` (last day shown, local date). `flask --app app purge-expired`, run by cron at 00:00, deletes every expired post of every kind plus its upload files. The feed also filters out expired posts, so nothing stale shows if cron didn't run. Seeds: the alert lasts 1 day, the rest 7.
- Reactions: one green heart counter per post (inline line-art SVG, no emoji) (`Post.hearts`), every kind, every tier. Plain form POST to `/post/<id>/heart`, incremented in SQL, redirects back to `#post-<id>`. No auth, so no per-person limit: one person can click many times. Expired or unknown posts give 404.
- Photos and videos: up to `MAX_FILES` (4) per post via one `<input type=file multiple>`, request capped by `MAX_CONTENT_LENGTH` (50 MB, 413 flashes a message). Allowed types in `MEDIA_TYPES` in `board.py` (jpg/jpeg/png/webp/gif, mp4/webm; no SVG); extension and browser mimetype must agree. Text is still required. Files are saved as `uuid4().hex` + extension in `instance/uploads/`, served by `/media/<filename>` (so `rest` blocks them too). `full` shows them inline (`<img loading=lazy>`, `<video preload=none>`); lower tiers show text links with file sizes. See `docs/MEDIA-UPLOAD.md`.
- JavaScript: allowed in the `full` tier (loaded by `base.html` only when the tier is `full`). `minimal` has none for now; whether it keeps any is undecided. `rest` sends no page. JS may only enhance how things look or update; every feature must still work without it.
- Energy is simulated from `/demo` (no link to it from the board, there is no top nav in any tier; open `/demo/` by URL): battery, sun and wind speed sliders, plus preset buttons (`PRESETS` dict in `demo.py`: sunny day, calm night, windy night, storm, covering every tier) handled by the same POST route. Plain forms, plus an inline `oninput` per slider that updates its displayed value live (`/demo` is outside the tiers, so the JS rule above doesn't apply to it). `/demo` is outside the simulation (it wouldn't exist on the real server): its template is standalone (doesn't extend `base.html`) with a fixed `css/demo.css`, so it looks the same at every battery level. Current store is an in-memory dict in `energy.py`, deliberately behind `read_energy`/`set_energy` so it can be swapped for a table.

## Not building unless time remains

Energy-budget formula, hysteresis, footprint/energy label, measurement, image dithering, real forecast (Open-Meteo), comments, other reaction emojis.

## Open items

- JS in `minimal`: keep it JS-free or allow some (e.g. feed refresh). Until decided, minimal needs a manual reload or `<meta http-equiv="refresh">` to see new posts.
- `static/js/refresh.js` is a stub.
- Uploads: EXIF (GPS) is not stripped and there are no thumbnails, both need Pillow. Seed posts have no media.
- Final values for the energy constants and tier thresholds.
- Should `rest` stay a plain battery threshold, or be driven by runway too?

## Conventions

- Idiomatic Flask only, tutorial style: factory, `init_app` per module, blueprints, `g`, `url_for`. No extra layers (no service/repository/hexagonal), no tests folder.
- Show code changes inline with explicit add/remove annotations. No zip files.
- Do not create new markdown files unless asked. Discuss in chat. Markdown other than README.md and CLAUDE.md lives in `docs/`.
- Flag gaps and ambiguities instead of filling them in silently.

## Run

```
source .venv/bin/activate
flask --app app init-db     # once, and after model changes (wipes data)
flask --app app run --debug
```

Nightly expiry (crontab -e), deletes posts whose last day is over:

```
0 0 * * * cd /path/to/odoo-hackathon-6 && .venv/bin/flask --app app purge-expired
```
