from datetime import date

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField, DateField, PasswordField, SelectField, StringField,
    SubmitField, TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

from .models import (
    CASE_STATUSES, INCIDENT_CATEGORIES, RESPONSE_ACTION_LABELS, RESPONSE_ACTION_TYPES,
    RISK_LEVELS, User,
)


class LoginForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Length(max=180)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Keep me signed in on this device")
    submit = SubmitField("Sign in securely")


class RegistrationForm(FlaskForm):
    full_name = StringField("Full name or preferred name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email address", validators=[DataRequired(), Email(), Length(max=180)])
    phone = StringField("Safe phone number (optional)", validators=[Optional(), Length(max=30)])
    password = PasswordField("Create password", validators=[DataRequired(), Length(min=10, max=128)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create secure account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("An account already uses this email address.")


class ProfileForm(FlaskForm):
    full_name = StringField("Name", validators=[DataRequired(), Length(min=2, max=120)])
    phone = StringField("Safe phone number", validators=[Optional(), Length(max=30)])
    submit = SubmitField("Save changes")


class ResponderCreateForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Work email", validators=[DataRequired(), Email(), Length(max=180)])
    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=30)])
    password = PasswordField("Temporary password", validators=[DataRequired(), Length(min=10, max=128)])
    submit = SubmitField("Create responder")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("An account already uses this email address.")


class IncidentForm(FlaskForm):
    category = SelectField("Type of incident", choices=[(v, v) for v in INCIDENT_CATEGORIES], validators=[DataRequired()])
    incident_date = DateField("When did this happen?", default=date.today, validators=[DataRequired()])
    location = StringField("Area or location", validators=[DataRequired(), Length(min=2, max=180)])
    description = TextAreaField("What happened?", validators=[DataRequired(), Length(min=20, max=4000)])
    preferred_contact_method = SelectField(
        "Preferred contact method",
        choices=[
            ("IN_APP", "Secure in-app updates only"),
            ("EMAIL", "Email"),
            ("PHONE", "Phone call"),
            ("TEXT", "Text message"),
            ("OTHER", "Another safe arrangement"),
        ],
        validators=[DataRequired()],
    )
    safe_contact = StringField("Safe contact instructions (optional)", validators=[Optional(), Length(max=120)])
    immediate_danger = BooleanField("I may be in immediate danger")
    threat_to_life = BooleanField("Threats to life were made")
    weapon_involved = BooleanField("A weapon was involved or mentioned")
    medical_attention = BooleanField("Medical attention may be required")
    dependants_at_risk = BooleanField("Children or dependants may be at immediate risk")
    is_anonymous = BooleanField("Hide my identity from responder-facing case views")
    consent = BooleanField("I understand this is an academic prototype and does not dispatch emergency services", validators=[DataRequired()])
    submit = SubmitField("Submit report securely")

    def validate_incident_date(self, field):
        if field.data and field.data > date.today():
            raise ValidationError("The incident date cannot be in the future.")


class EmergencyAlertForm(FlaskForm):
    category = SelectField("Type of emergency", choices=[(v, v) for v in INCIDENT_CATEGORIES], validators=[DataRequired()])
    description = TextAreaField("Briefly, what is happening right now?", validators=[DataRequired(), Length(min=10, max=600)])
    location = StringField("General area or location", validators=[DataRequired(), Length(min=2, max=180)])
    immediate_danger = BooleanField("I am in immediate danger right now")
    is_anonymous = BooleanField("Hide my identity from responder-facing views")
    consent = BooleanField(
        "I understand this academic prototype records the request in SHEild Response and does not contact real emergency services",
        validators=[DataRequired()],
    )
    submit = SubmitField("Send Emergency Request")


class CaseActionForm(FlaskForm):
    status = SelectField("Case status", choices=[(v, v.replace("_", " ").title()) for v in CASE_STATUSES], validators=[DataRequired()])
    risk_level = SelectField("Risk level", choices=[(v, v.title()) for v in RISK_LEVELS], validators=[DataRequired()])
    note = TextAreaField("Response note", validators=[DataRequired(), Length(min=5, max=2000)])
    visible_to_reporter = BooleanField("Share this update with the reporter", default=True)
    submit = SubmitField("Record update")


class InternalNoteForm(FlaskForm):
    note = TextAreaField("Internal note", validators=[DataRequired(), Length(min=3, max=2000)])
    submit = SubmitField("Add internal note")


class ReporterUpdateForm(FlaskForm):
    note = TextAreaField("Update for the reporter", validators=[DataRequired(), Length(min=3, max=2000)])
    submit = SubmitField("Add update for reporter")


class ResponseActionForm(FlaskForm):
    action_type = SelectField(
        "Action type",
        choices=[(v, RESPONSE_ACTION_LABELS[v]) for v in RESPONSE_ACTION_TYPES],
        validators=[DataRequired()],
    )
    note = TextAreaField("Optional note", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Record response action")


class ReferralForm(FlaskForm):
    support_service_id = SelectField("Support service", coerce=int, validators=[DataRequired()])
    note = TextAreaField("Optional note", validators=[Optional(), Length(max=2000)])
    mark_referred = BooleanField("Move case status to Referred", default=True)
    submit = SubmitField("Record referral")


class AssignmentForm(FlaskForm):
    responder_id = SelectField("Assigned responder", coerce=int, validators=[Optional()])
    status = SelectField("Case status", choices=[(v, v.replace("_", " ").title()) for v in CASE_STATUSES], validators=[DataRequired()])
    risk_level = SelectField("Risk level", choices=[(v, v.title()) for v in RISK_LEVELS], validators=[DataRequired()])
    note = TextAreaField("Administrative update", validators=[DataRequired(), Length(min=5, max=2000)])
    submit = SubmitField("Save assignment")


class SupportServiceForm(FlaskForm):
    name = StringField("Service name", validators=[DataRequired(), Length(max=120)])
    category = StringField("Category", validators=[DataRequired(), Length(max=80)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=1000)])
    phone = StringField("Phone", validators=[Optional(), Length(max=40)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=180)])
    website = StringField("Website", validators=[Optional(), Length(max=255)])
    hours = StringField("Hours", validators=[Optional(), Length(max=120)])
    is_active = BooleanField("Visible to reporters", default=True)
    submit = SubmitField("Save service")


class ContactForm(FlaskForm):
    name = StringField("Contact name", validators=[DataRequired(), Length(max=120)])
    phone = StringField("Phone", validators=[DataRequired(), Length(max=40)])
    description = StringField("Description", validators=[Optional(), Length(max=255)])
    is_primary = BooleanField("Show as primary emergency contact")
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save contact")
