import functools
from flask import Flask, request, session, render_template, redirect, url_for, flash
from sqlalchemy import select, insert, update, delete
import sqlite3
from models import *
import database

app = Flask(__name__)
app.secret_key = "super secret key"

def film_dictionary(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class Connection_db:
    def __init__(self):
        self.conn = sqlite3.connect('database.db')
        self.conn.row_factory = film_dictionary
        self.cur = self.conn.cursor()

    def __enter__(self):
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()

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
    with Connection_db() as cur:
        res = cur.execute(f'SELECT * FROM film ORDER BY id DESC LIMIT 10').fetchall()
    return render_template('main_page.html', films=res)

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
        get_phone_number=select(User).where(User.phone_number == phone_number)
        result_get_phone_number = database.db_session.execute(get_phone_number).scalar()

        get_login=select(User).where(User.login == login)
        result_get_login = database.db_session.execute(get_login).scalar()

        if result_get_phone_number:
            return "Phone number already exists", 409

        elif result_get_login:
            return "Login already registered", 409
        birth_date = request.form['birth_date']
        additional_info = request.form['additional_info']
        new_user = insert(User).values(first_name=first_name, last_name=last_name, login=login, password=password, email=email, phone_number=phone_number, birth_date=birth_date, additional_info=additional_info)

    return render_template('message.html', details="User registration successful", type="success", user={new_user})

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
    return f"Login success as {result_user}!"

@app.route('/logout', methods=['GET'])
def user_logout():
    if session['user_id']:
        session.clear()
        return render_template('message.html', details="Logout successful", type="success")
    return render_template('message.html', details="You haven`t been logged in", type="error")

@app.route('/users', methods=['GET'])
def users():
    with Connection_db() as cur:
        res = cur.execute(f'SELECT * FROM user').fetchall()
    return ""

@app.route('/users/<int:user_id>', methods=['GET'])
@login_check
def user_profile(user_id):
    if request.method == 'POST':
        first_name = request.form['fname']
        last_name = request.form['lname']
        login = request.form['login']
        password = request.form['password']
        email = request.form['email']
        phone = request.form['phone']
        birth_date = request.form['birth_date']
        photo = request.form['photo']
        additional_info = request.form['info']

        action = request.form.get('action')

        with Connection_db() as cur:
            if action == "save":
                cur.execute("UPDATE user SET first_name=?, last_name=?, login=?, password=?, email=?, phone_number=?, birth_date=?, photo=?, additional_info=? WHERE id=?",
                            (first_name, last_name, login, password, email, phone, birth_date, photo, additional_info, user_id))
                return render_template('message.html', details="User updated successfully", type="success")

            else:
                cur.execute("DELETE FROM user WHERE id=?", (user_id,))
                session.clear()
                return render_template('message.html',
                                       details="Account deleted",
                                       type="success")
    else:
        session_user_id = session.get('user_id')
        if session_user_id is None:
            return render_template('message.html', details="You haven`t been logged in", type="error")

        if session_user_id != user_id:
            return render_template('message.html', details="you are not logged in", type="error")

        with Connection_db() as cur:
            user_info = cur.execute(f'SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
        return render_template('user_profile.html', user=user_info, session_user=session_user_id)



@app.route('/users/<int:user_id>', methods=['DELETE'])
@login_check
def user_delete(user_id):
    return f'User {user_id} delete!'

@app.route('/films', methods=['GET'])
def films():
    filter_params = request.args
    query_parts = []
    params = []
    join = ""

    with Connection_db() as cur:
        countries = cur.execute(f'select * from country').fetchall()
        genres = cur.execute(f'select * from genre').fetchall()

    for key, value in filter_params.items():
        if value:
            if key == 'name':
                query_parts.append("name LIKE ?")
                params.append(f"%{value.strip()}%")
            elif key == 'genre':
                query_parts.append("g.genre LIKE ?")
                join = "f inner join genre_film gn on f.id = gn.film_id inner join genre g on gn.genre_id = g.genre"
                params.append(f"%{value.strip()}%")
            elif key == 'first_name':
                query_parts.append("a.first_name LIKE ?")
                join = "f inner join actor_film af on f.id == af.film_id inner join actor a on af.actor_id == a.id"
                params.append(f"%{value.strip()}%")
            elif key == 'last_name':
                query_parts.append("a.last_name LIKE ?")
                join = "f inner join actor_film af on f.id == af.film_id inner join actor a on af.actor_id == a.id"
                params.append(f"%{value.strip()}%")
            else:
                query_parts.append(f"{key} = ?")
                params.append(value.strip())

    base_sql = "select * from film"

    if query_parts:
        full_sql = f"{base_sql} {join} where {' and '.join(query_parts)} order by id desc"
    else:
        full_sql = f"{base_sql} order by id desc"

    with Connection_db() as cur:
        result = cur.execute(full_sql, params).fetchall()

    if not result:
        flash("Film not found", "error")
        return redirect(url_for('films'))

    return render_template('film.html', films=result, countries=countries, genres=genres)



@app.route('/films/<int:film_id>', methods=['PUT', 'GET'])
def film_edit(film_id):
    if film_id is None:
        return f'Film {film_id} does not exist!'
    if request.method == 'GET':
        with Connection_db() as cur:
            res = cur.execute(f'SELECT * FROM film WHERE id = ?', (film_id,)).fetchone()
        return f'Film {film_id} it is {res}!'
    return f'The received method is PUT'

@app.route('/films/<int:film_id>', methods=['POST'])
def film_create(film_id):
    return f'Film {film_id} create!'

@app.route('/films/<int:film_id>', methods=['DELETE'])
def film_delete(film_id):
    return f'Film {film_id} delete!'

@app.route('/films/<int:film_id>/rating', methods=['GET'])
def show_film_ratings(film_id):
    with Connection_db() as cur:
        res = cur.execute(f'SELECT rating FROM film WHERE id = ?', (film_id,)).fetchone()
    return f'Film {film_id} rating is {res}!'

@app.route('/films/<int:film_id>/rating', methods=['POST'])
def create_film_rating(film_id):
    return f'Film {film_id} rating!'

@app.route('/films/<int:film_id>/ratings/<int:feedback_id>', methods=['GET', 'PUT'])
def show_film_rating(film_id, feedback_id):
    if request.method == 'GET':
        if feedback_id is None:
            return f'Feedback {feedback_id} does not exist!'
        with Connection_db() as cur:
            res = cur.execute(f'SELECT * FROM feedback WHERE id = ?', (feedback_id,)).fetchone()
        return f'Feedback {feedback_id} it is {res}!'
    return f'The received method is PUT'

@app.route('/films/<int:film_id>/ratings/<int:feedback_id>', methods=['DELETE'])
def film_ratings_delete(film_id, feedback_id):
    return f'Film {film_id} ratings {feedback_id}!'

@app.route('/users/<int:user_id>/lists', methods=['GET', 'POST'])
@login_check
def user_lists(user_id):
    if request.method == 'GET':
        with Connection_db() as cur:
            res = cur.execute(f'SELECT * FROM list WHERE id = ?', (user_id,)).fetchall()
        return f'List {user_id} are {res}'
    return f'The received method is POST'

@app.route('/users/<int:user_id>/lists/<int:list_id>', methods=['DELETE'])
@login_check
def list_delete(user_id, list_id):
    return f'User {user_id} list {list_id} have been delete!'

@app.route('/users/<int:user_id>/lists/<int:list_id>', methods=['GET'])
@login_check
def list_show(user_id, list_id):
    with Connection_db() as cur:
        res = cur.execute(f'SELECT name, genre FROM film join film_list on film.id = film_list.film_id WHERE film_list.list_id= ?', (list_id,)).fetchall()
    return f'User {user_id} list item {list_id} have such films {",".join(i for i in res)}'

@app.route('/users/<int:user_id>/lists/<int:list_id>', methods=['POST'])
@login_check
def create_list(user_id, list_id):
    return f'User {user_id} list item {list_id}!'


@app.route('/users/<int:user_id>/lists/<int:list_id>/<int:film_id>', methods=['DELETE'])
@login_check
def user_list_item_delete(user_id, list_id, film_id):
    return f'User {user_id} list item {list_id} have been deleted!'


if __name__ == '__main__':
    app.run(port=5000)
