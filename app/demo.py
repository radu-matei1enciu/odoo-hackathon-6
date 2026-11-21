from flask import Blueprint, redirect, render_template, request, url_for

from .energy import set_energy

bp = Blueprint("demo", __name__, url_prefix="/demo")


@bp.route("/", methods=("GET", "POST"))
def index():
    if request.method == "POST":
        set_energy(
            request.form.get("battery", 100, type=int),
        )
        return redirect(url_for("demo.index"))
    return render_template("demo/index.html")
