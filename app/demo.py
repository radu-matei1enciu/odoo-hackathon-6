from flask import Blueprint, redirect, render_template, request, url_for

from .energy import set_energy

bp = Blueprint("demo", __name__, url_prefix="/demo")

# battery %, sun %, wind m/s; tiers noted for the default constants in energy.py
PRESETS = {
    "sunny day": {"battery": 60, "sun": 90, "wind_speed": 4},     # charging -> full
    "calm night": {"battery": 40, "sun": 0, "wind_speed": 1},     # 4 h runway -> minimal
    "windy night": {"battery": 50, "sun": 0, "wind_speed": 9},    # ~29 h runway -> full
    "storm": {"battery": 6, "sun": 5, "wind_speed": 16},          # charging, but low -> rest
}


@bp.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        preset = PRESETS.get(request.form.get("preset"))
        if preset:
            set_energy(**preset)
        else:
            set_energy(
                request.form.get("battery", 100, type=int),
                request.form.get("sun", 100, type=int),
                request.form.get("wind_speed", 0, type=int),
            )
        return redirect(url_for("demo.index"))
    return render_template("demo/index.html", presets=PRESETS)
