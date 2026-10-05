from flask import Blueprint, redirect, render_template

from ..models import EmergencyContact, SupportService


bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    services = SupportService.query.filter_by(is_active=True).limit(3).all()
    return render_template("main/home.html", services=services)


@bp.route("/support")
def support():
    services = SupportService.query.filter_by(is_active=True).order_by(SupportService.category, SupportService.name).all()
    contacts = EmergencyContact.query.filter_by(is_active=True).order_by(EmergencyContact.is_primary.desc()).all()
    return render_template("main/support.html", services=services, contacts=contacts)


@bp.route("/about-safety")
def about_safety():
    return render_template("main/about_safety.html")


@bp.route("/emergency")
def emergency_access():
    return render_template("main/emergency_access.html")


@bp.route("/quick-exit")
def quick_exit():
    return redirect("https://www.google.com", code=302)
