# Solar board

Hackathon project (6th Odoo Hackathon, 48h, theme "solarpunk"), demoed on a laptop with no hardware. Working title.

## Concept

A web app meant to run on a small solar-powered server in a solarpunk future of local, renewable-powered servers. It reads its power state (battery, weather) and renders its pages accordingly: the less energy, the less it renders. **Functionality never changes, only how things look.** The site is a message board: messages, news, emergency alerts. No company story.

## Stack (decided)

- Python, Flask, Jinja2, server-side rendering
- SQLite via Flask-SQLAlchemy
- venv + requirements.txt. Docker optional later

## Layout

```
app/
  __init__.py   create_app factory, registers blueprints
  db.py         SQLAlchemy instance, Post model, `init-db` CLI command (drops, creates, seeds)
  energy.py     read_energy, set_energy, choose_tier; before_request + context_processor
  board.py      blueprint: feed (/) and post creation (/post)
  demo.py       blueprint: /demo battery + weather controls
  templates/    base.html, board/, demo/
  static/       css/<tier>.css, js/
instance/       SQLite file (gitignored)
```

## How the tier is chosen

1. `energy.init_app` registers `before_request`: reads energy, `choose_tier()` sets `g.tier`.
2. A `context_processor` injects `tier` and `energy` into every template.
3. `base.html` loads `css/<tier>.css` and includes JS only when the tier is `full`.

One set of templates, one CSS file per tier. The CSS file name must equal the tier name. Tiers: `full`, `minimal`. Battery picks the tier, cloudy weather drops it one step (clamped at the lowest). Thresholds are placeholders, to confirm. Change tiers in `TIERS` and `choose_tier` together with the CSS files.

## Product rules

- Post kinds: `message`, `news`, `alert`. Alerts are pinned at the top in every tier.
- Author name is optional. No auth.
- Posting is a plain HTML form (POST, redirect, GET), so it works without JS in every tier.
- Energy signals are simulated from `/demo` (battery slider, weather toggle). Current store is an in-memory dict in `energy.py`, deliberately behind `read_energy`/`set_energy` so it can be swapped for a table.

## Not building unless time remains

Energy-budget formula, hysteresis, footprint/energy label, measurement, sleep mode, image dithering, rest page, real forecast (Open-Meteo), comments/likes.

## Open items

- Lower-tier feed refresh: JS refresh is full-tier only, so minimal needs a manual reload or `<meta http-equiv="refresh">`. Undecided.
- `static/js/refresh.js` is a stub.
- Final tier thresholds.

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
