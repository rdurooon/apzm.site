from flask import Blueprint, render_template, session, redirect, url_for

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.home"))
