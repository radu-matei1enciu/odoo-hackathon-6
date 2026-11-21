# IDEAS

Open ideas and decisions for the features, tiers and technical side of the project. Nothing here is agreed yet. "Said by the team" marks what the team has said. "Proposed" marks suggestions that still need a decision.

## 1. What is the website for?

**Said by the team:** a messaging board where everyone can post messages for everyone else to see, plus alerts in case of emergencies. News could be posted here too, like a social media feed.

### Open questions

- Post types: plain message, news item, emergency alert. Do we need all three?
- Who can post? Anyone, or only some people for news and alerts?
- Do posts show a name, or can they be anonymous?
- Alerts: always pinned at the top? Do they show even in the lowest energy tier?
- Social media features (comments, likes, sharing): in or out?
- Images in posts: allowed? How do they show at lower tiers?
- Updates: does the feed refresh automatically, or only when the visitor reloads?
- Where are posts stored on the server?
- For the demo: seeded posts, live posting, or both?

**Proposed:** start with one feed with three post types (message, news, alert), text first. A text feed keeps working in every tier, and only its look changes.

## 2. Signals (what the app reads)

- **Said by the team:** battery level, weather, others.
- **Proposed:** battery, solar input, a 6-hour forecast, and a visitor-load penalty.
- **Decide:**
  - Which signals do we actually use?
  - Is "weather" a real forecast (Open-Meteo) or only a simulated toggle?
  - Does visitor load count at all?
- **Advice:** start with battery and weather only, and add the others if there is time.

## 3. Tiers

- **Said by the team:** there are tiers based on the battery level. What they are is not fully decided.
- **Proposed:** five tiers (Bloom, Day, Dusk, Ember, Rest) with budget ranges from 80–100 down to 0–9.
- **Decide:**
  - How many tiers? Three is much less design work than five.
  - What does each tier change? The things that can be switched are animations, image size and colour, fonts, decorative art, and scripts.
  - Is there a "Rest" tier where the site shows only a short message?
  - Do the tiers use battery thresholds only, or a combined score?
- **Advice:** three tiers (full, reduced, minimal) plus an optional rest page. With five tiers and 3–4 pages you design 15–20 variations.

## 4. How tiers are built

- **Proposed:** one template folder per tier.
- **Alternative:** one set of pages with a tier switch in the code and CSS (for example a `data-tier` attribute), so each component decides what to show. This is far less duplicate work.
- **Decide:** one shared codebase with a switch, or separate templates per tier?

## 5. Demo controls

- **Proposed:** a `/demo` control panel with a battery slider, a weather toggle, a time-of-day scrubber, and a visitor surge button.
- **Decide:** what do we need to control live? Battery and weather are probably enough.

## 6. Extras

Optional ideas. Decide which of these, if any, go in the first version.

### Smaller extras

- A real Open-Meteo forecast instead of a simulated one.
- A sleep mode when idle.
- Automatic image dithering.
- A "notify me when the full version is back" option.

### Measurement

- **Proposed:** a footprint meter showing bytes actually sent per page, plus estimated energy and CO₂.
- **Decide:** bytes only (measurable and honest), or estimates as well?

### Switching behaviour

- **Proposed:** a 5-point buffer before moving up and a 60-second hold (5 seconds in the demo) so the page does not flicker.
- **Decide:** do we need this, or is it fine for the tier to change instantly each time a threshold is crossed?

### Combining signals into one number

- **Proposed:** a weighted score from 0 to 100 (0.55 battery, 0.25 solar, 0.20 forecast, minus a load penalty).
- **Alternative:** battery decides the tier alone, and the other signals only nudge it up or down one step.
- **Decide:** a formula, or simple rules like "battery below 30 % and cloudy means drop a tier"? Rules are easier to explain on stage.

## Where to start

Two decisions unlock the rest: which signals (section 2), and how many tiers and what each changes (sections 3 and 4). Section 1 comes first, because what the website is for shapes both.
