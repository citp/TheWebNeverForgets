import os
import shutil
import time
import traceback
import pipes
from os.path import join
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import selenium.common.exceptions as sel_exceptions
import crawler.common as cm
import crawler.mitm as mitm
import utils.db_utils as dbu
import utils.gen_utils as ut
from utils.file_utils import get_basename_from_url, rm
from extractor.extractor import process_crawler_output
from time import strftime, sleep
from pyvirtualdisplay import Display
import subprocess
import signal
import httplib
# TODO: make the following constants a part of crawler config
ENABLE_XVFB = True  # enable x virtual frame buffer
ENABLE_NSPR_LOGGING = False
CAPTURE_HTTP_W_MITM_PROXY = True
MAX_GET_DRIVER_TRIES = 5  # No of max retries for creating a webdriver object.


def open_log_file(out_dir, url):
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    basename = get_basename_from_url(url, "ff-%s" % ut.rand_str())
    return join(out_dir, '%s.log' % (basename))


def set_ff_prefs(ffp, proxy_port=None, flash_support=cm.FLASH_ENABLE,
                 cookie_support=cm.COOKIE_ALLOW_ALL):
    """Set default crawl preferences for FF profile."""
    set_pref = ffp.set_preference
    set_pref('network.cookie.cookieBehavior', cookie_support)
    set_pref('datareporting.healthreport.uploadEnabled', False)
    set_pref('toolkit.telemetry.enabled', False)
    set_pref('extensions.checkCompatibility.nightly', False)
    set_pref('browser.search.update', False)
    set_pref('browser.rights.3.shown', True)
    set_pref('browser.shell.checkDefaultBrowser', False)
    set_pref('security.OCSP.enabled', "0")
    set_pref('browser.safebrowsing.enabled', False)
    set_pref('devtools.profiler.enabled', False)
    set_pref('network.seer.enabled', False)  # predictive actions
    set_pref('network.dns.disablePrefetch', True)  # no need to prefetch
    set_pref('network.prefetch-next', False)  # no need to prefetch
    set_pref('browser.pagethumbnails.capturing_disabled', True)
    set_pref('browser.selfsupport.url', '')
    set_pref('browser.newtabpage.enabled', False)
    set_pref('geo.enabled', False)
    set_pref('geo.wifi.uri', '')
    set_pref('browser.search.geoip.url', '')
    set_pref('browser.search.geoSpecificDefaults.url', '')
    set_pref('privacy.trackingprotection.enabled', False)
    set_pref('privacy.trackingprotection.pbmode.enabled', False)
    set_pref('browser.safebrowsing.provider.mozilla.gethashURL', '')
    set_pref('browser.safebrowsing.provider.mozilla.updateURL', '')
    set_pref('browser.safebrowsing.provider.google.gethashURL', '')
    set_pref('layers.enable-tiles', False)
    set_pref('browser.newtabpage.directory.ping', '')
    set_pref('browser.newtabpage.directory.source', '')
    # To enable DNT header uncomment following lines
    # set_pref('privacy.donottrackheader.enabled', True)
    # set_pref('privacy.donottrackheader.value', 1)

    if not flash_support:
        set_pref('plugin.state.flash', 0)
        print "Disabling Flash"
    if proxy_port is not None:
        set_pref('network.proxy.http', "localhost")
        set_pref("network.proxy.http_port", proxy_port)
        set_pref('network.proxy.ssl', "localhost")
        set_pref("network.proxy.ssl_port", proxy_port)
        set_pref("network.proxy.type", 1)
        set_pref("network.proxy.share_proxy_settings", True)


def start_xvfb(win_w=1280, win_h=720):
    if ENABLE_XVFB:
        vdisplay = Display(visible=0, size=(win_w, win_h))
        vdisplay.start()
        return vdisplay


def stop_xvfb(vdisplay):
    if ENABLE_XVFB and vdisplay:
        vdisplay.stop()


