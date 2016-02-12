import os
import sqlite3 as sq
import crawler.common as cm
import utils.file_utils as fu
from utils.gen_utils import hash_text
from extractor.localstorage import get_ls_origin_from_scope
from multiprocessing import Lock
from time import sleep
import traceback


class DBTable:
    CANVAS = 1
    VISIT = 2
    LOCALSTORAGE = 3
    COOKIE = 4
    INDEXEDDB = 5
    CACHE = 6
    METADATA = 7
    LSO = 8
    HTTP_MSGS = 9


class DBCmd:
    ADD_VISIT = 1
    ADD_LSO_ITEMS = 2
    ADD_CANVAS = 3
    ADD_LOCALSTORAGE = 4
    ADD_INDEXEDDB = 5
    ADD_CACHE_ITEMS = 6
    ADD_METADATA = 7
    VISIT_BY_ID = 8
    GET_COOKIES = 9
    CANVAS_BY_ID = 10
    LOCALSTORAGE_BY_VISIT_ID = 11
    UPDATE_VISIT = 12
    ADD_INDEXEDDB_ITEMS = 13
    ADD_LOCALSTORAGE_ITEMS = 14
    ADD_COOKIES = 15
    INDEXEDDB_BY_VISIT_ID = 16
    ADD_ALL_VISIT_DATA = 17
    GET_CACHE = 18
    GET_FLASH_COOKIES = 19
    COUNT_VISITS = 20
    COUNT_COOKIES = 21
    COUNT_LOCALSTORAGE = 22
    COUNT_LSO = 23
    GET_CANVAS_META = 24
    GET_CANVAS_SCRIPTS_BY_META_ID = 25
    GET_PAGES_BY_META_ID = 26
    GET_VISIT_DATES = 27
    COUNT_SITES_BY_CANVAS_SCRIPT = 28
    GET_CANVAS_SCRIPTS = 29
    GET_RANK_AND_URLS_BY_CANVAS_SCRIPTS = 30
    GET_CANVAS_EVENTS_BY_SCRIPT = 31
    GET_XSITE_FLASH_COOKIES = 32
    GET_XSITE_LOCALSTORAGE = 33
    ADD_HTTP_HEADERS = 34
    GET_HTTP_HEADERS_BY_VISIT_ID = 35
    GEN_VISITS = 36
    GET_DISTINCT_ETAGS = 37
    GREP_IN_VISIT_DATA = 38
    GET_DISTINCT_FROM_DB = 39
    GREP_IN_PROFILE_DATA = 40
    GREP_IN_VISIT_COOKIES = 41
    GREP_IN_REQ_URLS = 42
    GET_REDIRECTIONS = 43
    GET_POST_MSGS = 44


def create_db_from_schema(db_file, schema_file=cm.DB_SCHEMA):
    schema = fu.read_file(schema_file)
    with sq.connect(db_file, timeout=cm.DB_CONN_TIMOEUT) as conn:
        cursor = conn.cursor()
        cursor.executescript(schema)


def insert_flash_cookies(cursor, visit_info, rows):
    # lso.rank is not really a rank.
    for lso in rows:
        cursor.execute("INSERT INTO flash_cookies VALUES "
                       "(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       ((None, visit_info.visit_id, visit_info.url) +
                        (lso.initiator, lso.js_file, lso.cookie_path, lso.key,
                        lso.log_text, lso.mode)))


def update_visit(cursor, visit_info, be):
    cursor.execute("UPDATE visit SET duration=?, incomplete=? WHERE id=?",
                   (visit_info.duration, visit_info.incomplete,
                    visit_info.visit_id))


def insert_visit_event(cursor, visit_info, be):
    cursor.execute("INSERT INTO visit VALUES (?, ?, ?, ?, ?, ?)",
                   (None, visit_info.url, visit_info.start_time,
                    visit_info.rank, visit_info.duration,
                    visit_info.incomplete))
    return cursor.lastrowid


def insert_canvas_events(cursor, visit_info, events):
    for be in events:
        try:
            insert_canvas_event(cursor, visit_info, be)
        except Exception as exc:
            print "insert_canvas_events", be.event_type, be.log_text, exc,
            traceback.format_exc()
            raise


