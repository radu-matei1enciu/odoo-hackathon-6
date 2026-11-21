from flask import g

TIERS = ("full", "minimal")  # best to worst

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
        index = 0
    elif battery >= 10:
        index = 1
    else:
        index = 2
    return TIERS[min(index, len(TIERS) - 1)]


def init_app(app):
    @app.before_request
    def load_tier():
        g.energy = read_energy()
        g.tier = choose_tier(g.energy)

    @app.context_processor
    def inject_energy():
        return {"tier": g.tier, "energy": g.energy}