def log_syscalls(proc, log_file):
    if type(proc.pid) != int:
        raise TypeError("Unexpected process id value %s" % proc.pid)
    dev_null = open(os.devnull, 'w')
    cmd = "/usr/bin/strace -p %d -f -s 512 -e open,read,write  2>&1"\
        " | grep SharedObjects > %s &" % (proc.pid, pipes.quote(log_file))

    return subprocess.Popen(cmd, stderr=dev_null, stdout=dev_null, shell=True)


def get_browser(ff_log_file, proxy_port=None, flash_support=cm.FLASH_ENABLE,
                cookie_support=cm.COOKIE_ALLOW_ALL):
    ff_log_file_handle = open(ff_log_file, "a+")
    ff_bin = FirefoxBinary(firefox_path=cm.FF_MOD_BIN,
                           log_file=ff_log_file_handle)

    ffp = webdriver.FirefoxProfile(None)
    set_ff_prefs(ffp, proxy_port, flash_support, cookie_support)
    tries = 0
    for tries in xrange(MAX_GET_DRIVER_TRIES):
        try:
            driver = webdriver.Firefox(firefox_profile=ffp,
                                       firefox_binary=ff_bin)
        except sel_exceptions.WebDriverException as wdexc:
            print "Error creating webdriver, will sleep (tried %s times) %s" %\
                (tries, wdexc)
            sleep(1)  # each call to webdriver constructor already takes 30 s
        else:
            if tries:
                print "Created the webdriver after sleeping %s sec" % (tries)
            break
        tries += 1
    else:
        raise sel_exceptions.WebDriverException("Cannot initialize webdriver")

    driver.set_page_load_timeout(cm.HARD_TIME_OUT - 5)
    driver.implicitly_wait(10)
    return driver, ffp.profile_dir, ff_bin.process


def visit_page(url_tuple, timeout=cm.HARD_TIME_OUT,
               wait_on_site=cm.WAIT_ON_SITE, pre_crawl_sleep=False,
               out_dir=cm.BASE_TMP_DIR, flash_support=cm.FLASH_ENABLE,
               cookie_support=cm.COOKIE_ALLOW_ALL):
    driver = None
    visit_info = cm.VisitInfo()
    try:
        visit_info.rank, visit_info.url = url_tuple
    except:
        # When rank of the page is not provided, we'll use rank=0
        visit_info.rank, visit_info.url = 0, url_tuple

    visit_info.sys_log = join(out_dir, "syscall-%s-%s.log" %
                              (visit_info.rank, ut.rand_str()))
    visit_info.http_log = join(out_dir, "http-%s-%s.log" %
                               (visit_info.rank, ut.rand_str()))
    visit_info.http_dump = join(out_dir, "mitm-%s-%s.dmp" %
                                (visit_info.rank, ut.rand_str()))
    visit_info.start_time = strftime("%Y%m%d-%H%M%S")
    visit_info.out_dir = out_dir
    visit_info.out_db = join(visit_info.out_dir, cm.DB_FILENAME)
    visit_info.err_log = join(out_dir, "error.log")
    visit_info.debug_log = join(out_dir, "debug.log")

    be = cm.BrowserEvent()
    be.event_type = cm.EVENT_NEW_VISIT

    visit_info.ff_log = open_log_file(out_dir, visit_info.url)

    if not visit_info.url[:5] in ('data:', 'http:', 'https', 'file:'):
        visit_info.url = 'http://' + visit_info.url

    try:
        visit_info.visit_id = dbu.insert_to_db(dbu.DBCmd.ADD_VISIT, be,
                                               visit_info)
        cm.print_debug(visit_info, "Visiting: %s %s (%s)" %
                       (visit_info.visit_id, visit_info.url, visit_info.rank))
        setup_nspr_logging(visit_info.http_log)
        visit_info.vdisplay = start_xvfb()
        port, visit_info.mitm_proc = start_mitm_capture(visit_info.http_dump)
        driver, visit_info.profile_dir, visit_info.sel_proc =\
            get_browser(visit_info.ff_log, port, flash_support, cookie_support)
        if flash_support:
            visit_info.strace_proc = log_syscalls(visit_info.sel_proc,
                                                  visit_info.sys_log)

        #############################################################
        driver_get(driver, visit_info, cm.SOFT_TIMEOUT)  # real visit
        #############################################################
        time.sleep(wait_on_site)
        close_driver(driver, timeout=10)
        stop_strace(visit_info.strace_proc)
        result_dict = process_crawler_output(visit_info.ff_log, visit_info,
                                             flash_support)
        cm.print_debug(visit_info, "Visit OK: %s %s (%s)" %
                       (visit_info.visit_id, visit_info.url, visit_info.rank))
        visit_info.incomplete = 0
        dbu.insert_to_db(dbu.DBCmd.UPDATE_VISIT, be, visit_info)
        quit_driver(driver)
        stop_xvfb(visit_info.vdisplay)
        remove_visit_files(visit_info)
    except (cm.TimeExceededError, sel_exceptions.TimeoutException) as texc:
        err_str = "Visit to %s(%s) timed out %s" % \
            (visit_info.url, visit_info.rank, texc)
        cm.print_error(visit_info, err_str)
        clean_up(visit_info, driver)
        return None
    except Exception as exc:
        err_str = "Exception visiting %s(%s) %s %s" % \
            (visit_info.url, visit_info.rank, exc, traceback.format_exc())
        cm.print_error(visit_info, err_str)
        clean_up(visit_info, driver)
        return None
    else:
        return result_dict