def insert_canvas_event(cursor, visit_info, be):
    meta_id = 0
    if be.event_type in cm.CANVAS_ALL_EVENTS:
        metadata_hash = hash_text(be.log_text)
        cursor.execute("SELECT id FROM metadata WHERE hash=:Hash and "
                       "event_type=:event_type",
                       {"Hash": metadata_hash, "event_type": be.event_type})
        meta_id = cursor.fetchone()

        if meta_id is None:
            cursor.execute("INSERT INTO metadata VALUES (?, ?, ?, ?)",
                           (None, be.event_type, be.log_text, metadata_hash))
            meta_id = cursor.lastrowid
        else:
            meta_id = meta_id[0]  # fetchone returns a tuple

    cursor.execute("INSERT INTO canvas VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (None, visit_info.visit_id, be.url, be.js_file,
                    be.js_line, be.event_type, 0, meta_id))
    return cursor.lastrowid


def insert_ff_cookies(cursor, visit_info, rows):
    for row in rows:
        cursor.execute("INSERT INTO cookies VALUES "
                       "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       ((None, visit_info.visit_id, visit_info.url) + row))


def insert_all_visit_data(cursor, visit_info, db_jobs):
    for db_cmd, data in db_jobs.iteritems():
        if not data:
            continue
        try:
            if db_cmd == DBCmd.ADD_CANVAS:
                insert_canvas_events(cursor, visit_info, data)
            elif db_cmd == DBCmd.ADD_VISIT:
                insert_visit_event(cursor, visit_info, data)
            elif db_cmd == DBCmd.UPDATE_VISIT:
                update_visit(cursor, visit_info, data)
            elif db_cmd == DBCmd.ADD_COOKIES:
                insert_ff_cookies(cursor, visit_info, data)
            elif db_cmd == DBCmd.ADD_LOCALSTORAGE_ITEMS:
                insert_localstorage_items(cursor, visit_info, data)
            elif db_cmd == DBCmd.ADD_INDEXEDDB_ITEMS:
                insert_indexed_db_items(cursor, visit_info, data)
            elif db_cmd == DBCmd.ADD_CACHE_ITEMS:
                insert_cache_items(cursor, visit_info, data)
            elif db_cmd == DBCmd.ADD_LSO_ITEMS:
                insert_flash_cookies(cursor, visit_info, data)
            elif db_cmd == DBCmd.ADD_HTTP_HEADERS:
                insert_http_headers(cursor, visit_info, data)
        except (sq.InterfaceError, sq.ProgrammingError) as ie:
            cm.print_error(visit_info, "Error inserting to DB %s %s %s" %
                           (visit_info.url, db_cmd, ie))


def insert_http_headers(cursor, visit_info, data):
    SKIP_INSERT = ("Accept", "Accept-Language", "Accept-Encoding",
                   "User-Agent", "Connection")
    for http_msg in data:
        req_hdrs = http_msg["req_headers"]
        resp_hdrs = http_msg["resp_headers"]
        cursor.execute("INSERT INTO http_msgs VALUES \
                (?, ?, ?, ?, ?, ?)", (None, visit_info.visit_id,
                                      visit_info.url, http_msg["req_url"],
                                      http_msg["method"], http_msg["referer"]))
        msg_id = cursor.lastrowid
        for name, value in req_hdrs:
            if name not in SKIP_INSERT:
                cursor.execute("INSERT INTO req_headers VALUES \
                        (?, ?, ?, ?, ?)", (None, visit_info.visit_id,
                                           msg_id, name, value))
        if http_msg["req_content"]:
            cursor.execute("INSERT INTO req_headers VALUES \
                    (?, ?, ?, ?, ?)", (None, visit_info.visit_id,
                                       msg_id, "RequestBody",
                                       http_msg["req_content"]))

        for name, value in resp_hdrs:
            cursor.execute("INSERT INTO resp_headers VALUES \
                    (?, ?, ?, ?, ?)", (None, visit_info.visit_id,
                                       msg_id, name, value))


def insert_indexed_db_items(cursor, visit_info, rows):
    for idb_file, db_name, idb_rows in rows:
        cm.print_log(visit_info, "Adding IndexedDB to DB %s %s %s" %
                     (visit_info.url, idb_file, db_name))
        for idb_row in idb_rows:
            cursor.execute("INSERT INTO indexeddb VALUES "
                           "(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           ((None, visit_info.visit_id, idb_file, db_name) +
                            idb_row + ("", "")))


