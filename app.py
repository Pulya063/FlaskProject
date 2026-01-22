import functools
from flask import Flask, request, session, render_template, redirect, url_for, flash
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from database.models import *
from database import database
from other.mail_sender import send_registration_email

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
    try:
        database.get_db()
        films_stmt = select(Film).order_by(Film.id.desc()).limit(10)
        result_films = database.db_session.execute(films_stmt).scalars()

        return render_template('main_page.html', films=result_films)
    except Exception as e:
        flash(f'Помилка завантаження сторінки: {str(e)}', 'error')
        return render_template('main_page.html', films=[])


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
        birth_date = request.form['birth_date']
        phone_number = request.form['phone_number']
        additional_info = request.form['additional_info']
        get_phone_number = select(User).where(User.phone_number == phone_number)
        result_get_phone_number = database.db_session.execute(get_phone_number).scalar()

        if result_get_phone_number:
            return render_template('message.html', details="Номер телефону вже зареєстрований", type="error")

        get_login = select(User).where(User.login == login)
        result_get_login = database.db_session.execute(get_login).scalar()

        if result_get_login:
            return render_template('message.html', details="Логін вже зареєстрований", type="error")

        try:
            birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
        except ValueError:
            return render_template('message.html', details="Невірний формат дати народження (очікується YYYY-MM-DD)", type="error")
        try:
            new_user = insert(User).values(first_name=first_name, last_name=last_name, login=login, password=password,
                                            email=email, phone_number=phone_number, birth_date=birth_date_obj,
                                            additional_info=additional_info if additional_info else None)

            database.db_session.execute(new_user)
            database.db_session.commit()

            send_registration_email.delay(email, first_name)

            return render_template('message.html', details="Користувач успішно зареєстрований", type="success")
        except IntegrityError:
            database.db_session.rollback()
            return render_template('message.html', details="Помилка реєстрації. Можливо, логін або телефон вже існує.", type="error")
        except Exception as e:
            database.db_session.rollback()
            return render_template('message.html', details=f"Помилка реєстрації: {str(e)}", type="error")


@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def user_login_post():
    try:
        database.get_db()
        login = request.form.get('login')
        password = request.form.get('password')

        if not login or not password:
            flash('Будь ласка, введіть логін та пароль.', 'error')
            return redirect(url_for('login_page'))

        user = select(User).where(User.login == login)
        result_user = database.db_session.execute(user).scalar()

        if result_user is None or result_user.password != password:
            flash('Невірний логін або пароль. Спробуйте ще раз.', 'error')
            return redirect(url_for('login_page'))

        session['user_id'] = result_user.id
        return redirect(url_for('main_page'))
    except Exception as e:
        flash('Сталася помилка при вході. Спробуйте ще раз.', 'error')
        return redirect(url_for('login_page'))


@app.route('/logout', methods=['GET'])
def user_logout():
    if session.get('user_id'):
        session.clear()
        return render_template('message.html', details="Logout successful", type="success")
    return render_template('message.html', details="You haven`t been logged in", type="error")


@app.route('/users', methods=['GET'])
def users():
    database.get_db()
    users_stmt = select(User)
    result = database.db_session.execute(users_stmt).scalars().all()
    return str([f"{u.first_name} {u.last_name} ({u.login})" for u in result])


@app.route('/users/<int:user_id>', methods=['GET', 'POST'])
@login_check
def user_profile(user_id):
    if session.get('user_id') != user_id:
        return "Access denied", 403

    database.get_db()
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        login = request.form['login']
        password = request.form['password']
        email = request.form['email']
        phone_number = request.form['phone_number']
        birth_date = request.form['birth_date']
        additional_info = request.form['additional_info']

        action = request.form.get('action')
        if action == "save":
            existing_user = database.db_session.execute(select(User).where(User.login == login)).scalar()
            if existing_user and existing_user.id != user_id:
                return render_template('message.html', details="Логін вже використовується іншим користувачем", type="error")

            existing_phone = database.db_session.execute(select(User).where(User.phone_number == phone_number)).scalar()
            if existing_phone and existing_phone.id != user_id:
                return render_template('message.html', details="Номер телефону вже використовується іншим користувачем", type="error")

            try:
                birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
            except ValueError:
                return render_template('message.html', details="Невірний формат дати (очікується YYYY-MM-DD)", type="error")

            update_user = update(User).where(User.id == user_id).values(first_name=first_name, last_name=last_name,
                                                                        login=login, password=password, email=email,
                                                                        phone_number=phone_number, birth_date=birth_date_obj,
                                                                        additional_info=additional_info if additional_info else None)
            database.db_session.execute(update_user)
            database.db_session.commit()
            return render_template('message.html', details="Профіль успішно оновлено", type="success")

        elif action == "delete":
            deleted_user = delete(User).where(User.id == user_id)
            database.db_session.execute(deleted_user)
            database.db_session.commit()
            session.clear()
            return render_template('message.html', details="Акаунт видалено", type="success")
        else:
            user_info_stmt = select(User).where(User.id == user_id)
            res_user_info = database.db_session.execute(user_info_stmt).scalar()
            if not res_user_info:
                return "Користувача не знайдено", 404
            return render_template('user_profile.html', user=res_user_info)


