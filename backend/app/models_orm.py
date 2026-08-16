from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
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


class Usluga(Base):
    __tablename__ = "usluge"

    __table_args__ = (
        CheckConstraint("trajanje > 0", name="ck_usluge_trajanje_pozitivno"),
        CheckConstraint("cijena >= 0.00", name="ck_usluge_cijena_nenegativna"),
    )

    id = Column(Integer, primary_key=True)
    naziv = Column(String(150), nullable=False, unique=True)
    trajanje = Column(Integer, nullable=False)
    cijena = Column(DECIMAL(10, 2), nullable=False)


class StatusRezervacija(Base):
    __tablename__ = "statusrezervacija"

    id = Column(Integer, primary_key=True)
    naziv = Column(String(50), nullable=False, unique=True)


class RadnoVrijeme(Base):
    __tablename__ = "radnovrijeme"

    __table_args__ = (
        CheckConstraint("vrijeme_do > vrijeme_od", name="provjera_smjene"),
        Index("idx_radno_vrijeme_raspon", "vrijeme_od", "vrijeme_do"),
    )

    id = Column(Integer, primary_key=True)
    vrijeme_od = Column(DateTime(timezone=True), nullable=False)
    vrijeme_do = Column(DateTime(timezone=True), nullable=False)


class Rezervacija(Base):
    __tablename__ = "rezervacije"

    __table_args__ = (
        CheckConstraint("kraj > pocetak", name="provjera_trajanja"),
        Index(
            "idx_aktivne_rezervacije",
            "pocetak",
            "kraj",
            "status_id",
            postgresql_where=text("status_id IN (1, 2)"),
        ),
    )

    id = Column(Integer, primary_key=True)
    pocetak = Column(DateTime(timezone=True), nullable=False)
    kraj = Column(DateTime(timezone=True), nullable=False)
    biljeska = Column(Text)
    usluga_id = Column(Integer, ForeignKey("usluge.id", ondelete="RESTRICT"), nullable=False)
    klijent_id = Column(Integer, ForeignKey("korisnici.id", ondelete="CASCADE"), nullable=False)
    status_id = Column(Integer, ForeignKey("statusrezervacija.id"), nullable=False, default=1)


class KlijentBiljeska(Base):
    __tablename__ = "klijentbiljeska"

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    rezervacija_id = Column(Integer, ForeignKey("rezervacije.id", ondelete="CASCADE"), nullable=False, unique=True)


class Recenzija(Base):
    __tablename__ = "recenzije"

    __table_args__ = (
        CheckConstraint("ocjena BETWEEN 1 AND 5", name="ck_recenzije_ocjena_raspon"),
        Index("idx_brzo_grupisanje_recenzija", "usluga_id", "ocjena"),
    )

    id = Column(Integer, primary_key=True)
    ocjena = Column(Integer, nullable=False)
    komentar = Column(Text)
    rezervacija_id = Column(Integer, ForeignKey("rezervacije.id", ondelete="CASCADE"), nullable=False, unique=True)
    usluga_id = Column(Integer, ForeignKey("usluge.id", ondelete="CASCADE"), nullable=False)
    klijent_id = Column(Integer, ForeignKey("korisnici.id", ondelete="CASCADE"), nullable=False)


class ListaCekanja(Base):
    __tablename__ = "listacekanja"

    __table_args__ = (
        CheckConstraint("vrijeme_do > vrijeme_od", name="provjera_cekanja"),
        Index(
            "idx_red_cekanja_aktivno",
            "vrijeme_od",
            "obavijesten",
            postgresql_where=text("obavijesten = FALSE"),
        ),
    )

    id = Column(Integer, primary_key=True)
    vrijeme_od = Column(DateTime(timezone=True), nullable=False)
    vrijeme_do = Column(DateTime(timezone=True), nullable=False)
    obavijesten = Column(Boolean, default=False)
    usluga_id = Column(Integer, ForeignKey("usluge.id", ondelete="CASCADE"), nullable=False)
    klijent_id = Column(Integer, ForeignKey("korisnici.id", ondelete="CASCADE"), nullable=False)
