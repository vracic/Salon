from contextlib import contextmanager

from psycopg2.pool import ThreadedConnectionPool

from app.config import settings


connection_pool: ThreadedConnectionPool | None = None


def get_connection_pool() -> ThreadedConnectionPool:
    global connection_pool
    if connection_pool is None:
        connection_pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=settings.database_url,
        )
    return connection_pool


@contextmanager
def get_connection():
    pool = get_connection_pool()
    connection = pool.getconn()
    try:
        yield connection
    finally:
        pool.putconn(connection)


@contextmanager
def get_cursor(commit: bool = False):
    with get_connection() as connection:
        cursor = connection.cursor()
        try:
            yield cursor
            if commit:
                connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()


def test_connection() -> bool:
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                return bool(row and row[0] == 1)
    except Exception:
        return False


def create_korisnik(
    ime: str,
    prezime: str,
    broj_mobitela: str,
    email: str | None,
    username: str | None,
    password_hash: str,
) -> dict:
    sql = """
        INSERT INTO korisnici (ime, prezime, broj_mobitela, email, username, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, ime, prezime, broj_mobitela, email, username, rola_id
    """
    with get_cursor(commit=True) as cur:
        cur.execute(sql, (ime, prezime, broj_mobitela, email, username, password_hash))
        row = cur.fetchone()
        if row is None:
            raise RuntimeError("korisnik_insert_returned_no_row")
        return {
            "id": row[0],
            "ime": row[1],
            "prezime": row[2],
            "broj_mobitela": row[3],
            "email": row[4],
            "username": row[5],
            "rola_id": row[6],
        }


def get_korisnik_by_email(email: str) -> dict | None:
    sql = "SELECT id, ime, prezime, broj_mobitela, email, username, password_hash, rola_id FROM korisnici WHERE email = %s"
    with get_cursor() as cur:
        cur.execute(sql, (email,))
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "ime": row[1],
            "prezime": row[2],
            "broj_mobitela": row[3],
            "email": row[4],
            "username": row[5],
            "password_hash": row[6],
            "rola_id": row[7],
        }


def get_korisnik_by_username(username: str) -> dict | None:
    sql = "SELECT id, ime, prezime, broj_mobitela, email, username, password_hash, rola_id FROM korisnici WHERE username = %s"
    with get_cursor() as cur:
        cur.execute(sql, (username,))
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "ime": row[1],
            "prezime": row[2],
            "broj_mobitela": row[3],
            "email": row[4],
            "username": row[5],
            "password_hash": row[6],
            "rola_id": row[7],
        }


def get_korisnik_by_id(korisnik_id: int) -> dict | None:
    sql = "SELECT id, ime, prezime, broj_mobitela, email, username, rola_id FROM korisnici WHERE id = %s"
    with get_cursor() as cur:
        cur.execute(sql, (korisnik_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "ime": row[1],
            "prezime": row[2],
            "broj_mobitela": row[3],
            "email": row[4],
            "username": row[5],
            "rola_id": row[6],
        }
