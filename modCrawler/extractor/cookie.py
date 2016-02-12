import sqlite3
import os
FF_COOKIE_DB_FILENAME = "cookies.sqlite"


def get_ff_cookies(profile_dir):
    cookie_db = os.path.join(profile_dir, FF_COOKIE_DB_FILENAME)
    if not os.path.isfile(cookie_db):
        print "Error: Cannot find cookie.db", cookie_db
        return None
    conn = sqlite3.connect(cookie_db)
    with conn:
        c = conn.cursor()
        c.execute("""select baseDomain, name, value, host, path, expiry,
                    lastAccessed, creationTime, isSecure, isHttpOnly
                    from moz_cookies""")
        rows = c.fetchall()
        return rows
