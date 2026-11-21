from flask import g, request

# Placeholder constants, easy to tweak
CAPACITY_WH = 100       # battery capacity
DRAW_W = 10             # constant server draw
PANEL_RATED_W = 40      # solar panel output at 100% sun
TURBINE_RATED_W = 20    # wind turbine output from WIND_RATED up to WIND_CUT_OUT
WIND_CUT_IN = 3         # m/s, turbine produces nothing below this
WIND_RATED = 12         # m/s, turbine reaches rated output here
WIND_CUT_OUT = 25       # m/s, turbine shuts down (0 W) at or above this
WIND_MAX = 30           # m/s, top of the demo input range
RUNWAY_FULL_H = 12      # runway at or above this (or charging) means "full"
REST_BELOW = 10         # battery % below which the site rests

TIERS = ("full", "minimal", "rest")  # best to worst; rest sends REST_MESSAGE only
REST_MESSAGE = (
    "Solar board is down: the battery is low. "
    f"It will come back up when the battery is at {REST_BELOW}% or more.\n"
)

# Placeholder store for the simulated causes. Open decision: keep in memory
# or persist (e.g. a one-row table). Only read_energy/set_energy touch it.
_state = {"battery": 100, "sun": 100, "wind_speed": 0}


def _wind_w(v):
    if v < WIND_CUT_IN or v >= WIND_CUT_OUT:
        return 0.0
    if v >= WIND_RATED:
        return float(TURBINE_RATED_W)
    return TURBINE_RATED_W * (v**3 - WIND_CUT_IN**3) / (WIND_RATED**3 - WIND_CUT_IN**3)


def read_energy():
    """Stored causes plus the readings and balance derived from them."""
    energy = dict(_state)
    energy["solar_w"] = PANEL_RATED_W * energy["sun"] / 100
    energy["wind_w"] = _wind_w(energy["wind_speed"])
    energy["power_in"] = energy["solar_w"] + energy["wind_w"]
    energy["power_out"] = DRAW_W
    energy["stored_wh"] = CAPACITY_WH * energy["battery"] / 100
    energy["net_w"] = energy["power_in"] - energy["power_out"]
    # hours until empty at the current net power; None while not draining
    energy["runway_h"] = (
        energy["stored_wh"] / -energy["net_w"] if energy["net_w"] < 0 else None
    )
    return energy


def set_energy(battery, sun, wind_speed):
    _state["battery"] = max(0, min(100, battery))
    _state["sun"] = max(0, min(100, sun))
    _state["wind_speed"] = max(0, min(WIND_MAX, wind_speed))


def choose_tier(energy):
    """Low battery rests; otherwise runway picks full or minimal."""
    if energy["battery"] < REST_BELOW:
        return "rest"
    runway = energy["runway_h"]
    if runway is None or runway >= RUNWAY_FULL_H:
        return "full"
    return "minimal"


def init_app(app):
    @app.before_request
    def load_tier():
        g.energy = read_energy()
        g.tier = choose_tier(g.energy)
        # /demo is outside the simulation (its own fixed style), so it and the
        # static files it needs stay up, otherwise the battery can't be raised again
        if g.tier == "rest" and request.blueprint != "demo" \
                and request.endpoint != "static":
            return REST_MESSAGE, 503, {"Content-Type": "text/plain; charset=utf-8"}

    @app.context_processor
    def inject_energy():
        return {"tier": g.tier, "energy": g.energy}