def driver_get(driver, visit_info, timeout=cm.SOFT_TIMEOUT):
    ut.timeout(cm.SOFT_TIMEOUT)
    t0 = time.time()
    #############################################################
    # The real visit happens here ###############################
    driver.get(visit_info.url)
    #############################################################
    #############################################################
    visit_info.duration = time.time() - t0
    ut.cancel_timeout()


def start_mitm_capture(http_dump):
    if not CAPTURE_HTTP_W_MITM_PROXY:
        return None, None
    return mitm.start_http_capture(http_dump, cm.HARD_TIME_OUT)


def quit_driver(driver):
    try:
        driver.quit()
    except httplib.CannotSendRequest:
        pass


def stop_strace(strace_proc):
    if strace_proc:
        strace_proc.terminate()


def stop_mitmdump(mitm_proc):
    # visit_info.mitm_proc.terminate()
    if mitm_proc:
        os.kill(mitm_proc.pid, signal.SIGTERM)


def close_driver(driver, timeout=10):
    ut.timeout(timeout)
    try:
        driver.close()
    except (sel_exceptions.UnexpectedAlertPresentException,
            cm.TimeExceededError):
        pass
    ut.cancel_timeout()


def setup_nspr_logging(http_log):
    if ENABLE_NSPR_LOGGING:
            os.environ['NSPR_LOG_MODULES'] = "timestamp,nsHttp:3"
            os.environ['NSPR_LOG_FILE'] = os.path.join(http_log)


def remove_visit_files(visit_info):
    rm(visit_info.ff_log)
    rm(visit_info.sys_log)
    tries = 0
    MAX_LOCK_CHECK = 30
    rm(visit_info.http_dump)
    if os.path.isdir(visit_info.profile_dir):
        # lock file means firefox is still running or didn't exit properly
        while os.path.isfile(join(visit_info.profile_dir, "lock")):
            time.sleep(1)
            tries += 1
            if tries > MAX_LOCK_CHECK:
                break
        if tries:
            cm.print_debug(visit_info,
                           "Waited %s sec for the lock to be removed" % tries)
        shutil.rmtree(visit_info.profile_dir, ignore_errors=True)


def clean_up(visit_info, driver):
    stop_xvfb(visit_info.vdisplay)
    remove_visit_files(visit_info)
    if visit_info.strace_proc:
        visit_info.strace_proc.terminate()
    # os.kill(visit_info.mitm_proc.pid, signal.SIGTERM)
    try:
        driver.quit()
    except:
        if visit_info.sel_proc:
            visit_info.sel_proc.terminate()
