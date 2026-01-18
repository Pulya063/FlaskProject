import functools
from flask import Flask, request, session, render_template, redirect, url_for, flash
from sqlalchemy import select, insert, update, delete
import sqlite3
from models import *
import database

app = Flask(__name__)
app.secret_key = "super secret key"


def login_check(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if session.get('user_id'):
            return func(*args, **kwargs)
        else:
            return redirect(url_for('login_page'))

    return wrapper


@app.route('/', methods=['GET'])
@login_check
def main_page():
    database.get_db()
    films = select(Film).order_by(Film.id.desc()).limit(10)
    result_films = database.db_session.execute(films).scalars()

    return render_template('main_page.html', films=result_films)


@app.route('/register', methods=['GET'])
def registration_page():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def user_register():
    database.get_db()
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        login = request.form['login']
        password = request.form['password']
        email = request.form['email']
        phone_number = request.form['phone_number']
        get_phone_number = select(User).where(User.phone_number == phone_number)
        result_get_phone_number = database.db_session.execute(get_phone_number).scalar()

        get_login = select(User).where(User.login == login)
        result_get_login = database.db_session.execute(get_login).scalar()

        if result_get_phone_number:
            return "Phone number already exists", 409

        elif result_get_login:
            return "Login already registered", 409

        birth_date = request.form['birth_date']
        additional_info = request.form['additional_info']
        new_user = insert(User).values(first_name=first_name, last_name=last_name, login=login, password=password,
                                       email=email, phone_number=phone_number, birth_date=birth_date,
                                       additional_info=additional_info)

        database.db_session.execute(new_user)
        database.db_session.commit()

    return render_template('message.html', details="User registration successful", type="success")


@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def user_login_post():
    database.get_db()
    login = request.form['login']
    password = request.form['password']

    user = select(User).where(User.login == login, User.password == password)
    result_user = database.db_session.execute(user).scalar()

    if result_user is None:
        flash('Невірний логін або пароль. Спробуйте ще раз.', 'error')
        return redirect(url_for('login_page'))

    session['user_id'] = result_user.id
    return f"Login success as {result_user.login}!"


@app.route('/logout', methods=['GET'])
def user_logout():
    if session.get('user_id'):
        session.clear()
        return render_template('message.html', details="Logout successful", type="success")
    return render_template('message.html', details="You haven`t been logged in", type="error")


@app.route('/users', methods=['GET'])
def users():
    database.get_db()
    users = select(User)
    result_user = database.db_session.execute(users).scalars()
    return ""


@app.route('/users/<int:user_id>', methods=['GET', 'POST'])
@login_check
def user_profile(user_id):
    database.get_db()
    if request.method == 'POST':
        first_name = request.form['fname']
        last_name = request.form['lname']
        login = request.form['login']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        birth_date = request.form['birth_date']
        additional_info = request.form['info']

        action = request.form.get('action')
        if action == "save":
            update_user = update(User).where(User.id == user_id).values(first_name=first_name, last_name=last_name,
                                                                        login=login, password=password, email=email,
                                                                        phone_number=phone, birth_date=birth_date,
                                                                        additional_info=additional_info)
            database.db_session.execute(update_user)
            database.db_session.commit()
            return render_template('message.html', details="User updated successfully", type="success")

        elif action == "delete":
            return redirect(url_for("/users/<int:user_id>/delete"))
        else:
        user_info_stmt = select(User).where(User.id == user_id)
        res_user_info = database.db_session.execute(user_info_stmt).scalar()
        return render_template('user_profile.html', user=res_user_info)


@app.route('/users/<int:user_id>/delete', methods=['GET'])
@login_check
def user_delete(user_id):
    database.get_db()
    deleted_user = delete(User).where(User.id == user_id)
    database.db_session.execute(deleted_user)
    database.db_session.commit()
    return f'User {user_id} delete!'


@app.route('/films', methods=['GET'])
def films():
    database.get_db()
    filter_params = request.args
    stmt = select(Film).distinct()

    countries = database.db_session.execute(select(Country)).scalars().all()
    genres = database.db_session.execute(select(Genre)).scalars().all()

    name = filter_params.get('name')
    genre_val = filter_params.get('genre')

    if name:
        stmt = stmt.where(Film.name.icontains(name.strip()))

    if genre_val:
        stmt = stmt.join(Film.genres).where(Genre.genre == genre_val)

    stmt = stmt.order_by(Film.id.desc())
    result = database.db_session.execute(stmt).scalars().all()

    if not result:
        flash("Film not found", "error")

    return render_template('film.html', films=result, countries=countries, genres=genres)


@app.route('/films/<int:film_id>', methods=['PUT', 'GET'])
def film_edit(film_id):
    database.get_db()
    if request.method == 'GET':
        film = select(Film).where(Film.id == film_id)
        res_film = database.db_session.execute(film).scalar()
        return f'Film {film_id} is {res_film}!'
    return f'The received method is PUT'


@app.route('/films/<int:film_id>', methods=['DELETE'])
def film_delete(film_id):
    database.get_db()
    stmt = delete(Film).where(Film.id == film_id)
    database.db_session.execute(stmt)
    database.db_session.commit()
    return f'Film {film_id} delete!'


@app.route('/films/<int:film_id>/rating', methods=['POST'])
def create_film_rating(film_id):
    database.get_db()
    # Логіка створення рейтингу
    database.db_session.commit()
    return f'Film {film_id} rating created!'


@app.route('/films/<int:film_id>/ratings/<int:feedback_id>', methods=['DELETE'])
def film_ratings_delete(film_id, feedback_id):
    database.get_db()
    stmt = delete(Feedback).where(Feedback.id == feedback_id)
    database.db_session.execute(stmt)
    database.db_session.commit()
    return f'Film {film_id} ratings {feedback_id} deleted!'


@app.route('/users/<int:user_id>/lists/<int:list_id>', methods=['DELETE'])
@login_check
def list_delete(user_id, list_id):
    database.get_db()
    stmt = delete(MovieList).where(MovieList.id == list_id)
    database.db_session.execute(stmt)
    database.db_session.commit()
    return f'User {user_id} list {list_id} have been delete!'


@app.route('/users/<int:user_id>/lists/<int:list_id>/<int:film_id>', methods=['DELETE'])
@login_check
def user_list_item_delete(user_id, list_id, film_id):
    database.get_db()
    stmt = delete(FilmList).where(FilmList.list_id == list_id, FilmList.film_id == film_id)
    database.db_session.execute(stmt)
    database.db_session.commit()
    return f'User {user_id} list item {list_id} have been deleted!'


if __name__ == '__main__':
    app.run(port=5000)
