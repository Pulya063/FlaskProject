from flask import Flask, request
import sqlite3
app = Flask(__name__)

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

@app.route('/', methods=['GET'])
def main_page():
    with Connection_db() as cur:
        res = cur.execute(f'SELECT * FROM film ORDER BY id DESC LIMIT 10').fetchall()
    return res

@app.route('/register', methods=['GET'])
def registration_page():
    return """
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Форма користувача</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f0f2f5;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
    
            .container {
                background: #ffffff;
                padding: 40px 30px;
                border-radius: 12px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.15);
                width: 380px;
            }
    
            .container h2 {
                text-align: center;
                margin-bottom: 30px;
                font-weight: 600;
                color: #333333;
            }
    
            input[type="text"],
            input[type="email"],
            input[type="tel"],
            input[type="date"],
            input[type="file"],
            textarea {
                width: 100%;
                padding: 12px 14px;
                margin: 10px 0;
                border: 1px solid #ccc;
                border-radius: 8px;
                font-size: 14px;
                transition: all 0.3s ease;
                box-sizing: border-box;
            }
    
            input:focus,
            textarea:focus {
                outline: none;
                border-color: #4CAF50;
                box-shadow: 0 0 6px rgba(76, 175, 80, 0.3);
            }
    
            button {
                width: 100%;
                padding: 12px;
                margin-top: 15px;
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                    font-weight: 600;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: background 0.3s ease;
            }
    
            button:hover {
                background-color: #45a049;
            }
    
            textarea {
                resize: vertical;
                min-height: 80px;
            }
    
            input[type="file"] {
                padding: 5px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Додати користувача</h2>
            <form>
                <input type="text" name="id" placeholder="ID" required>
                <input type="text" name="first_name" placeholder="Ім'я" required>
                <input type="text" name="last_name" placeholder="Прізвище" required>
                <input type="text" name="login" placeholder="Логін" required>
                <input type="email" name="email" placeholder="Email" required>
                <input type="tel" name="phone_number" placeholder="Номер телефону">
                <input type="date" name="birth_date" placeholder="Дата народження">
                <input type="file" name="photo">
                <textarea name="additional_info" placeholder="Додаткова інформація"></textarea>
                <button type="submit">Зберегти</button>
            </form>
        </div>
    </body>
    </html>

    """


@app.route('/register', methods=['POST'])
def user_register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        login = request.form['login']
        email = request.form['email']
        phone_number = request.form['phone_number']
        birth_date = request.form['birth_date']
        additional_info = request.form['additional_info']

        with Connection_db() as cur:
            res = cur.execute('INSERT INTO user (first_name, last_name, login, email, phone_number, birth_date, additional_info) VALUES (?, ?, ?, ?, ?, ?, ?)', (first_name, last_name, login, email, phone_number, birth_date, additional_info))
    return f'Register successuly, new user!'

@app.route('/login', methods=['POST'])
def user_login():
    return 'Login!'

@app.route('/logout', methods=['GET'])
def user_logout():
    return 'Logout!'


@app.route('/users', methods=['GET'])
def users():
    with Connection_db() as cur:
        res = cur.execute(f'SELECT * FROM user').fetchall()
    return res

@app.route('/users/<int:user_id>', methods=['PUT', 'GET'])
def user_profile(user_id):
    if request.method == 'GET':
        with Connection_db() as cur:
            res = cur.execute(f'SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
        return f'User {user_id} profile is {res}!'
    return f'The received method is PUT'

@app.route('/users/<int:user_id>', methods=['DELETE'])
def user_delete(user_id):
    return f'User {user_id} delete!'

@app.route('/films', methods=['GET'])
def films():
    with Connection_db() as cur:
        res = cur.execute('SELECT * FROM film').fetchall()
    return f"All films: {",".join(i for i in map(str, res))}"

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
def user_lists(user_id):
    if request.method == 'GET':
        with Connection_db() as cur:
            res = cur.execute(f'SELECT * FROM list WHERE id = ?', (user_id,)).fetchall()
        return f'List {user_id} are {res}'
    return f'The received method is POST'

@app.route('/users/<int:user_id>/lists/<int:list_id>', methods=['DELETE'])
def list_delete(user_id, list_id):
    return f'User {user_id} list {list_id} have been delete!'

@app.route('/users/<int:user_id>/lists/<int:list_id>', methods=['GET'])
def list_show(user_id, list_id):
    with Connection_db() as cur:
        res = cur.execute(f'SELECT name, genre FROM film join film_list on film.id = film_list.film_id WHERE film_list.list_id= ?', (list_id,)).fetchall()
    return f'User {user_id} list item {list_id} have such films {",".join(i for i in res)}'

@app.route('/users/<int:user_id>/lists/<int:list_id>', methods=['POST'])
def create_list(user_id, list_id):
    return f'User {user_id} list item {list_id}!'


@app.route('/users/<int:user_id>/lists/<int:list_id>/<int:film_id>', methods=['DELETE'])
def user_list_item_delete(user_id, list_id, film_id):
    return f'User {user_id} list item {list_id} have been deleted!'


if __name__ == '__main__':
    app.run(debug=True, reload=True)
