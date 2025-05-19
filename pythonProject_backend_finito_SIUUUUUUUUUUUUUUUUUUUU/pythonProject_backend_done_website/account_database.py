from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Definizione del database (SQLite in questo esempio)
engine = create_engine('sqlite:///accounts.db', echo=False)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)

    def __repr__(self):
        return f"<User(username='{self.username}', is_admin={self.is_admin})>"

# Creazione di una sessione per le operazioni CRUD
Session = sessionmaker(bind=engine)
session = Session()

if __name__ == '__main__':
    # Crea le tabelle nel database
    Base.metadata.create_all(engine)

    # Esempio: creare un nuovo utente
    # new_user = User(username='mario', password='segreta', is_admin=True)
    # session.add(new_user)
    # session.commit()
    # print(new_user)
