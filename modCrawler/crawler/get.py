import os
import sys
dirname = os.path.dirname
sys.path.insert(0, dirname(dirname(os.path.realpath(__file__))))

import crawler.ffmod as ffm
import crawler.common as cm

if __name__ == '__main__':

    args = sys.argv[1:]
    rank = 0
    url = ""
    out_dir = "/dev/null"
    flash_support = cm.FLASH_ENABLE
    cookie_support = cm.COOKIE_ALLOW_ALL
    if not args:
        print 'usage: --urls urls --stop stop_pos [--start start_pos]\
             --max_proc max_parallel_processes --flash flash_support'
        sys.exit(1)

    if args and args[0] == '--url':
        url = args[1]
        del args[0:2]

    if args and args[0] == '--rank':
        rank = int(args[1])
        del args[0:2]

    if args and args[0] == '--out_dir':
        out_dir = args[1]
        del args[0:2]

    if args and args[0] == '--flash':
        flash_support = int(args[1])
        del args[0:2]

    if args and args[0] == '--cookie':
        cookie_support = int(args[1])
        del args[0:2]

    ffm.visit_page((rank, url), timeout=None, pre_crawl_sleep=True,
                   out_dir=out_dir, flash_support=flash_support,
                   cookie_support=cookie_support)
