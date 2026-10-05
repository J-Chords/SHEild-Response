from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..forms import LoginForm, ProfileForm, RegistrationForm
from ..models import User


bp = Blueprint("auth", __name__, url_prefix="/auth")


def is_safe_url(target):
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in ("http", "https") and host_url.netloc == redirect_url.netloc


def dashboard_url(user):
    return url_for(f"{user.role.lower()}.dashboard")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(dashboard_url(current_user))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("This account has been deactivated. Contact an administrator for help.", "error")
            else:
                login_user(user, remember=form.remember.data)
                flash("Welcome back. You are signed in securely.", "success")
                next_page = request.args.get("next")
                return redirect(next_page if next_page and is_safe_url(next_page) else dashboard_url(user))
        else:
            flash("The email or password was not recognised.", "error")
    return render_template("auth/login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(dashboard_url(current_user))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.strip().lower(),
            phone=form.phone.data.strip() if form.phone.data else None,
            role="REPORTER",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Your private reporter account is ready.", "success")
        next_page = request.args.get("next")
        return redirect(next_page if next_page and is_safe_url(next_page) else url_for("reporter.dashboard"))
    return render_template("auth/register.html", form=form)


@bp.route("/forgot-password")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(dashboard_url(current_user))
    return render_template("auth/forgot_password.html")


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        db.session.commit()
        flash("Your profile has been updated.", "success")
        return redirect(url_for("auth.profile"))
    return render_template("auth/profile.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.home"))
