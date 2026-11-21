from flask import g, request

TIERS = ("full", "minimal", "rest")  # best to worst; rest sends REST_MESSAGE only
REST_MESSAGE = (
    "Solar board is down: the battery is low. "
    "It will come back up when the battery is at 10% or more.\n"
)

# Placeholder store for the simulated signals. Open decision: keep in memory
# or persist (e.g. a one-row table). Only read_energy/set_energy touch it.
_state = {"battery": 100}


def read_energy():
    return dict(_state)


def set_energy(battery):
    _state["battery"] = max(0, min(100, battery))


def choose_tier(energy):
    """Battery picks the tier; cloudy weather drops it one step."""
    battery = energy["battery"]
    # placeholder thresholds, to confirm with the team
    if battery >= 50:
        return "full"
    if battery >= 10:
        return "minimal"
    return "rest"


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
