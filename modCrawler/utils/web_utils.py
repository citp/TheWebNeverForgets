import os.path as ospath
from urllib2 import urlopen
import crawler.common as cm


def read_url(uri):
    """Fetch and return a URI content."""
    w = urlopen(uri)
    return w.read()


def gen_url_list(stop, start=1, get_rank=False, filename="", sep=','):
    """Yield URLs for a given rank range from a given file (or default Alexa list).

    start and stop is inclusive and 1-based indexes.
    """
    if not filename:
        filename = cm.ALEXA_TOP_1M

    if not ospath.isfile(filename):
        print('Cannot find URL list (Top Alexa CSV etc.) file!')
        return

    for line in open(filename).readlines()[start-1:stop]:
        if sep in line:
            # we expect a comma between rank and URL a la Alexa format
            rank, site_url = line.split(sep, 1)
            site_url = site_url.rstrip()
            if get_rank:  # if caller asked for rank
                yield int(rank), site_url
            else:
                yield site_url
        else:
            if get_rank:
                yield 0, line.rstrip()  # yield 0 if we couldn't find the rank
            else:
                yield line.rstrip()  # no comma
