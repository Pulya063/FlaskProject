import pytest
from app import app as flask_app
from database.database import db_session, init_db, engine
from database.models import User, Film, Genre, Country, Actor
from datetime import date, datetime

@pytest.fixture(scope="session")
def app():
    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret_key",
    })

    with flask_app.app_context():
        init_db()

    yield flask_app

@pytest.fixture(scope="function")
def db(app):
    """
    Yields a database session with a transaction that is rolled back after
    each test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    db_session.configure(bind=connection)

    yield db_session

    db_session.remove()
    transaction.rollback()
    connection.close()

@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture()
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture(scope="function")
def user(db):
    """Creates a new user for each test."""
    new_user = User(
        first_name="Test",
        last_name="User",
        login="testuser",
        password="testpassword",
        email="test@example.com",
        phone_number="1234567890",
        birth_date=date(2000, 1, 1),
        additional_info="Test info"
    )
    db.add(new_user)
    db.commit()
    return new_user

@pytest.fixture(scope="function")
def film(db, country):
    """Creates a new film for each test."""
    new_film = Film(
        name="Test Film",
        date=date(2022, 1, 1),
        poster="test.jpg",
        description="A test film.",
        rating=8,
        duration=120,
        country_name=country.country_name,
        added_at=datetime.now()
    )
    db.add(new_film)
    db.commit()
    return new_film

@pytest.fixture(scope="function")
def genre(db):
    """Creates a new genre for each test."""
    new_genre = Genre(genre="Test Genre")
    db.add(new_genre)
    db.commit()
    return new_genre

@pytest.fixture(scope="function")
def country(db):
    """Creates a new country for each test."""
    new_country = Country(country_name="Test Country")
    db.add(new_country)
    db.commit()
    return new_country

@pytest.fixture(scope="function")
def actor(db):
    """Creates a new actor for each test."""
    new_actor = Actor(
        first_name="Test",
        last_name="Actor",
        birth_day=date(1990, 1, 1),
        description="A test actor."
    )
    db.add(new_actor)
    db.commit()
    return new_actor