def insert_cache_items(cursor, visit_info, rows):
    for cache_item in rows:
        cursor.execute("INSERT INTO cache VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (None, visit_info.visit_id,
                        visit_info.url,
                        cache_item["Body"],
                        cache_item["Hash"],
                        cache_item["Expires"],
                        cache_item["Cache-Control"],
                        cache_item["Etag"],
                        cache_item['Request String']))


def insert_localstorage_items(cursor, visit_info, rows):
    for row in rows:
        cursor.execute("INSERT INTO localstorage VALUES (?, ?, ?, ?, ?, ?)",
                       (None, visit_info.visit_id, visit_info.url,
                        get_ls_origin_from_scope(row[0]), row[1], row[2]))


def insert_to_opened_db(cursor, table, data, visit_info):
    if table == DBCmd.ADD_CANVAS:
        return insert_canvas_event(cursor, visit_info, data)
    elif table == DBCmd.ADD_VISIT:
        return insert_visit_event(cursor, visit_info, data)
    elif table == DBCmd.UPDATE_VISIT:
        return update_visit(cursor, visit_info, data)
    elif table == DBCmd.ADD_COOKIES:
        return insert_ff_cookies(cursor, visit_info, data)
    elif table == DBCmd.ADD_LOCALSTORAGE_ITEMS:
        return insert_localstorage_items(cursor, visit_info, data)
    elif table == DBCmd.ADD_INDEXEDDB_ITEMS:
        return insert_indexed_db_items(cursor, visit_info, data)
    elif table == DBCmd.ADD_CACHE_ITEMS:
        return insert_cache_items(cursor, visit_info, data)
    elif table == DBCmd.ADD_ALL_VISIT_DATA:
        return insert_all_visit_data(cursor, visit_info, data)
    elif table == DBCmd.ADD_LSO_ITEMS:
        insert_flash_cookies(cursor, visit_info, data)
    elif table == DBCmd.ADD_HTTP_HEADERS:
        insert_http_headers(cursor, visit_info, data)


def insert_to_db(table, data, visit_info):
    """Insert event data to database."""
    for _ in xrange(0, cm.MAX_WAIT_FOR_DB_CONN):
        try:
            l = Lock()
            l.acquire()
            with sq.connect(visit_info.out_db,
                            timeout=cm.DB_CONN_TIMOEUT) as conn:
                cursor = conn.cursor()
                return insert_to_opened_db(cursor, table, data, visit_info)
            l.release()
        except sq.OperationalError:  # @UndefinedVariable
            l.release()
            sleep(1)
    cm.print_log(visit_info, "Cannot insert to DB (%s) URL: %s Table: (%s)" %
                 (visit_info.out_db, visit_info.url, table))


