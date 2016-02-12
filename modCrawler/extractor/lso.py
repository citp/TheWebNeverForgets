import utils.file_utils as fu
import os
from pyamf import sol
import crawler.common as cm
from sets import Set

COMMON_LSO_DIRS =\
    ("~/.macromedia/Flash_Player/macromedia.com/support/flashplayer/sys",
     "~/.mozilla/firefox/",
     "~/.macromedia/Flash_Player/#SharedObjects/",
     "~/.config/google-chrome/Default/Pepper Data/Shockwave Flash/WritableRoot"
     "/#SharedObjects/"
     )

COMMON_FF_LSO_DIRS = ("~/.macromedia/Flash_Player/macromedia.com/support/"
                      "flashplayer/sys",
                      "~/.mozilla/firefox/",
                      "~/.macromedia/Flash_Player/#SharedObjects/")


def parse_strace_logs(visit_info, test_lso=None):
    events = []
    lines_seen = Set()
    # cm.print_log(visit_info, visit_info.sys_log, cm.LOG_DEBUG)
    for line in fu.gen_cat_file(visit_info.sys_log):
        if (".macromedia/Flash_Player/#SharedObjects" not in line or
                (line in lines_seen)):
            continue

        lines_seen.add(line)
        try:
            pieces = line.split("#SharedObjects/")[1].split("/")
            lso_file, mode_str = pieces[-1].split("\"")
            if "O_RDWR" in mode_str:
                mode = cm.ACCESS_MODE_READ_WRITE
            else:
                mode = cm.ACCESS_MODE_READ_ONLY
            domain = pieces[1]
            filename = line.split("\"")[1]
            file_ext = filename.rsplit(".", 1)[-1]
            # We observe .sxx extension for LSOs instead of .sol in strace logs
            # We recover the real filename by replacing
            # [pid 26407] open("/home/xyz/.macromedia/Flash_Player/#SharedObjects/GWZSHMBL/securehomes.esat.kuleuven.be/FlashCookie.sxx", O_RDWR|O_CREAT|O_APPEND, 0666) = 18  # noqa
            # [pid 26407] write(18, "\0\277\0\0\0-TCSO\0\4\0\0\0\0\0\vFlashCookie\0\0\0\3\21test_key\6\rjb0uf9\0", 51) = 51  # noqa
            # the only file in SharedObjects/GWZSHMBL/securehomes.esat.kuleuven.be would be a .sol file, which is not in the strace logs if it's created on this visit.  # noqa
            if file_ext == "sxx":
                filename = filename.replace(".sxx", ".sol")
            if test_lso is not None:  # just to simplify tests
                filename = test_lso  # override the lso filename
            if not filename.endswith(".sol"):
                print "Unexpected LSO file extension", filename, file_ext, line
                continue
            if not os.path.isfile(filename):
                # Happens when the (temp) LSO is removed before the visit ends.
                print "Cannot find LSO file", filename, file_ext, line
                continue
        except ValueError:
            continue
        # TODO: move below code to a separate function
        try:
            lso_dict = sol.load(filename)
            for k, v in lso_dict.iteritems():
                be = cm.BrowserEvent()
                be.event_type = cm.EVENT_FLASH_LSO
                be.js_file = lso_file
                be.initiator = domain
                be.mode = mode  # this doesn't seem to work
                be.cookie_path = filename.split("#SharedObjects/")[1]
                be.key = unicode(k)
                try:
                    be.log_text = unicode(v)
                except UnicodeDecodeError:  # obj is byte string
                    ascii_text = str(v).encode('string_escape')
                    be.log_text = unicode(ascii_text)
                events.append(be)
        except Exception as exc:
            cm.print_log(visit_info, "Error parsing LSO %s %s" %
                         (filename, exc))
    return events


def gen_flash_cookies(lso_dirs=COMMON_LSO_DIRS, mod_since=0):
    """Return a generator of Flash cookies (Local Shared Objects)."""
    for top_dir in lso_dirs:
        top_dir = os.path.expanduser(top_dir)
        for lso_file in fu.gen_find_files("*.sol", top_dir):
            mtime = os.path.getmtime(lso_file)
            if mtime > mod_since:
                try:
                    lso_content = sol.load(lso_file)
                    # lso_content is a dict that need to be parsed
                except:
                    print "Exception reading", lso_file
                else:
                    yield lso_content, lso_file


def list_flash_cookies(lso_dirs=COMMON_LSO_DIRS):
    lso_count = 0
    for lso_content, lso_file in gen_flash_cookies(lso_dirs):
        lso_count += 1
        print lso_count, lso_content, lso_file

if __name__ == '__main__':
    list_flash_cookies()
