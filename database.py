from sqlalchemy import engine, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

engine = create_engine('sqlite:///database.db')
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()

Base.query = db_session.query_property()

def get_db():
    Base.metadata.create_all(bind=engine)