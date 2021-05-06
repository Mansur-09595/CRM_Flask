import os
import secrets
import csv
import sqlite3
from PIL import Image
from flask import render_template, url_for, redirect, flash, request, abort
from flaskuserview import app, bcrypt, db
from flaskuserview.forms import RegistrationForm, LoginForm, AccountUpdateForm
from flaskuserview.models import User
from flask_login import login_user, logout_user, current_user, login_required


@app.route('/')
def home():
    return render_template ('home.html')

FILE = 'tv.csv'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Аккаунт  создан {form.username.data}! Вы можете войти в свой аккаунт!', 'success')
        return redirect(url_for('login'))
    return render_template ('register.html', form=form)

@app.route('/export_db', methods=['GET', 'POST'])
def export_db():
    con = sqlite3.connect('flaskuserview/users.db')
    outfile = open('flaskuserview/users.csv', 'w')
    outcsv = csv.writer(outfile)

    cursor = con.execute('select username, email from users')
    # dump column titles (optional)
    outcsv.writerow(x[0] for x in cursor.description)
    # dump rows
    outcsv.writerows(cursor.fetchall())
    outfile.close()
    flash(f'База данных успешно экспортирована в файл users.csv', 'success')
    return redirect(url_for('home'))
    


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(f'Войти не удалось. Пожалуйста, проверьте почту и пароль', 'danger')
    return render_template ('login.html', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_avatar(avatar):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(avatar.filename)
    avatar_name = random_hex + f_ext
    avatar_path = os.path.join(app.root_path, 'static/profile_images', avatar_name)
    avatar_size = (125, 125)
    i = Image.open(avatar)
    i.thumbnail(avatar_size)
    i.save(avatar_path)
    return avatar_name


@app.route('/account/<username>', methods=['GET', 'POST'])
@login_required
def account(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = AccountUpdateForm()
    if form.validate_on_submit():
        if form.avatar.data:
            avatar_file = save_avatar(form.avatar.data)
            current_user.avatar = avatar_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Данные пользователя были обновлены!', 'success')
        return redirect(url_for('account', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    avatar = url_for('static', filename='profile_images/' + current_user.avatar)
    return render_template('account.html', form=form, avatar=avatar, user=user)


@app.route('/human')
def human():
    users = User.query.all()
    return render_template ('human.html', users=users)

@app.route('/human/new', methods=['GET', 'POST'])
@login_required
def new_human():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Пользователь был создан!', 'success')
        redirect(url_for('home'))
    return render_template('human_create.html', form=form, legend='Создать пользователя')

@app.route('/human/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def human_edit(user_id):
    user = User.query.get_or_404(user_id)
    form = AccountUpdateForm()
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        db.session.commit()
        flash('Данные пользователя были обновлены!', 'success')
        return redirect(url_for('home', user_id=user.id))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
    return render_template('human_edit.html', form=form, legend='Изменить пост')

@app.route('/human/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_human(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Пост был удален!', 'success')
    return redirect(url_for('home'))
    