@app.route('/users/<int:user_id>', methods=['DELETE'])
@login_check
def user_delete(user_id):
    if session.get('user_id') != user_id:
        return "Access denied", 403

    try:
        database.get_db()
        user_check = database.db_session.execute(select(User).where(User.id == user_id)).scalar()
        if not user_check:
            return "Користувача не знайдено", 404

        deleted_user = delete(User).where(User.id == user_id)
        database.db_session.execute(deleted_user)
        database.db_session.commit()
        session.clear()
        return f'User {user_id} delete!'
    except Exception as e:
        database.db_session.rollback()
        return f"Помилка видалення: {str(e)}", 500


@app.route('/films', methods=['GET'])
def films():
    try:
        database.get_db()
        filter_params = request.args
        stmt = select(Film).distinct()

        countries = database.db_session.execute(select(Country)).scalars().all()
        genres = database.db_session.execute(select(Genre)).scalars().all()

        name = filter_params.get('name')
        genre_val = filter_params.get('genre')

        if name:
            stmt = stmt.where(Film.name.ilike(f"%{name.strip()}%"))

        if genre_val:
            stmt = stmt.join(Film.genres).where(Genre.genre == genre_val)

        stmt = stmt.order_by(Film.id.desc())
        result = database.db_session.execute(stmt).scalars().all()

        if not result and (name or genre_val):
            flash("Фільм не знайдено", "error")

        return render_template('film.html', films=result, countries=countries, genres=genres)
    except Exception as e:
        flash(f'Помилка завантаження фільмів: {str(e)}', 'error')
        database.get_db()
        countries = database.db_session.execute(select(Country)).scalars().all()
        genres = database.db_session.execute(select(Genre)).scalars().all()
        return render_template('film.html', films=[], countries=countries, genres=genres)


@app.route('/films/<int:film_id>', methods=['PUT', 'GET'])
def film_edit(film_id):
    try:
        database.get_db()
        if request.method == 'GET':
            film = select(Film).where(Film.id == film_id)
            res_film = database.db_session.execute(film).scalar()
            if not res_film:
                return "Фільм не знайдено", 404
            return f'Film {film_id} is {res_film}!'
        else:
            name = request.form['name']
            year = request.form['year']
            poster = request.form['poster']
            actors = request.form['actors']
            description = request.form['description']
            rating = request.form['rating']
            duration = request.form['duration']
            country_name = request.form['country_name']
            genre_names = request.form.getlist('genres')

            film_check = database.db_session.execute(select(Film).where(Film.id == film_id)).scalar()
            if not film_check:
                return "Фільм не знайдено", 404

            country_check = database.db_session.execute(select(Country).where(Country.country_name == country_name)).scalar()
            if not country_check:
                return "Країна не знайдена", 404

            try:
                year_obj = datetime.strptime(str(year), '%Y-%m-%d').date()
                rating_int = int(rating)
                duration_int = int(duration)
            except (ValueError, TypeError) as e:
                return f"Невірний формат даних: {str(e)}", 400

            update_film_values = {
                'name': name,
                'year': year_obj,
                'poster': poster,
                'actors': actors,
                'description': description,
                'rating': rating_int,
                'duration': duration_int,
                'country_name': country_name
            }

            database.db_session.execute(update(Film).where(Film.id == film_id).values(**update_film_values))

            if genre_names:
                film_obj = database.db_session.execute(select(Film).where(Film.id == film_id)).scalar_one()
                film_obj.genres.clear()
                for genre_name in genre_names:
                    genre_obj = database.db_session.execute(select(Genre).where(Genre.genre == genre_name)).scalar()
                    if genre_obj:
                        film_obj.genres.append(genre_obj)
            
            database.db_session.commit()
            return f'Film {film_id} updated!'
    except IntegrityError:
        database.db_session.rollback()
        return "Помилка оновлення фільму", 500
    except Exception as e:
        database.db_session.rollback()
        return f"Помилка: {str(e)}", 500


