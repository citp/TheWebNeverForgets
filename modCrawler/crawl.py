import os
import sys
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import pipes
import crawler.common as cm
import utils.ssh_utils as ssh
import utils.web_utils as wu
import utils.db_utils as dbu
from os.path import join, isfile, isdir, expanduser
from os import mkdir, unlink, environ

import crawler.parallelize as parallelize
import shutil
from functools import partial
import utils.file_utils as fu
from time import strftime, sleep
import utils.gen_utils as ut
import psutil
from random import random
from glob import glob
import analysis.gen_report as gr
import commands


def ensure_run_folder():
    for _dir in (cm.BASE_JOBS_DIR, cm.BASE_TMP_DIR):
        if not isdir(_dir):
            mkdir(_dir)


def create_job_folder(suffix):
    """Prepare output folder."""
    ensure_run_folder()
    crawl_name = "%s%s" % (strftime("%Y%m%d-%H%M%S"), suffix)
    output_dir = join(cm.BASE_JOBS_DIR, crawl_name)
    mkdir(output_dir)
    fu.add_symlink(join(cm.BASE_JOBS_DIR, 'latest'), output_dir)
    return output_dir, crawl_name


def run_cmd(url_tuple, out_dir, timeout=cm.HARD_TIME_OUT,
            flash_support=cm.FLASH_ENABLE, cookie_support=cm.COOKIE_ALLOW_ALL):
    if isfile(cm.STOP_CRAWL_FILE):
        print "Stop crawl file exists, won't run"
        return
    cpu_util = psutil.cpu_percent()
    if cpu_util > cm.MIN_CPU_UTIL_FOR_SLEEP:
        sleep_dur = (cm.MAX_PRE_CRAWL_SLEEP * cpu_util * random()) / 100
        print "CPU util is %s, will sleep: %s on before visiting %s" %\
            (cpu_util, sleep_dur, url_tuple)
        sleep(sleep_dur)
    debug_log = join(out_dir, "debug.log")
    cmd = "timeout -k %d %d python crawler/get.py --url %s"\
        " --rank %d  --out_dir %s --flash %d  --cookie %s 2>&1 >> %s" %\
        (cm.KILL_TIME_OUT, timeout, pipes.quote(url_tuple[1]),
         int(url_tuple[0]), pipes.quote(out_dir), int(flash_support),
         int(cookie_support), pipes.quote(debug_log))

    print "Will run:", cmd
    # print "status, output:", ut.run_cmd(cmd)
    ut.run_cmd(cmd)


def copy_mitm_certs():
    """Overwrite mitmproxy certs with the ones installed in our FF profile.

    This function is not used anymore since Webdriver started to accept
    certificates from any CA by default. If you want the browser to
    only accept certs from browser-trusted CAs, you need to add mitmproxy
    as a trusted CA in Firefox's profile.
    """
    for filename in glob(join(cm.MITM_PROXY_SRC_CERT_DIR, '*.*')):
        shutil.copy(filename, cm.MITM_PROXY_DST_CERT_DIR)


def pack_data(crawl_dir):
    if not os.path.isdir(crawl_dir):
        print "Cannot find the crawl dir: %s" % crawl_dir
        return False
    if crawl_dir.endswith(os.path.sep):
        crawl_dir = crawl_dir[:-1]

    crawl_name = os.path.basename(crawl_dir)
    containing_dir = os.path.dirname(crawl_dir)
    os.chdir(containing_dir)
    arc_path = "%s.tar.gz" % crawl_name
    tar_cmd = "tar czvf %s %s" % (arc_path, crawl_name)
    print "Packing the crawl dir with cmd: %s" % tar_cmd
    status, txt = commands.getstatusoutput(tar_cmd)
    if status:
        print "Tar cmd failed: %s \nSt: %s txt: %s" % (tar_cmd, status, txt)
        return False
    else:
        # http://stackoverflow.com/a/2001749/3104416
        tar_gz_check_cmd = "gunzip -c %s | tar t > /dev/null" % arc_path
        tar_status, tar_txt = commands.getstatusoutput(tar_gz_check_cmd)
        if tar_status:
            print "Tar check failed: %s tar_status: %s tar_txt: %s" %\
                (tar_gz_check_cmd, tar_status, tar_txt)
            return False
        else:
            return arc_path


