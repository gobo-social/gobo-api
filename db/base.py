import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ.get("DB_URL"))
Session = sessionmaker(bind=engine)

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass