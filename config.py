import database
from models import User, Film
from sqlalchemy import select
from datetime import datetime, timedelta

def get_users_emails():
    try:
        database.db_session()
        users = database.db_session.execute(select(User).filter(User.email.isnot(None))).scalars().all()
        return users
    except Exception as e:
        print(f"Error getting emails: {e}")
        return {}
    finally:
        database.db_session.remove()

print(get_users_emails())

def get_new_films():
    database.db_session()
    time_threshold = datetime.now() - timedelta(hours=24)
    query = select(Film).filter(Film.added_at >= time_threshold, Film.added_at <= datetime.now())

    films = database.db_session.execute(query).scalars().all()
    database.db_session.remove()
    return films

print(get_new_films())