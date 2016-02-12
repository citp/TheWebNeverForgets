from utils.file_utils import gen_cat_file
import cookie
import localstorage as ls
import indexedDB
import lso
from os.path import join
from glob import glob
import time
from sets import Set
import crawler.common as cm
import crawler.mitm as mitm
import utils.db_utils as dbu
import cache as cu

WAL_CHECKPOINT_DEBUGGING = 0


def check_canvas_rw_access(calls):
    """Return True if logs include both read and write access to canvas."""
    # TODO: process calls per domain
    urls_read_from_canvas = Set()
    urls_wrote_to_canvas = Set()
    for call in calls:
        if call.event_type in cm.CANVAS_READ_EVENTS:
            urls_read_from_canvas.add(call.js_file)
        elif call.event_type in cm.CANVAS_WRITE_EVENTS:
            urls_wrote_to_canvas.add(call.js_file)
    return list(urls_read_from_canvas & urls_wrote_to_canvas)


def ff_log_parser(log_file, visit_info):
    events = []
    fp_events = []
    for line in gen_cat_file(log_file):
        # print line
        if line.startswith("FPD"):
            line = line.replace("FPD\t", "").rstrip()
            be = cm.BrowserEvent()
            log_items = line.split("\t")
            if len(log_items) == 5:
                be.initiator, be.event_type, be.js_file,\
                    be.js_line, be.log_text = log_items
                be.url = visit_info.url
                be.rank = visit_info.rank
                events.append(be)
            elif len(log_items) == 4 and log_items[1] in cm.EVENTS_WITH_4_ARGS:
                be.initiator, cm.event_type, be.js_file,\
                    be.js_line = log_items
                # filter out screenshots taken by browser for page thumbnails
                if not be.js_line.startswith('resource'):
                    events.append(be)
            else:
                print "Hmm WAT!:", log_items

    canvas_fp_urls = check_canvas_rw_access(events)
    for canvas_fp_url in canvas_fp_urls:
        for event in events:
            # we only add events from this URL
            if event.js_file == canvas_fp_url:
                fp_events.append(event)
    return fp_events, events


def tmp_sqlite_files_exist(path):
    """Check if temporary sqlite files(wal, shm) exist in a given path."""
    return glob(join(path, '*-wal')) or\
        glob(join(path, '*-shm'))


def sleep_until_sqlite_checkpoint(profile_dir, timeout=30):
    """We wait until all the shm and wal files are checkpointed to DB.

    https://www.sqlite.org/wal.html#ckpt.
    """
    waited = 0
    while (waited < timeout and tmp_sqlite_files_exist(profile_dir)):
        time.sleep(1)
        waited += 1
    if WAL_CHECKPOINT_DEBUGGING:
        print "Waited %s seconds for sqlite checkpointing" % (waited)


def process_crawler_output(ff_log_file, visit_info, flash=1):
    # wait until tmp files are merged to db, otherwise we won't
    # find the recently added items in db

    db_jobs = {}
    flash_cookies = []
    sleep_until_sqlite_checkpoint(visit_info.profile_dir)

    cache_entries = cu.get_ff_cache(visit_info.profile_dir)
    db_jobs[dbu.DBCmd.ADD_CACHE_ITEMS] = cache_entries

    js_calls, all_calls = ff_log_parser(ff_log_file, visit_info)
    db_jobs[dbu.DBCmd.ADD_CANVAS] = js_calls

    cookies = cookie.get_ff_cookies(visit_info.profile_dir)
    db_jobs[dbu.DBCmd.ADD_COOKIES] = cookies

    local_storage_entries = ls.get_ff_local_storage(visit_info.profile_dir)
    db_jobs[dbu.DBCmd.ADD_LOCALSTORAGE_ITEMS] = local_storage_entries

    indexed_db_entries = indexedDB.gen_ff_indexedDB(visit_info)
    db_jobs[dbu.DBCmd.ADD_INDEXEDDB_ITEMS] = indexed_db_entries

    if flash:
        time.sleep(5)  # strace logs may not be available immediately
        flash_cookies = lso.parse_strace_logs(visit_info)
        db_jobs[dbu.DBCmd.ADD_LSO_ITEMS] = flash_cookies

    http_msgs = list(mitm.parse_mitm_dump(visit_info.http_dump))
    db_jobs[dbu.DBCmd.ADD_HTTP_HEADERS] = http_msgs

    dbu.insert_to_db(dbu.DBCmd.ADD_ALL_VISIT_DATA, db_jobs, visit_info)

    return {"calls": all_calls,
            "cookies": cookies,
            "flash_cookies": flash_cookies,
            "local_storage": local_storage_entries,
            "indexed_db": indexed_db_entries,
            "cache": cache_entries,
            "http_msgs": http_msgs}

if __name__ == '__main__':
    pass