def clean_tmp_files(crawl_dir):
    visit_file_patterns = ("*.dmp", "syscall*.log", "ff-*.log")
    visit_dir_patterns = ("/tmp/tmp*", "/tmp/plugtmp*")
    for vfp in visit_file_patterns:
        for vf in glob("%s/%s" % (crawl_dir, vfp)):
            print "Removing %s" % vf
            try:
                os.remove(vf)
            except:
                print "Exception removing %s" % vf

    for vdp in visit_dir_patterns:
        for td in glob(vdp):
            print "Removing %s" % td
            try:
                shutil.rmtree(td)
            except:
                print "Exception removing %s" % td


def read_machine_id():
    """Return the machine_id. This ID is then used to name the crawl data."""
    machine_id_file = expanduser("~/.machine_id")
    try:
        with open(machine_id_file, "r") as fid:
            return fid.read().strip()
    except:
        return "Unk"


# def crawl(urls, max_parallel_procs=cm.NUM_PARALLEL_PROCS,
#           flash_support=cm.FLASH_ENABLE, cookie_pref=cm.COOKIE_ALLOW_ALL,
#           upload_data=1):
def crawl(crawl_info):
    # modified get function with specific browser
    if isfile(crawl_info.urls):
        url_tuples = wu.gen_url_list(crawl_info.max_rank,
                                     crawl_info.min_rank, True,
                                     crawl_info.urls)
    else:
        url_tuples = [(0, crawl_info.urls), ]  # a single url has been passed

    machine_id = read_machine_id()
    suffix = "_%s_FL%s_CO%s_%s_%s" % (machine_id, crawl_info.flash_support,
                                      crawl_info.cookie_support,
                                      crawl_info.min_rank,
                                      crawl_info.max_rank)
    out_dir, crawl_name = create_job_folder(suffix)
    # copy_mitm_certs()
    db_file = join(out_dir, cm.DB_FILENAME)

    report_file = join(out_dir, "%s.html" % crawl_name)
    print "Crawl name:", crawl_name
    dbu.create_db_from_schema(db_file)
    custom_get = partial(run_cmd, out_dir=out_dir,
                         flash_support=crawl_info.flash_support,
                         cookie_support=crawl_info.cookie_support)
    parallelize.run_in_parallel(url_tuples, custom_get,
                                crawl_info.max_parallel_procs)
    gr.gen_crawl_report(db_file, report_file)
    # clean_tmp_files(out_dir)
    zipped = pack_data(out_dir)
    if crawl_info.upload_data:
        ssh.scp_put_to_server(zipped)
        ssh.scp_put_to_server(report_file)


def reset_stop_crawl():
    if isfile(cm.STOP_CRAWL_FILE):
        print "Removing stop crawl file"
        unlink(cm.STOP_CRAWL_FILE)

if __name__ == '__main__':
    crawl_info = cm.CrawlInfo()
#     crawl_info.
#     min_rank = 1
#     max_rank = 0
#     upload_data = 0
#     max_parallel_procs = cm.NUM_PARALLEL_PROCS
#     flash_support = cm.FLASH_ENABLE  # enable Flash
#     cookie_support = cm.COOKIE_ALLOW_ALL  # enable 1st and 3rd party cookies
#     urls = ''
    environ["DISPLAY"] = ":0.0"
    args = sys.argv[1:]
    # Remove residual crawl reset files
    reset_stop_crawl()

    if not args:
        print """usage: --urls urls --max_rank max_rank [--min_rank min_rank]
         --max_proc max_parallel_processes [--flash 0 | 1]
         [--cookie | 1 | 2 | 3]"""
        sys.exit(1)

    if args and args[0] == '--urls':
        crawl_info.urls = args[1]
        del args[0:2]

    if args and args[0] == '--max_rank':
        crawl_info.max_rank = int(args[1])
        del args[0:2]

    if args and args[0] == '--min_rank':
        crawl_info.min_rank = int(args[1])
        del args[0:2]

    if args and args[0] == '--max_proc':
        crawl_info.max_parallel_procs = int(args[1])
        del args[0:2]

    if args and args[0] == '--flash':
        crawl_info.flash_support = int(args[1])
        del args[0:2]

    if args and args[0] == '--cookie':
        crawl_info.cookie_support = int(args[1])
        del args[0:2]

    # add server and ssh key info in common.py if you want to upload crawl data
    if args and args[0] == '--upload':
        crawl_info.upload_data = bool(int(args[1]))
        del args[0:2]
    # TODO: process all urls if no max_rank is provided
    if not crawl_info.max_rank:
        print 'Cannot get the argument for max_rank %s' % (crawl_info.max_rank)
        sys.exit(1)

    if args:
        print 'Some arguments not processed, check your command: %s' % (args)
        sys.exit(1)

    crawl(crawl_info)
