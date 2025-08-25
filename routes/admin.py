from flask import Blueprint, render_template, url_for

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin")
def admin():
    return render_template('admin.html')