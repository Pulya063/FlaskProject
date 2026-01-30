import functools
from flask import Flask, request, session, render_template, redirect, url_for, flash
from sqlalchemy import select, insert, update, delete, extract
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date

from sqlalchemy.orm import selectinload

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
            flash("You haven`t been logged in")
            return redirect(url_for('login_page'))
    return wrapper


@app.route('/', methods=['GET'])
def main_page():
    try:
        database.get_db()

        countries = database.db_session.execute(select(Country).order_by(Country.country_name.desc())).scalars().all()
        genres = database.db_session.execute(select(Genre).order_by(Genre.genre.desc())).scalars().all()

        result_films = database.db_session.execute(select(Film).order_by(Film.id.desc()).limit(10)).scalars().all()

        return render_template('film.html', films=result_films, countries=countries, genres=genres)
    except Exception as e:
        flash(f'Помилка завантаження сторінки: {str(e)}', 'error')
        return render_template('film.html', films=[])


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

        result_get_login = database.db_session.execute(select(User).where(User.login == login)).scalar_one_or_none()

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
            flash('Реєстрація успішна!', 'success')
            return redirect(url_for('login_page'))
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

        result_user = database.db_session.execute(select(User).where(User.login == login)).scalar_one_or_none()

        if result_user is None or result_user.password != password:
            flash('Невірний логін або пароль. Спробуйте ще раз.', 'error')
            return redirect(url_for('login_page'))

        session['user_id'] = result_user.id
        return redirect(url_for('main_page'))
    except Exception:
        flash('Сталася помилка при вході. Спробуйте ще раз.', 'error')
        return redirect(url_for('login_page'))


@app.route('/logout', methods=['GET'])
@login_check
def user_logout():
    session.clear()
    return redirect(url_for('main_page'))


@app.route('/users', methods=['GET'])
def users():
    database.get_db()
    result = database.db_session.execute(select(User)).scalars().all()
    return str([f"{u.first_name} {u.last_name} ({u.login})" for u in result])


