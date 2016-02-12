import os
import platform
from multiprocessing import Lock
from time import strftime
from urlparse import urlparse
expanduser = os.path.expanduser
join = os.path.join

if 'x86_64' in platform.processor():
    arch = '64'
else:
    arch = '32'


LOG_TO_CONSOLE = 1
LOG_TO_FILE = 2

NUM_PARALLEL_PROCS = 5  # use --max_proc cmd line argument to overwrite

FLASH_ENABLE = 1
FLASH_DISABLE = 0

COOKIE_ALLOW_ALL = 0
COOKIE_ALLOW_1ST_PARTY = 1
COOKIE_ALLOW_NONE = 2
COOKIE_ALLOW_3RD_PARTY_FROM_VISITED = 3


class CrawlInfo(object):
    min_rank = 1
    max_rank = 0
    upload_data = False
    max_parallel_procs = NUM_PARALLEL_PROCS
    flash_support = FLASH_ENABLE  # enable Flash
    cookie_support = COOKIE_ALLOW_ALL  # enable 1st and 3rd party cookies
    urls = ''


class VisitInfo(object):
    url = ""
    visit_id = 0
    start_time = None
    duration = 0
    incomplete = 1
    rank = 0
    profile_dir = ""
    out_db = ""
    out_dir = ""
    ff_log = ""
    err_log = ""
    sys_log = ""
    strace_proc = None
    sel_proc = ""
    debug_log = ""
    log_options = [LOG_TO_FILE]
    vdisplay = None


class BrowserEvent(object):

    def __str__(self):
        return "\t".join(["%s: %s" % (a, getattr(self, a)) for a in dir(self)
                          if not a.startswith('__')])

    event_type = ""  # filltext, todataurl etc.
    initiator = ""  # cpp file or the origin that is responsible for the event
    js_file = ""  # js file responsible for the call
    js_line = ""  # js line number responsible for the call
    log_text = ""  # the text if this is a fill_text call
    url = ""
    rank = 0
    cookie_path = ""
    key = ""
    mode = ""


class TimeExceededError(Exception):
    pass


class DBException(Exception):
    pass


DB_FILENAME = "crawl.sqlite"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
BASE_BIN_DIR = join(BASE_DIR, 'bins')
BASE_ETC_DIR = join(BASE_DIR, 'etc')
BASE_TMP_DIR = join(BASE_DIR, 'tmp')
BASE_DATA_DIR = join(BASE_DIR, 'data')
BASE_JOBS_DIR = join(BASE_DIR, 'jobs')
BASE_TEST_DIR = join(BASE_DIR, 'test')
BASE_TEST_FILES_DIR = join(BASE_TEST_DIR, 'files')
BASE_TEST_DATAURLS_DIR = join(BASE_TEST_DIR, 'dataurls')
DB_SCHEMA = join(BASE_ETC_DIR, "base.db.sql")
PY_REQUIREMENTS_FILE = join(BASE_ETC_DIR, 'requirements.txt')
STOP_CRAWL_FILE = join(BASE_DIR, "__STOPCRAWLING__")
FF_MOD_BIN = join(BASE_BIN_DIR, 'ff-mod/firefox')
# These two dirs are not used anymore.
# Webdriver accepts certificates from mitmproxy by default
MITM_PROXY_SRC_CERT_DIR = join(BASE_ETC_DIR, 'mitmcert')
MITM_PROXY_DST_CERT_DIR = expanduser("~/.mitmproxy/")

HOME_PATH = expanduser('~')

BASE_TEST_URL = 'https://securehomes.esat.kuleuven.be/~gacar/dev/test'
ONLINE_TEST_HOST = urlparse(BASE_TEST_URL).hostname
ONLINE_TEST_DOMAIN = "kuleuven.be"

WAIT_ON_SITE = 10
ALEXA_TOP_1M = join(BASE_ETC_DIR, 'top-1m.csv')

BR_TYPE_SELENIUM = 'selenium'
BR_TYPE_FIREFOX_CMDLINE = 'cmd'

HARD_TIME_OUT = 180
DB_CONN_TIMOEUT = 120
SOFT_TIMEOUT = 90
KILL_TIME_OUT = 5
TIME_OUT = 30
MAX_WAIT_FOR_DB_CONN = 30
# if CPU utilization is greater than this, the visitor process will sleep
# for a while proportional to the utilization
MIN_CPU_UTIL_FOR_SLEEP = 75
MAX_PRE_CRAWL_SLEEP = 30

EVENT_FILLTEXT = "FillText"
EVENT_STROKETEXT = "StrokeText"
EVENT_MEASURETEXT = "MeasureText"
EVENT_TODATAURL = "ToDataURL"
EVENT_EXTRACTDATA = "ExtractData"
EVENT_TOBLOB = "ToBlob"
EVENT_GET_IMAGE_DATA = "GetImageData"
EVENT_DRAW_IMAGE = "DrawImage"
EVENT_COOKIE = "Cookie"
EVENT_FLASH_LSO = "Flash LSO"
EVENT_LOCALSTORAGE = "localstorage"
EVENT_INDEXED_DB = "indexedDB"
EVENT_NEW_VISIT = "NewVisit"

CANVAS_READ_EVENTS = (EVENT_TODATAURL, EVENT_TOBLOB, EVENT_GET_IMAGE_DATA)
CANVAS_WRITE_EVENTS = (EVENT_FILLTEXT, EVENT_STROKETEXT)
CANVAS_ALL_EVENTS = CANVAS_READ_EVENTS + CANVAS_WRITE_EVENTS
EVENTS_WITH_4_ARGS = (EVENT_TOBLOB, EVENT_GET_IMAGE_DATA, EVENT_DRAW_IMAGE)

ACCESS_MODE_READ_WRITE = 0
ACCESS_MODE_READ_ONLY = 1

LOG_ERROR = 1
LOG_DEBUG = 2



def print_debug(visit_info, log_line, log_fname=None):
    print_log(visit_info, log_line,
              log_type=LOG_DEBUG,
              log_fname=log_fname)


def print_error(visit_info, log_line, log_fname=None):
    print_log(visit_info, log_line,
              log_type=LOG_ERROR,
              log_fname=log_fname)


def print_log(visit_info, log_line, log_type=LOG_ERROR, log_fname=None):
    time_str = strftime("%Y%m%d-%H%M%S")
    log_type_str = "ERROR" if log_type == LOG_ERROR else "DEBUG"
    log_str = "%s: %s %s\n" % (time_str, log_type_str, log_line)
    if visit_info:
        if LOG_TO_CONSOLE in visit_info.log_options:
            print log_str
        if LOG_TO_FILE in visit_info.log_options:
            if log_type == LOG_ERROR:
                log_file = visit_info.err_log
            else:
                log_file = visit_info.debug_log
    elif log_fname:
        log_file = log_fname
    else:
        print log_str
        return
    l = Lock()
    l.acquire()
    with open(log_file, 'a') as logfile:
        logfile.write(log_str)
    l.release()
