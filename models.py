from sqlalchemy import String, Integer, ForeignKey, Date, Column, DateTime
from database import Base


class Country(Base):
    __tablename__ = "country"

    country_name = Column(String, primary_key=True)


class Genre(Base):
    __tablename__ = "genre"

    genre = Column(String, primary_key=True)


class Actor(Base):
    __tablename__ = "actor"

    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_day = Column(String, nullable=False)
    death_day = Column(String)
    description = Column(String, nullable=False)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    birth_date = Column(Date, nullable=False)
    photo = Column(String)
    additional_info = Column(String)


class Film(Base):
    __tablename__ = "film"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    year = Column(Date, nullable=False)
    poster = Column(String, unique=True, nullable=False)

    genre = Column("genre", String)

    actors = Column("actors", String, nullable=False)

    description = Column("describtion", String, nullable=False)

    rating = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)

    country_name = Column("country", String, ForeignKey("country.country_name"), nullable=False)
    added_at = Column(DateTime, nullable=False)


class MovieList(Base):
    __tablename__ = "list"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)

    film_id = Column("film", Integer, ForeignKey("film.id"), nullable=False)
    user_id = Column("user", Integer, ForeignKey("user.id"), nullable=False)

    grade = Column(Integer, nullable=False)
    description = Column("describtion", String, nullable=False)


class ActorFilm(Base):
    __tablename__ = "actor_film"

    id = Column(Integer, primary_key=True)
    film_id = Column(Integer, ForeignKey("film.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("actor.id"), nullable=False)


class GenreFilm(Base):
    __tablename__ = "genre_film"

    id = Column(Integer, primary_key=True)
    film_id = Column(Integer, ForeignKey("film.id"), nullable=False)
    genre_id = Column(String, ForeignKey("genre.genre"), nullable=False)


class FilmList(Base):
    __tablename__ = "film_list"

    film_id = Column(Integer, ForeignKey("film.id"), primary_key=True)
    list_id = Column(Integer, ForeignKey("list.id"), primary_key=True)