def get_db_entry(db, cmd, idx=None):
    if not os.path.isfile(db):
        raise cm.DBException("Can't find database file %s" % db)

    with sq.connect(db, timeout=cm.DB_CONN_TIMOEUT) as con:
        cursor = con.cursor()
        if cmd == DBCmd.CANVAS_BY_ID:
            return get_canvas_event(cursor, idx)
        if cmd == DBCmd.VISIT_BY_ID:
            return get_visit_info(cursor, idx)
        if cmd == DBCmd.GET_COOKIES:
            return gen_cookies(cursor, idx)
        if cmd == DBCmd.LOCALSTORAGE_BY_VISIT_ID:
            return gen_localstorage_by_visit_id(cursor, idx)
        if cmd == DBCmd.INDEXEDDB_BY_VISIT_ID:
            return gen_indexed_db_by_visit_id(cursor, idx)
        if cmd == DBCmd.GET_CACHE:
            return gen_cache(cursor, idx)
        if cmd == DBCmd.GET_FLASH_COOKIES:
            return gen_lso(cursor, idx)
        if cmd == DBCmd.COUNT_VISITS:
            return get_visit_count(cursor, idx)
        if cmd == DBCmd.COUNT_COOKIES:
            return get_cookie_count(cursor)
        if cmd == DBCmd.COUNT_LOCALSTORAGE:
            return get_localstorage_count(cursor)
        if cmd == DBCmd.COUNT_LSO:
            return get_lso_count(cursor)
        if cmd == DBCmd.GET_CANVAS_META:
            return get_canvas_meta(cursor)
        if cmd == DBCmd.GET_CANVAS_SCRIPTS_BY_META_ID:
            return get_scripts_by_meta_id(cursor, idx)
        if cmd == DBCmd.GET_PAGES_BY_META_ID:
            return get_pages_by_meta_id(cursor, idx)
        if cmd == DBCmd.GET_VISIT_DATES:
            return get_visit_dates(cursor)
        if cmd == DBCmd.COUNT_SITES_BY_CANVAS_SCRIPT:
            return get_site_no_for_canvas_url(cursor, idx)
        if cmd == DBCmd.GET_CANVAS_SCRIPTS:
            return get_canvas_scripts(cursor)
        if cmd == DBCmd.GET_RANK_AND_URLS_BY_CANVAS_SCRIPTS:
            return get_rank_and_url_list_by_script_urls(cursor, idx)
        if cmd == DBCmd.GET_CANVAS_EVENTS_BY_SCRIPT:
            return get_canvas_events_by_script(cursor, idx)
        if cmd == DBCmd.GET_XSITE_FLASH_COOKIES:
            return get_evercookie_candidates(cursor)
        if cmd == DBCmd.GET_XSITE_LOCALSTORAGE:
            return get_xsite_localstorage(cursor)
        if cmd == DBCmd.GET_HTTP_HEADERS_BY_VISIT_ID:
            return get_http_headers(cursor, idx)
        if cmd == DBCmd.GEN_VISITS:
            return gen_visit(cursor, idx)
        if cmd == DBCmd.GET_DISTINCT_FROM_DB:
            return get_distinct_from_db(cursor, idx)
        if cmd == DBCmd.GREP_IN_VISIT_DATA:
            return grep_in_visit_data(cursor, idx)
        if cmd == DBCmd.GREP_IN_VISIT_COOKIES:
            return grep_in_visit_cookies(cursor, idx)
        if cmd == DBCmd.GREP_IN_PROFILE_DATA:
            return grep_in_profile_data(cursor, idx)
        if cmd == DBCmd.GREP_IN_REQ_URLS:
            return grep_in_req_urls(cursor, idx)
        if cmd == DBCmd.GET_REDIRECTIONS:
            return get_redirections(cursor, idx)
        if cmd == DBCmd.GET_POST_MSGS:
            return get_post_msgs(cursor, idx)
        else:
            raise Exception("DB: No such method")


def get_post_msgs(cursor, visit_id=None):
    if visit_id is None:
        return cursor.execute("SELECT * FROM http_msgs WHERE method = 'POST'")
    else:
        return cursor.execute("SELECT * FROM http_msgs WHERE method = 'POST' "
                              "AND visit_id=:visit_id",
                              {"visit_id": visit_id})


def get_redirections(cursor, visit_id=None):
    if visit_id is None:
        return cursor.execute("SELECT * FROM resp_headers WHERE "
                              "name = 'Location'")
    else:
        return cursor.execute("SELECT * FROM resp_headers WHERE name = 'Location' \
                                AND visit_id=:visit_id",
                              {"visit_id": visit_id})


def grep_in_profile_data(cursor, (string, visit_id, table)):
    cookie = []
    if table != DBTable.COOKIE:
        cookie = cursor.execute("SELECT * FROM moz_cookies WHERE value like ?",
                                ("%" + string + "%",)).fetchall()
    return {"cookie": cookie}


