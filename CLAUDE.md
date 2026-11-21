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
  db.py         SQLAlchemy instance, Post model, `init-db` CLI command (drops, creates, seeds)
  energy.py     model constants, read_energy, set_energy, choose_tier; before_request + context_processor
  board.py      blueprint: feed (/) and post creation (/post)
  demo.py       blueprint: /demo battery/sun/wind controls and PRESETS
  templates/    base.html, board/, demo/
  static/       css/<tier>.css, css/demo.css, js/
instance/       SQLite file (gitignored)
```

## How the tier is chosen

1. `energy.init_app` registers `before_request`: reads energy, `choose_tier()` sets `g.tier`. If the tier is `rest`, it returns `REST_MESSAGE` as plain text with a 503, except for `/demo` and static files, so the battery can be raised again.
2. A `context_processor` injects `tier` and `energy` into every template.
3. `base.html` loads `css/<tier>.css` and includes JS only when the tier is `full`.

One set of templates, one CSS file per page-rendering tier. The CSS file name must equal the tier name. Change tiers in `TIERS` and `choose_tier` together with the CSS files.

## Energy model (`energy.py`, constants at the top, all placeholders)

- Stored state (what `/demo` sets, `set_energy(battery, sun, wind_speed)` clamps): `battery` 0-100 %, `sun` 0-100 % of panel rating, `wind_speed` 0-`WIND_MAX` (30) m/s.
- `read_energy()` returns the stored values plus derived readings: `solar_w = PANEL_RATED_W * sun / 100`; `wind_w` is 0 below `WIND_CUT_IN`, cubic up to `WIND_RATED`, `TURBINE_RATED_W` from there up to `WIND_CUT_OUT` (25 m/s), 0 at or above it (turbine shuts down in storms); `power_in = solar_w + wind_w`, `power_out = DRAW_W`, `stored_wh`, `net_w = power_in - power_out`, `runway_h = stored_wh / -net_w` when draining, else `None` (shown as "charging", also when net is exactly 0).
- `choose_tier`: battery < `REST_BELOW` (10%) gives `rest`, even while charging. Otherwise charging or `runway_h >= RUNWAY_FULL_H` (12 h) gives `full`, else `minimal`.

## Product rules

- Post kinds: `message`, `news`, `alert`. Alerts are pinned at the top in every tier.
- Author name is optional. No auth.
- Posting is a plain HTML form (POST, redirect, GET), so it works without JS in every tier.
- JavaScript: allowed in the `full` tier (loaded by `base.html` only when the tier is `full`). `minimal` has none for now; whether it keeps any is undecided. `rest` sends no page. JS may only enhance how things look or update; every feature must still work without it.
- Energy is simulated from `/demo`: battery, sun and wind speed sliders, plus preset buttons (`PRESETS` dict in `demo.py`: sunny day, calm night, windy night, storm, covering every tier) handled by the same POST route. Plain forms, plus an inline `oninput` per slider that updates its displayed value live (`/demo` is outside the tiers, so the JS rule above doesn't apply to it). `/demo` is outside the simulation (it wouldn't exist on the real server): its template is standalone (doesn't extend `base.html`) with a fixed `css/demo.css`, so it looks the same at every battery level. Current store is an in-memory dict in `energy.py`, deliberately behind `read_energy`/`set_energy` so it can be swapped for a table.

## Not building unless time remains

Energy-budget formula, hysteresis, footprint/energy label, measurement, image dithering, real forecast (Open-Meteo), comments/likes.

## Open items

- JS in `minimal`: keep it JS-free or allow some (e.g. feed refresh). Until decided, minimal needs a manual reload or `<meta http-equiv="refresh">` to see new posts.
- `static/js/refresh.js` is a stub.
- Final values for the energy constants and tier thresholds.
- Should `rest` stay a plain battery threshold, or be driven by runway too?

## Conventions

- Idiomatic Flask only, tutorial style: factory, `init_app` per module, blueprints, `g`, `url_for`. No extra layers (no service/repository/hexagonal), no tests folder.
- Show code changes inline with explicit add/remove annotations. No zip files.
- Do not create new markdown files unless asked. Discuss in chat.
- Flag gaps and ambiguities instead of filling them in silently.

## Run

```
source .venv/bin/activate
flask --app app init-db     # once, and after model changes (wipes data)
flask --app app run --debug
```
