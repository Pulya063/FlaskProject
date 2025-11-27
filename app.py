from flask import Flask, request
import sqlite3
app = Flask(__name__)

def sql():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    return cur
@app.route('/', methods=['GET'])
def main_page():
    cur = sql()
    res = cur.execute(f'SELECT * FROM film ORDER BY id DESC LIMIT 10')
    films = res.fetchall()
    return films

@app.route('/register', methods=['POST'])
def user_register():
    return 'Register!'

@app.route('/login', methods=['POST'])
def user_login():
    return 'Login!'

@app.route('/logout', methods=['GET'])
def user_logout():
    return 'Logout!'

@app.route('/users/<user_id>', methods=['PUT', 'GET'])
def user_profile(user_id):
    if request.method == 'GET':
        conn = sql()
        cur = conn.cursor()
        res = cur.execute(f'SELECT * FROM users WHERE id = {user_id}')
        user = res.fetchone()
        return f'User {user_id} profile is {user}!'
    return f'The received metod is PUT'

@app.route('/users/<user_id>', methods=['DELETE'])
def user_delete(user_id):
    return f'User {user_id} delete!'

@app.route('/films', methods=['GET'])
def films():
    cur = sql()
    res = cur.execute('SELECT * FROM film')
    films = res.fetchall()
    return f"All films: {",".join(i for i in map(str, films))}"

@app.route('/films/<film_id>', methods=['PUT', 'GET'])
def film_edit(film_id):
    cur = sql()
    if film_id is None:
        return f'Film {film_id} does not exist!'
    if request.method == 'GET':
        res = cur.execute(f'SELECT * FROM film WHERE id={film_id}')
        film = res.fetchone()
        return f'Film {film_id} it is {film}!'
    return f'The received metod is PUT'

@app.route('/films/<film_id>', methods=['POST'])
def film_create(film_id):
    return f'Film {film_id} create!'

@app.route('/films/<film_id>', methods=['DELETE'])
def film_delete(film_id):
    return f'Film {film_id} delete!'

@app.route('/films/<film_id>/rating', methods=['GET'])
def show_film_ratings(film_id):
    cur = sql()
    res = cur.execute(f'SELECT rating FROM film WHERE id={film_id}')
    rating = res.fetchone()
    return f'Film {film_id} rating is {rating}!'

@app.route('/films/<film_id>/rating', methods=['POST'])
def create_film_rating(film_id):
    return f'Film {film_id} rating!'

@app.route('/films/<film_id>/ratings/<feedback_id>', methods=['GET', 'PUT'])
def show_film_rating(film_id, feedback_id):
    if request.method == 'GET':
        if feedback_id is None:
            return f'Feedback {feedback_id} does not exist!'
        cur = sql()
        res = cur.execute(f'SELECT * FROM feedback WHERE id={feedback_id}')
        feedback = res.fetchone()
        return f'Feedback {feedback_id} it is {feedback}!'
    return f'The received metod is PUT'

@app.route('/films/<film_id>/ratings/<feedback_id>', methods=['DELETE'])
def film_ratings_delete(film_id, feedback_id):
    return f'Film {film_id} ratings {feedback_id}!'

@app.route('/users/<user_id>/lists', methods=['GET', 'POST'])
def user_lists(user_id):
    if request.method == 'GET':
        cur = sql()
        res = cur.execute(f'SELECT * FROM list WHERE id={user_id}')
        lists = res.fetchall()
        return f'List {user_id} are {lists}'
    return f'The received metod is POST'

@app.route('/users/<user_id>/lists/<list_id>', methods=['DELETE'])
def list_delete(user_id, list_id):
    return f'User {user_id} list {list_id} have been delete!'

@app.route('/users/<user_id>/lists/<list_id>', methods=['GET'])
def list_show(user_id, list_id):
    cur = sql()
    res = cur.execute(f'SELECT name, genre FROM film join film_list on film.id = film_list.film_id WHERE film_list.list_id={list_id}')
    list = res.fetchall()
    return f'User {user_id} list item {list_id} have such films {",".join(i for i in list)}'

@app.route('/users/<user_id>/lists/<list_id>', methods=['POST'])
def create_list(user_id, list_id):
    return f'User {user_id} list item {list_id}!'


@app.route('/users/<user_id>/lists/<list_id>/<film_id>', methods=['DELETE'])
def user_list_item_delete(user_id, list_id, film_id):
    return f'User {user_id} list item {list_id} have been deleted!'


if __name__ == '__main__':
    app.run()
