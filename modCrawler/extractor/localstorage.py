import sqlite3
import os
FF_LOCALSTORAGE_DB_FILENAME = "webappsstore.sqlite"


def get_ls_origin_from_scope(ls_scope):
    """Return origin in scheme:host:port form."""
    rev_host, scheme, port = ls_scope.rsplit(':', 2)
    host = rev_host[::-1]
    return '%s://%s:%s' % (scheme, host, port)


def get_ff_local_storage(profile_dir):
    ff_ls_file = os.path.join(profile_dir, FF_LOCALSTORAGE_DB_FILENAME)
    if not os.path.isfile(ff_ls_file):
        print "Cannot find the localstorage DB %s" % ff_ls_file

    conn = sqlite3.connect(ff_ls_file)
    with conn:
        c = conn.cursor()
        c.execute('select scope, KEY, value from webappsstore2')
        rows = c.fetchall()
        return rows
