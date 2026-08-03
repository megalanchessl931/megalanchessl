from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField
from wtforms.validators import DataRequired, Length, Email
from ..extensions import limiter

from ..models import db
from ..models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="")

class LoginForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField("Entrar")

class RegisterForm(FlaskForm):
    username = StringField("Usuário", validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField("E-mail", validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField("Registrar")

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("admin.dashboard"))
        flash("Usuário ou senha inválidos.", "error")
    return render_template("auth/login.html", form=form)

@auth_bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Não foi possível criar o cadastro com esses dados.", "error")
            return render_template("auth/registro.html", form=form), 400
        user = User(username=username, email=email, is_admin=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Cadastro realizado. Faça login.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/registro.html", form=form)
