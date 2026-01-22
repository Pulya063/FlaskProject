from sqlalchemy import engine, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
import os

db_host = os.environ.get('DB_HOST', 'localhost')
SQLALCHEMY_DATABASE_URL = f"postgresql://admin:pass@{db_host}:5432/film_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()

Base.query = db_session.query_property()

def get_db():
    Base.metadata.create_all(bind=engine)