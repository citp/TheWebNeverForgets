import os
import subprocess
import socket
from time import sleep
from libmproxy import flow

MITM_LOG_EXTENSION = 'mlog'
MAX_FILENAME_LEN = 256

MITM_MAX_TRIES = 2
MAX_PORT_NO = 65535
MIN_PORT_NO = 1024
PORT_TRY_TIMEOUT = 2
REMOVE_DMP_FILES = True  # remove mitm dump files or not...


def get_free_port():
    """Get a free port number for mitmdump.

    http://stackoverflow.com/questions/1365265/on-localhost-how-to-pick-a-free-port-number?#answer-1365284

    """
    max_tries = 0
    while max_tries < MITM_MAX_TRIES:
        max_tries += 1
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('', 0))
            port = s.getsockname()[1]
        except Exception:
            sleep(1)
        else:
            return port
    return None


def start_http_capture(dump_file, timeout, logging=False):
    """Run mitmdump as a subprocess in the background with a timeout."""
    port = get_free_port()
    if not port:  # we cannot get a free port
        return None, None

    cmd_re_dir = ''  # for redirecting stderr to stdout and teeing
    quite_option = '-q'  # mitmdump option to be quiet - no log

    if logging:
        mitm_log_file = "%s.%s" % (dump_file, MITM_LOG_EXTENSION)
        cmd_re_dir = ' 2>&1 |tee %s' % mitm_log_file  # redirect to log file
        quite_option = ''  # we don't want be quite!

    cmd = 'timeout %s mitmdump %s -p %s -w %s %s' % (timeout,
                                                     quite_option,
                                                     port, dump_file,
                                                     cmd_re_dir)
    # better remove shell=True on the next line
    subp = subprocess.Popen("exec " + cmd, shell=True, preexec_fn=os.setsid)
    return port, subp


def parse_mitm_dump(dumpfile):
    http_dicts = []
    if os.path.isfile(dumpfile):
        fr = flow.FlowReader(open(dumpfile))
        try:
            for msg in fr.stream():
                http_dict = {}
                http_dict["req_content"] = ""
                http_dict["resp_headers"] = []
                http_dict["req_url"] = msg.request.url
                http_dict["referer"] = msg.request.headers['Referer'][0]\
                    if msg.request.headers['Referer'] else ""
                http_dict["method"] = msg.request.method
                http_dict["req_headers"] = msg.request.headers.lst
                if msg.request.content:
                    http_dict["req_content"] = msg.request.content

                if msg.response:
                    http_dict["resp_headers"] = msg.response.headers.lst
                    if hasattr(msg.response, "code"):
                        http_dict["resp_code"] = msg.response.code
                    elif hasattr(msg.response, "status_code"):
                        http_dict["resp_code"] = msg.response.code
                    else:  # this shouldn't happen
                        http_dict["resp_code"] = 0
                        print "HTTP response status code is missing"
                http_dicts.append(http_dict)
        except flow.FlowReadError as exc:
            print "Error reading mitm dump %s" % exc
    else:
        print "Cannot find mitm dump %s" % dumpfile
    return http_dicts