@app.route('/films/<int:film_id>', methods=['DELETE'])
def film_delete(film_id):
    try:
        database.get_db()
        film_check = database.db_session.execute(select(Film).where(Film.id == film_id)).scalar()
        if not film_check:
            return "Фільм не знайдено", 404

        stmt = delete(Film).where(Film.id == film_id)
        database.db_session.execute(stmt)
        database.db_session.commit()
        return f'Film {film_id} delete!'
    except Exception as e:
        database.db_session.rollback()
        return f"Помилка видалення: {str(e)}", 500


@app.route('/films/<int:film_id>/rating', methods=['POST'])
@login_check
def create_film_rating(film_id):
    try:
        database.get_db()
        user_id = session.get('user_id')
        
        film_check = database.db_session.execute(select(Film).where(Film.id == film_id)).scalar()
        if not film_check:
            return "Фільм не знайдено", 404

        grade = request.form.get('grade')
        description = request.form.get('description')

        if not grade:
            return "Оцінка обов'язкова", 400

        try:
            grade_int = int(grade)
            if grade_int < 1 or grade_int > 10:
                return "Оцінка повинна бути від 1 до 10", 400
        except (ValueError, TypeError):
            return "Невірний формат оцінки", 400

        if not description:
            return "Опис обов'язковий", 400

        new_feedback = insert(Feedback).values(film_id=film_id, user_id=user_id, grade=grade_int, description=description)
        database.db_session.execute(new_feedback)
        database.db_session.commit()
        return f'Film {film_id} rating created!'
    except IntegrityError:
        database.db_session.rollback()
        return "Помилка створення оцінки", 500
    except Exception as e:
        database.db_session.rollback()
        return f"Помилка: {str(e)}", 500


@app.route('/films/<int:film_id>/ratings/<int:feedback_id>', methods=['DELETE'])
def film_ratings_delete(film_id, feedback_id):
    try:
        database.get_db()
        feedback_check = database.db_session.execute(
            select(Feedback).where(Feedback.id == feedback_id, Feedback.film_id == film_id)
        ).scalar()
        if not feedback_check:
            return "Відгук не знайдено", 404

        stmt = delete(Feedback).where(Feedback.id == feedback_id)
        database.db_session.execute(stmt)
        database.db_session.commit()
        return f'Film {film_id} ratings {feedback_id} deleted!'
    except Exception as e:
        database.db_session.rollback()
        return f"Помилка видалення: {str(e)}", 500


@app.route('/users/<int:user_id>/lists/<int:list_id>', methods=['DELETE'])
@login_check
def list_delete(user_id, list_id):
    try:
        database.get_db()
        list_check = database.db_session.execute(
            select(MovieList).where(MovieList.id == list_id, MovieList.user_id == session.get('user_id'))
        ).scalar()
        if not list_check:
            return "Список не знайдено або доступ заборонено", 404

        stmt = delete(MovieList).where(MovieList.id == list_id, MovieList.user_id == session['user_id'])
        database.db_session.execute(stmt)
        database.db_session.commit()
        return f'User {user_id} list {list_id} have been delete!'
    except Exception as e:
        database.db_session.rollback()
        return f"Помилка видалення: {str(e)}", 500


@app.route('/users/<int:user_id>/lists/<int:list_id>/<int:film_id>', methods=['DELETE'])
@login_check
def user_list_item_delete(user_id, list_id, film_id):
    try:
        database.get_db()
        check_list = select(MovieList).where(MovieList.id == list_id, MovieList.user_id == session['user_id'])
        if not database.db_session.execute(check_list).scalar():
            return "Access denied or list not found", 403

        item_check = database.db_session.execute(
            select(FilmList).where(FilmList.list_id == list_id, FilmList.film_id == film_id)
        ).scalar()
        if not item_check:
            return "Елемент не знайдено в списку", 404

        stmt = delete(FilmList).where(FilmList.list_id == list_id, FilmList.film_id == film_id)
        database.db_session.execute(stmt)
        database.db_session.commit()
        return f'User {user_id} list item {list_id} have been deleted!'
    except Exception as e:
        database.db_session.rollback()
        return f"Помилка видалення: {str(e)}", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0' , port=5000)