def grep_in_visit_cookies(cursor, string):
    return cursor.execute("SELECT * FROM cookies WHERE value like ?",
                          ("%" + string + "%",)).fetchall()


def grep_in_req_urls(cursor, string):
    return cursor.execute("SELECT * FROM http_msgs, visit WHERE req_url like ? \
                            AND http_msgs.visit_id = visit.id",
                          ("%" + string + "%",)).fetchall()


def grep_in_visit_data(cursor, (string, visit_id, exclude_table)):
    cookie, http_msg, lso, local_storage = [], [], [], []
    if exclude_table != DBTable.COOKIE:
        cookie = cursor.execute("SELECT * FROM cookies WHERE  visit_id = ? and"
                                " value like ?",
                                (visit_id, "%" + string + "%")).fetchall()

    if exclude_table != DBTable.HTTP_MSGS:
        http_msg = cursor.execute("SELECT * FROM http_msgs WHERE visit_id = ?"
                                  " and req_url like ?",
                                  (visit_id, "%" + string + "%")).fetchall()
    if exclude_table != DBTable.LSO:
        lso = cursor.execute("SELECT * FROM flash_cookies WHERE visit_id = ?"
                             " and content like ?",
                             (visit_id, "%" + string + "%")).fetchall()

    if exclude_table != DBTable.LOCALSTORAGE:
        local_storage = cursor.execute("SELECT * FROM localstorage WHERE "
                                       "visit_id = ? and value like ?",
                                       (visit_id,
                                        "%" + string + "%")).fetchall()

    # Shall we ever do that?
    request_content = cursor.execute("SELECT * FROM req_headers "
                                     "WHERE visit_id = ? and "
                                     "name = ?  and value like ?",
                                     (visit_id, "RequestBody",
                                      "%" + string + "%")).fetchall()

    return {"cookie": cookie, "http_msg": http_msg, "lso": lso,
            "local_storage": local_storage, "request_content": request_content}


def get_distinct_from_db(cursor, (column, table)):
    return cursor.execute("SELECT Distinct %s FROM %s" %
                          (column, table)).fetchall()


def get_http_headers(cursor, visit_id):
    return cursor.execute("SELECT * FROM (req_headers left join resp_headers "
                          "on resp_headers.msg_id = req_headers.msg_id) left "
                          "join http_msgs on req_headers.msg_id = http_msgs.id"
                          " WHERE http_msgs.visit_id =:visit_id",
                          {"visit_id": visit_id}).fetchall()


def get_xsite_localstorage(cursor):
    return cursor.execute("""SELECT COUNT(*), FC.scope, FC.key, FC.value
        FROM (SELECT DISTINCT value, page_url, key, scope
        FROM localstorage) AS FC
        WHERE LENGTH(FC.value) > 5 AND LENGTH(FC.value) < 100
        GROUP BY value HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC""").fetchall()


def get_evercookie_candidates(cursor):
    return cursor.execute("""SELECT COUNT(*), FC.domain, FC.key, FC.content, FC.filename
        FROM (SELECT DISTINCT content, page_url, key, filename, domain FROM
        flash_cookies) AS FC WHERE LENGTH(FC.content) > 5  AND
        LENGTH(FC.content) < 100 GROUP BY content
        HAVING COUNT(*) > 1 ORDER BY COUNT(*) DESC""").fetchall()


def get_canvas_events_by_script(cursor, url):
    return cursor.execute("""SELECT DISTINCT event_meta_id, value,
        metadata.event_type
        FROM canvas, metadata
        WHERE canvas.event_meta_id = metadata.id
        and canvas.script_url =:scr_url""", {"scr_url": url}).fetchall()


def get_rank_and_url_list_by_script_urls(cursor, urls):
    # TODO: move script url to meta table and select by id here
    return cursor.execute("SELECT distinct rank, url FROM visit, canvas"
                          " WHERE script_url IN (%s) AND "
                          "(visit.id = canvas.visit_id)" %
                          ','.join('?' * len(urls)), urls).fetchall()


