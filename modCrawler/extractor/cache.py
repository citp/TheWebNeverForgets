import shutil
import os
from crawler.common import BASE_TMP_DIR
from utils.file_utils import append_timestamp, create_dir
import subprocess
from glob import glob
import base64
from datetime import datetime
from utils.gen_utils import hash_text, rand_str
import traceback
from werkzeug.http import parse_date, parse_cache_control_header
from werkzeug.datastructures import ResponseCacheControl

PERL_PATH = os.path.join("/usr", "bin", "perl")


########################################################
# "ff_cache_find_0.3.pl" by Ritchie was used to process Firefox cache
# http://articles.forensicfocus.com/2012/03/09/firefox-cache-format-and-extraction/
# Since then Firefox has moved to cache2, for which the support needs to be
# added perhaps using, https://github.com/JamesHabben/FirefoxCache2
########################################################
# CACHE_PERL_SCRIPT = os.path.join(BASE_ETC_DIR, "ff_cache_find_0.3.pl")
CACHE_PERL_SCRIPT = ""
########################################################

DELTA_MONTH = 2592000


def parse_metadata(str_meta):
    indented_str_meta = str_meta.replace("\t", "")
    if "security-info" in indented_str_meta:  # strip security info hash
        indented_str_meta = indented_str_meta.split("security-info")[0]
    key_value_pairs = [pair for pair in
                       [line.split(': ') for line in
                        indented_str_meta.splitlines()] if len(pair) == 2]
    return dict(key_value_pairs)


def get_ff_cache(profile_dir, store_body=False):
    cache_dir = os.path.join(profile_dir, "Cache")
    if not os.path.isdir(cache_dir):
        return []  # Firefox updated the cache dir structure since our study
    cache_map = os.path.join(cache_dir, "_CACHE_MAP_")
    cache_dump = os.path.join(BASE_TMP_DIR, append_timestamp("cache") +
                              rand_str())
    create_dir(cache_dump)
    subprocess.call([PERL_PATH, CACHE_PERL_SCRIPT, cache_map, "--recover=" +
                     cache_dump])
    cache_items = []
    db_items = ("Etag", "Request String", "Expires", "Cache-Control")
    for fname in glob(os.path.join(cache_dump, "*_metadata")):
        item = {}
        try:
            with open(fname) as f:
                metadata = f.read()
                item = parse_metadata(metadata)
                for db_item in db_items:
                    if db_item not in item:
                        item[db_item] = ""

                # If a response includes both an Expires header and a max-age
                # directive, the max-age directive overrides the Expires header
                # (http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html)
                expiry_delta_sec = 0
                if "Expires" in item:
                    # parse expiry date
                    expiry = parse_date(item["Expires"])
                    if expiry:
                        expiry_delta = expiry - datetime.now()
                        expiry_delta_sec = expiry_delta.total_seconds()
                if "Cache-Control:" in item:
                    # parse max-age directive
                    cache_directives =\
                        parse_cache_control_header(item["Cache-Control"],
                                                   cls=ResponseCacheControl)
                    if "max-age" in cache_directives:
                        expiry_delta_sec = cache_directives["max-age"]
                if expiry_delta_sec < DELTA_MONTH:
                    continue
                item["Expiry-Delta"] = expiry_delta_sec

            with open(fname[:-9]) as f:
                data = f.read()
                item["Body"] = data if store_body else ""  # store as BLOB
                item["Hash"] = hash_text(base64.b64encode(data))
        except IOError as exc:
            print "Error processing cache: %s: %s" % (exc,
                                                      traceback.format_exc())

        cache_items.append(item)
    if os.path.isdir(cache_dump):
        shutil.rmtree(cache_dump)
    return cache_items


if __name__ == '__main__':
    pass
