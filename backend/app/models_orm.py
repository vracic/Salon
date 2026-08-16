from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class Korisnickarola(Base):
    __tablename__ = "korisnickarola"

    id = Column(Integer, primary_key=True)
    naziv = Column(String(50), nullable=False, unique=True)


class Korisnik(Base):
    __tablename__ = "korisnici"

    id = Column(Integer, primary_key=True)
    ime = Column(String(100), nullable=False)
    prezime = Column(String(100), nullable=False)
    broj_mobitela = Column(String(50), unique=True)
    email = Column(String(255), unique=True)
    username = Column(String(100), unique=True)
    password_hash = Column(String(255))
    rola_id = Column(Integer, ForeignKey("korisnickarola.id"), nullable=False, default=2)