def get_canvas_scripts(cursor):
    return cursor.execute("SELECT Distinct script_url FROM canvas").fetchall()


def get_site_no_for_canvas_url(cursor, url):
    # we could count visit_id's but let's assume
    return cursor.execute("SELECT Count(Distinct page_url) AS countsites"
                          " FROM canvas WHERE script_url=:scr_url",
                          {"scr_url": url}).fetchone()


def get_visit_dates(cursor):
    return cursor.execute("SELECT MIN(start_time), "
                          "MAX(start_time) FROM visit").fetchone()


def get_scripts_by_meta_id(cursor, meta_id):
    return cursor.execute("SELECT distinct script_url "
                          "FROM canvas WHERE event_meta_id =:Id",
                          {"Id": meta_id}).fetchall()


def get_pages_by_meta_id(cursor, meta_id):
    return cursor.execute("SELECT distinct rank, page_url"
                          " FROM canvas, visit WHERE (event_meta_id =:Id)"
                          " AND (visit.id = canvas.visit_id)",
                          {"Id": meta_id}).fetchall()


def get_canvas_meta(cursor):
    return cursor.execute("SELECT * FROM metadata").fetchall()


def get_lso_count(cursor):
    return cursor.execute("SELECT count(*) FROM flash_cookies").fetchone()


def get_localstorage_count(cursor):
    return cursor.execute("SELECT count(*) FROM localstorage").fetchone()


def get_cookie_count(cursor):
    return cursor.execute("SELECT count(*) FROM cookies").fetchone()


def get_visit_count(cursor, only_complete=False):
    if only_complete:
        return cursor.execute("SELECT COUNT(*) FROM visit"
                              " WHERE incomplete = 0").fetchone()
    else:
        return cursor.execute("SELECT COUNT(*) FROM visit").fetchone()


def gen_cookies(cursor, visit_id=None):
    if visit_id is None:
        return cursor.execute("SELECT * FROM cookies")
    else:
        return cursor.execute("SELECT * FROM cookies WHERE visit_id=:Id",
                              {"Id": visit_id})


def gen_cache(cursor, visit_id):
    if visit_id is None:
        return cursor.execute("SELECT * FROM cache")
    else:
        return cursor.execute("SELECT * FROM cache WHERE visit_id=:Id",
                              {"Id": visit_id})


def gen_visit(cursor, visit_id):
    if visit_id is None:
        return cursor.execute("SELECT * FROM visit")
    elif visit_id == -1:
        return cursor.execute("SELECT * FROM visit WHERE incomplete = 0")
    else:
        return cursor.execute("SELECT * FROM visit WHERE visit_id=:Id",
                              {"Id": visit_id})


def gen_lso(cursor, visit_id):
    if visit_id is None:
        return cursor.execute("SELECT * FROM flash_cookies")
    else:
        return cursor.execute("SELECT * FROM flash_cookies WHERE visit_id=:Id",
                              {"Id": visit_id})


def gen_localstorage_by_visit_id(cursor, visit_id):
    return cursor.execute("SELECT * FROM localstorage WHERE visit_id=:Id",
                          {"Id": visit_id})


def gen_indexed_db_by_visit_id(cursor, visit_id):
    return cursor.execute("SELECT * FROM indexeddb WHERE visit_id=:Id",
                          {"Id": visit_id})


def get_visit_info(cur, visit_id):
    cur.execute("SELECT * FROM visit WHERE id=:Id",
                {"Id": visit_id})
    visit_row = cur.fetchone()
    vi = cm.VisitInfo()
    vi.visit_id, vi.url, vi.start_time, \
        vi.rank, vi.duration, vi.incomplete = visit_row
    return vi


def get_canvas_event(cur, canvas_ev_id):
    cur.execute("SELECT * FROM canvas WHERE id=:Id",
                {"Id": canvas_ev_id})
    canvas_row = cur.fetchone()
    be = cm.BrowserEvent()
    _, visit_id, be.url, be.js_file, be.js_line, be.event_type,\
        event_time, data_url_id = canvas_row
    return visit_id, data_url_id, event_time, be

if __name__ == '__main__':
    pass