@app.route('/users/<int:user_id>', methods=['GET', 'POST'])
@login_check
def user_profile(user_id):
    database.get_db()
    
    # Перевірка прав доступу (користувач може бачити тільки свій профіль)
    if session.get('user_id') != user_id:
        flash("У вас немає прав для перегляду цього профілю", "error")
        return redirect(url_for('main_page'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        login = request.form['login']
        password = request.form['password']
        email = request.form['email']
        phone_number = request.form['phone_number']
        birth_date = request.form['birth_date']
        additional_info = request.form['additional_info']

        existing_user = database.db_session.execute(select(User).where(User.login == login)).scalar()
        if existing_user and existing_user.id != user_id:
            flash("Логін вже використовується іншим користувачем", "error")
            return redirect(url_for('user_profile', user_id=user_id))

        existing_phone = database.db_session.execute(select(User).where(User.phone_number == phone_number)).scalar()
        if existing_phone and existing_phone.id != user_id:
            flash("Номер телефону вже використовується іншим користувачем", "error")
            return redirect(url_for('user_profile', user_id=user_id))

        try:
            birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
        except ValueError:
            flash("Невірний формат дати", "error")
            return redirect(url_for('user_profile', user_id=user_id))

        update_user = update(User).where(User.id == user_id).values(first_name=first_name, last_name=last_name,
                                                                    login=login, password=password, email=email,
                                                                    phone_number=phone_number, birth_date=birth_date_obj,
                                                                    additional_info=additional_info if additional_info else None)
        database.db_session.execute(update_user)
        database.db_session.commit()
        flash("Профіль успішно оновлено", "success")
        return redirect(url_for('user_profile', user_id = user_id))
    else:
        res_user_info = database.db_session.execute(select(User).where(User.id == user_id)).scalar()
        # Завантажуємо списки користувача
        user_lists = database.db_session.execute(select(MovieList).where(MovieList.user_id == user_id)).scalars().all()
        return render_template('user_profile.html', user=res_user_info, user_lists=user_lists)

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_check
def user_delete(user_id):
        database.get_db()
        deleted_user = delete(User).where(User.id == user_id)

        try:
            database.db_session.execute(deleted_user)
            database.db_session.commit()
            session.clear()
            flash('Акаунт успішно видалено', 'success')
            return redirect(url_for('main_page'))
        except Exception as e:
            database.db_session.rollback()
            flash(f'Помилка видалення користувача: {str(e)}', 'error')
            return redirect(url_for('user_profile', user_id=user_id))


@app.route('/films/new', methods=['GET'])
@login_check
def film_create_page():
    database.get_db()
    countries = database.db_session.execute(select(Country).order_by(Country.country_name)).scalars().all()
    genres = database.db_session.execute(select(Genre).order_by(Genre.genre)).scalars().all()
    actors = database.db_session.execute(select(Actor).order_by(Actor.id)).scalars().all()
    return render_template('film_create.html', countries=countries, genres=genres, all_actors=actors)



@app.route('/films', methods=['GET', 'POST'])
def films():
    database.get_db()
    if request.method == "POST":
        try:
            name = request.form.get('name')
            year_str = request.form.get('date')
            poster = request.form.get('poster')
            country_name = request.form.get('country')
            genre_val = request.form.get('genre')
            actors_ids = request.form.getlist('actor[]')
            rating = request.form.get('rating')
            duration = request.form.get('duration')
            description = request.form.get('description')

            if not all([name, year_str, country_name, rating, duration]):
                flash("Заповніть обов'язкові поля", "error")
                return redirect(url_for('film_create_page'))

            try:
                year_obj = datetime.strptime(year_str, '%Y-%m-%d').date()
                rating_int = int(rating)
                duration_int = int(duration)
            except ValueError:
                flash("Невірний формат даних", "error")
                return redirect(url_for('film_create_page'))

            new_film = Film(
                name=name,
                date=year_obj,
                poster=poster,
                country_name=country_name,
                genre=genre_val,
                rating=rating_int,
                duration=duration_int,
                description=description,
                added_at=datetime.now()
            )
            
            database.db_session.add(new_film)
            database.db_session.flush()

            if actors_ids:
                for actor_id in actors_ids:
                    actor_film = ActorFilm(film_id=new_film.id, actor_id=int(actor_id))
                    database.db_session.add(actor_film)

            database.db_session.commit()
            
            flash("Фільм успішно створено!", "success")
            return redirect(url_for('film_info', film_id=new_film.id))

        except Exception as e:
            database.db_session.rollback()
            flash(f"Помилка створення: {str(e)}", "error")
            return redirect(url_for('film_create_page'))

    else:
        filter_params = request.args

        query = select(Film)

        countries = database.db_session.execute(select(Country)).scalars().all()
        genres = database.db_session.execute(select(Genre)).scalars().all()

        for key, value in filter_params.items():
            if value:
                if key == 'name':
                    query = query.filter(Film.name.ilike(f'%{value.strip()}%'))
                elif key == 'genre':
                    query = query.filter(Film.genre == value.strip())
                elif key == 'first_name':
                    query = query.join(ActorFilm).join(Actor).filter(Actor.first_name.ilike(f'%{value.strip()}%'))
                elif key == 'last_name':
                    query = query.join(ActorFilm).join(Actor).filter(Actor.last_name.ilike(f'%{value.strip()}%'))
                elif key == 'country':
                    query = query.join(Country).filter(Country.country_name == value.strip())
                elif key == 'year':
                    query = query.filter(extract('year', Film.date) == value)

        try:
            query = query.order_by(Film.id.desc()) # Нові зверху
            result = database.db_session.execute(query).scalars().all()

            if not result and filter_params:
                flash("Фільм не знайдено", "error")

            return render_template('film.html', films=result, countries=countries, genres=genres)
        except Exception as e:
            flash(f'Помилка завантаження фільмів: {str(e)}', 'error')
        countries = database.db_session.execute(select(Country)).scalars().all()
        genres = database.db_session.execute(select(Genre)).scalars().all()
        database.db_session.close()
        return render_template('film.html', films=[], countries=countries, genres=genres)

@app.route('/films/<int:film_id>', methods=['GET'])
def film_info(film_id):
    database.get_db()
    try:
        res_film = database.db_session.execute(select(Film).where(Film.id == film_id)).scalar()
        if not res_film:
            flash("Не вдалос знайти фільм", "danger")
            return redirect(url_for('films'))

        film_actors = database.db_session.execute(select(Actor).join(ActorFilm).where(ActorFilm.film_id == film_id)).scalars().all()

        feedbacks = database.db_session.execute(select(Feedback).where(Feedback.film_id == film_id).order_by(Feedback.added_at)).scalars().all()

        countries = database.db_session.execute(select(Country)).scalars().all()
        genres = database.db_session.execute(select(Genre)).scalars().all()

        user_lists = database.db_session.execute(select(MovieList).where(MovieList.user_id == session['user_id'])).scalars().all()

        return render_template("film_info.html", film=res_film, film_feedbacks=feedbacks, user_lists=user_lists, film_actors = film_actors, countries=countries, genres=genres)
    except Exception as e:
        flash(f'Помилка завантаження сторінки: {str(e)}', 'error')
        return redirect(url_for('films'))

@app.route('/films/<int:film_id>/edit', methods=['GET', 'POST'])
def film_edit(film_id):
    database.get_db()
    
    if request.method == 'GET':
        res_film = database.db_session.execute(select(Film).where(Film.id == film_id)).scalar()

        countries = database.db_session.execute(select(Country)).scalars().all()
        genres = database.db_session.execute(select(Genre)).scalars().all()
        database.db_session.close()

        if not res_film:
            flash("Фільм не знайдено", "error")
            return redirect(url_for('films'))
        return render_template("film_edit.html", film=res_film, countries=countries, genres=genres)
        
    else:
        try:
            print(f"DEBUG: Form data: {request.form}")

            # Отримуємо дані з форми
            name = request.form.get('name')
            year_str = request.form.get('date')
            poster = request.form.get('poster')
            actors = request.form.get('actors')
            description = request.form.get('description')
            rating = request.form.get('rating')
            duration = request.form.get('duration')
            country_name = request.form.get('country')
            genre_val = request.form.get('genre')

            film_check = database.db_session.execute(select(Film).where(Film.id == film_id)).scalar()
            if not film_check:
                flash("Фільм не знайдено", "error")
                return redirect(url_for('films'))

            # Обробка дати
            year_obj = film_check.date # За замовчуванням залишаємо стару дату
            if year_str:
                try:
                    year_obj = datetime.strptime(year_str, '%Y-%m-%d').date()
                except ValueError:
                    flash("Невірний формат дати. Використано стару дату.", "warning")

            # Обробка числових полів
            try:
                rating_int = int(rating) if rating else film_check.rating
                duration_int = int(duration) if duration else film_check.duration
            except ValueError:
                flash("Рейтинг та тривалість мають бути числами", "error")
                return redirect(url_for('film_edit', film_id=film_id))

            # Оновлення
            update_values = {
                'name': name,
                'date': year_obj,
                'poster': poster,
                'genre': genre_val,
                'actor': actors,
                'description': description,
                'rating': rating_int,
                'duration': duration_int,
                'country_name': country_name
            }

            database.db_session.execute(update(Film).where(Film.id == film_id).values(**update_values))
            database.db_session.commit()
            flash("Фільм успішно оновлено", "success")
            return redirect(url_for('film_info', film_id=film_id))
        except IntegrityError as e:
            database.db_session.rollback()
            print(f"DEBUG: IntegrityError: {e}")
            flash("Помилка оновлення фільму (IntegrityError)", "error")
            return redirect(url_for('film_edit', film_id=film_id))
        except Exception as e:
            database.db_session.rollback()
            print(f"DEBUG: Error in film_edit: {e}")
            flash(f"Помилка при оновленні: {str(e)}", "error")
            return redirect(url_for('film_edit', film_id=film_id))


@app.route('/films/<int:film_id>/delete', methods=['POST'])
def film_delete(film_id):
    try:
        database.get_db()
        film_check = database.db_session.execute(select(Film).where(Film.id == film_id)).scalar()
        if not film_check:
            flash("Фільм не знайдено", "error")
            return redirect(url_for('films'))

        stmt = delete(Film).where(Film.id == film_id)
        database.db_session.execute(stmt)
        database.db_session.commit()
        flash(f'Фільм {film_id} видалено!', 'success')
        return redirect(url_for('films'))
    except Exception as e:
        database.db_session.rollback()
        flash(f"Помилка видалення: {str(e)}", "error")
        return redirect(url_for('film_info', film_id=film_id))

@app.route('/films/<int:film_id>/rating', methods=['POST'])
@login_check
def create_film_rating(film_id):
    database.get_db()
    try:
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

        stmt = insert(Feedback).values(film_id=film_id, user_id=user_id, grade=grade_int, description=description)
        database.db_session.execute(stmt)
        database.db_session.commit()
        
        flash('Відгук успішно додано!', 'success')
        return redirect(url_for('film_info', film_id=film_id))
    except IntegrityError:
        database.db_session.rollback()
        flash("Помилка додавання відгуку", "error")
        return redirect(url_for('film_info', film_id=film_id))
    except Exception as e:
        database.db_session.rollback()
        flash(f"Помилка: {str(e)}", "error")
        return redirect(url_for('film_info', film_id=film_id))

@app.route('/films/<int:film_id>/rating/<int:feedback_id>/update', methods=['POST', 'GET'])
def edit_film_rating(feedback_id, film_id):
    database.get_db()
    film_check = database.db_session.execute(select(Film).where(Film.id == film_id)).scalar()
    if request.method == 'POST':
        if not film_check:
            flash("Фільм не знайдено")
            return redirect(url_for('film_info', film_id=film_id))

        grade = request.form.get('grade')
        description = request.form.get('description')

        if not grade:
            flash("Оцінка обов'язкова")
            return redirect(url_for('film_info', film_id=film_id))

        try:
            grade_int = int(grade)
            if grade_int < 1 or grade_int > 10:
                flash("Оцінка повинна бути від 1 до 10")
                return redirect(url_for('film_info', film_id=film_id))
        except (ValueError, TypeError):
            flash("Невірний формат оцінки")
            return redirect(url_for('film_info', film_id=film_id))


        if not description:
            flash("Опис обов'язковий")
            return redirect(url_for('film_info', film_id=film_id))

        try:
            updated_feedback = database.db_session.execute(update(Feedback).where(Feedback.id == feedback_id).values(grade=grade_int, description=description))
            database.db_session.commit()
            flash("Відгук успішно оновлено!")
            return redirect(url_for('film_info', film_id=film_id))
        except Exception as e:
            database.db_session.rollback()
            flash(f"Помилка оновлення відгуку: {str(e)}")
            return redirect(url_for('film_info', film_id=film_id))

    feedbacks = database.db_session.execute(
        select(Feedback).where(Feedback.film_id == film_id).order_by(Feedback.added_at)).scalars().all()
    return render_template('film_info.html', film=film_check, film_feedbacks=feedbacks, feedback_id=feedback_id)


@app.route('/films/<int:film_id>/ratings/<int:feedback_id>', methods=['POST'])
@login_check
def film_ratings_delete(film_id, feedback_id):
    try:
        database.get_db()
        # Перевірка прав (чи це відгук поточного юзера)
        feedback_check = database.db_session.execute(
            select(Feedback).where(Feedback.id == feedback_id, Feedback.film_id == film_id, Feedback.user_id == session.get('user_id'))
        ).scalar()
        
        if not feedback_check:
            flash("Відгук не знайдено або у вас немає прав на його видалення", "error")
            return redirect(url_for('film_info', film_id=film_id))

        stmt = delete(Feedback).where(Feedback.id == feedback_id)
        database.db_session.execute(stmt)
        database.db_session.commit()
        
        flash('Відгук видалено!', 'success')
        return redirect(url_for('film_info', film_id=film_id))
    except Exception as e:
        database.db_session.rollback()
        flash(f"Помилка видалення: {str(e)}", "error")
        return redirect(url_for('film_info', film_id=film_id))

# --- Роути для списків ---

@app.route('/users/<int:user_id>/lists', methods=['POST'])
@login_check
def create_list(user_id):
    database.get_db()
    if request.method == 'POST':
        list_name = request.form.get('list_name')
        if not list_name:
            flash("Назва списку обов'язкова", "error")
            return redirect(url_for('user_profile', user_id=user_id))

        try:
            new_list = MovieList(name=list_name, user_id=user_id)
            database.db_session.add(new_list)
            database.db_session.commit()

            flash(f"Список '{list_name}' створено!", "success")
            return redirect(url_for('user_profile', user_id=user_id))
        except IntegrityError:
            database.db_session.rollback()
        except Exception as e:
            database.db_session.rollback()
            flash(f"Помилка створення списку: {str(e)}", "error")
            return redirect(url_for('user_profile', user_id=user_id))

@app.route('/films/<int:film_id>/ratings/<int:feedback_id>/edit', methods=['POST'])
@login_check
def film_ratings_edit(film_id, feedback_id):
    try:
        database.get_db()
        # Перевірка прав
        feedback_check = database.db_session.execute(
            select(Feedback).where(Feedback.id == feedback_id, Feedback.film_id == film_id, Feedback.user_id == session.get('user_id'))
        ).scalar()
        
        if not feedback_check:
            flash("Відгук не знайдено або у вас немає прав", "error")
            return redirect(url_for('film_info', film_id=film_id))

        new_description = request.form.get('description')
        new_grade = request.form.get('grade')

        if new_description:
            # Оновлюємо
            stmt = update(Feedback).where(Feedback.id == feedback_id).values(description=new_description, grade=int(new_grade) if new_grade else feedback_check.grade)
            database.db_session.execute(stmt)
            database.db_session.commit()
            flash('Відгук оновлено!', 'success')
        
        return redirect(url_for('film_info', film_id=film_id))
    except Exception as e:
        database.db_session.rollback()
        flash(f"Помилка оновлення: {str(e)}", "error")
        return redirect(url_for('film_info', film_id=film_id))

@app.route('/users/<int:user_id>/lists/<int:list_id>', methods=['GET'])
@login_check
def view_list(user_id, list_id):
    database.get_db()
    try:
        list_check = database.db_session.execute(select(MovieList).where(MovieList.id == list_id, MovieList.user_id == user_id)).scalar()
        if not list_check:
            flash("Список не знайдено або доступ заборонено", "error")
            return redirect(url_for('user_profile', user_id=user_id))

        film_list = database.db_session.execute(select(Film).join(FilmList, FilmList.film_id == Film.id).where(FilmList.list_id == list_id)).scalars().all()

        return render_template('user_list.html', list=list_check, films=film_list)
    except Exception as e:
        flash(f'Помилка завантаження сторінки: {str(e)}', 'error')
        return redirect(url_for('user_profile', user_id=user_id))


@app.route('/users/<int:user_id>/lists/<int:list_id>', methods=['POST'])
@login_check
def list_delete(user_id, list_id):
    try:
        database.get_db()
        if session.get('user_id') != user_id:
            flash("Доступ заборонено", "error")
            return redirect(url_for('main_page'))

        stmt = delete(MovieList).where(MovieList.id == list_id, MovieList.user_id == user_id)
        database.db_session.execute(stmt)
        database.db_session.commit()

        flash('Список видалено!', 'success')
        return redirect(url_for('user_profile', user_id=user_id))
    except Exception as e:
        database.db_session.rollback()
        flash(f"Помилка видалення: {str(e)}", "error")
        return redirect(url_for('user_profile', user_id=user_id))


@app.route('/users/<int:user_id>/lists/<int:list_id>/<int:film_id>/delete', methods=['POST'])
@login_check
def user_list_item_delete(user_id, list_id, film_id):
    try:
        database.get_db()
        if session.get('user_id') != user_id:
            flash("Доступ заборонено", "error")
            return redirect(url_for('main_page'))

        stmt = delete(FilmList).where(FilmList.list_id == list_id, FilmList.film_id == film_id)
        database.db_session.execute(stmt)
        database.db_session.commit()

        flash('Фільм видалено зі списку!', 'success')
        return redirect(url_for('view_list', user_id=user_id, list_id=list_id))
    except Exception as e:
        database.db_session.rollback()
        return f"Помилка видалення: {str(e)}", 500

@app.route('/films/<int:film_id>/add_to_list', methods=['POST'])
@login_check
def add_to_list(film_id):
    database.get_db()
    user_id = session.get('user_id')
    list_id = request.form.get('list_id')

    try:
        if not list_id:
            flash("Оберіть список", "error")
            return redirect(url_for('film_info', film_id=film_id))
            
        # Перевірка, чи належить список користувачу
        list_check = database.db_session.execute(select(MovieList).where(MovieList.id == list_id, MovieList.user_id == user_id)).scalar()
        if not list_check:
            flash("Список не знайдено або доступ заборонено", "error")
            return redirect(url_for('film_info', film_id=film_id))
            
        # Перевірка, чи фільм вже є в списку
        exists = database.db_session.execute(select(FilmList).where(FilmList.list_id == list_id, FilmList.film_id == film_id)).scalar()
        if exists:
            flash("Фільм вже є в цьому списку", "info")
            return redirect(url_for('film_info', film_id=film_id))
            
        # Додавання
        new_item = FilmList(list_id=list_id, film_id=film_id)
        database.db_session.add(new_item)
        database.db_session.commit()
        
        flash("Фільм додано до списку!", "success")
        return redirect(url_for('film_info', film_id=film_id))
        
    except Exception as e:
        database.db_session.rollback()
        flash(f"Помилка додавання: {str(e)}", "error")
        return redirect(url_for('film_info', film_id=film_id))


if __name__ == '__main__':
    app.run(debug=True, port=7000)
