from sqlalchemy import String, Integer, ForeignKey, Date, Column, DateTime
from sqlalchemy.orm import relationship
from database.database import Base


class Country(Base):
    __tablename__ = "country"

    country_name = Column(String, primary_key=True)


class Genre(Base):
    __tablename__ = "genre"

    genre = Column(String, primary_key=True)


class Actor(Base):
    __tablename__ = "actor"

    id = Column(Integer, autoincrement=True, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_day = Column(Date, nullable=False)
    death_day = Column(Date)
    description = Column(String, nullable=False)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    login = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, unique=True, nullable=False)
    birth_date = Column(Date, nullable=False)
    photo = Column(String)
    additional_info = Column(String)

    def to_dict(self):
        return {"id": self.id, "first_name": self.first_name, "last_name": self.last_name, "login": self.login, "email": self.email, "phone_number": self.phone_number, "birth_date": self.birth_date, "additional_info": self.additional_info, "photo": self.photo}


class Film(Base):
    __tablename__ = "film"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    year = Column(Date, nullable=False)
    poster = Column(String, unique=True)

    genre = Column("genre", String)

    actor = Column("actor", String)

    description = Column(String, nullable=False)

    rating = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)

    country_name = Column("country", String, ForeignKey("country.country_name"), nullable=False)
    added_at = Column(DateTime, nullable=False)

    actors = relationship("Actor", secondary="actor_film", backref="films")
    genres = relationship("Genre", secondary="genre_film", backref="films")


    def to_dict(self):
        return {"id": self.id, "name": self.name, "year": self.year, "poster": self.poster, "genre": self.genre, "actor": self.actor, "description": self.description, "rating": self.rating, "duration": self.duration, "country": self.country_name}

class MovieList(Base):
    __tablename__ = "list"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)

    film_id = Column("film", Integer, ForeignKey("film.id"), nullable=False)
    user_id = Column("user", Integer, ForeignKey("user.id"), nullable=False)

    grade = Column(Integer, nullable=False)
    description = Column("describtion", String, nullable=False)


class ActorFilm(Base):
    __tablename__ = "actor_film"

    id = Column(Integer, primary_key=True, autoincrement=True)
    film_id = Column(Integer, ForeignKey("film.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("actor.id"), nullable=False)


class GenreFilm(Base):
    __tablename__ = "genre_film"

    id = Column(Integer, primary_key=True, autoincrement=True)
    film_id = Column(Integer, ForeignKey("film.id"), nullable=False)
    genre_id = Column(String, ForeignKey("genre.genre"), nullable=False)


class FilmList(Base):
    __tablename__ = "film_list"

    film_id = Column(Integer, ForeignKey("film.id"), primary_key=True)
    list_id = Column(Integer, ForeignKey("list.id"), primary_key=True)
