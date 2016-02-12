# This is code adapted from Princeton crawler code written by
# Steve Englehardt and Chris Eubank

# This module is used to extractor persistent cookie IDs using
# the same heuristics from the PETS 2014 paper

from utils import census_utils
from collections import defaultdict
import sqlite3 as lite
from dateutil import parser
DB_TYPE_OPENWPM = 1
DB_TYPE_MOZ_COOKIES = 2
DB_TYPE_LEUVEN = 3


# builds a dictionary with keys = (domain, name) and values being list of
# cookie values  values must be from non short-lived cookies and consistent
# across the crawls extracts from a single OpenWPM database
def extract_cookie_candidates_from_db(db_name):
    con = lite.connect(db_name)
    cur = con.cursor()
    cookie_table, accessed_col, domain_col = get_cookie_table_name(cur)
    # first, add all cookie/value pairs for cookies that live at least one month
    raw_cookie_dict = defaultdict(list)  # maps (domain, names) to lists of values

    for domain, name, value, access, expiry in cur.execute('SELECT %s, name, value, %s, expiry FROM %s' % (domain_col, accessed_col, cookie_table)):
        domain = domain if len(domain) == 0 or domain[0] != "." else domain[1:]
        # prune away cookies with expiry times under a month
        try:
            if (parser.parse(expiry).replace(tzinfo=None) - parser.parse(access).replace(tzinfo=None)).days < 30:
                continue
        except:
            if (expiry * 1000000 - access) / (24 * 60 * 60 * 1000000) < 30:
                continue
        # add the basic values, then try to parse inner parameters and add them
        raw_cookie_dict[(domain, name)].append(value)
        add_inner_parameters(raw_cookie_dict, domain, name, value)

    # only keep cookies with values that remain constant throughout the crawl
    cookie_dict = {}
    for cookie in raw_cookie_dict:
        if census_utils.all_same(raw_cookie_dict[cookie]):
            cookie_dict[cookie] = raw_cookie_dict[cookie][0]

    con.close()
    return cookie_dict


# goes through the cookies values and looks for values of the form id=XXX&time=YYYY
# then appends to raw_cookie_dict the cookie (domain, name#id) XXX
# and (domain, name#time) YYY
# currently uses two known delimiters
def add_inner_parameters(raw_cookie_dict, domain, name, value):
    delimiters = [":", "&"]  # currently known inner cookie delimiters
    for delimiter in delimiters:
        parts = value.split(delimiter)
        for part in parts:
            params = part.split("=")
            if len(params) == 2:
                raw_cookie_dict[(domain, name + "#" + params[0])].append(params[1])


# takes in dictionaries of persistent, non-session cookies
# finds common ids that have values of the same length
# are not the same and have pairwise similarities < 0.9 (which covers all being equal)
# an ID must appear in at least 2 different crawls (otherwise, can't make a definitive statement about it)
# prunes away cookies with lengths less than or equal to 5 (these strings are probably too short
# returns dictionary with domains as keys and cookie names as values
def extract_common_persistent_ids(cookie_dicts):
    raw_id_dict = defaultdict(list)  # for each cookie, a list of the values across each crawl

    # combine all smaller cookie dictionaries into a larger dictionary
    for cookie_dict in cookie_dicts:
        for cookie in cookie_dict:
            raw_id_dict[cookie].append(cookie_dict[cookie])

    domain_dict = defaultdict(list)  # for each domain,list of candidate ID cookies

    # prune away cookies that fail one of our unique ID heuristics
    for cookie in raw_id_dict:
        if len(raw_id_dict[cookie]) <= 1 or len(raw_id_dict[cookie][0]) <= 5 or len(raw_id_dict[cookie][0]) > 100 \
                or not census_utils.all_same_len(raw_id_dict[cookie]) \
                or not census_utils.all_dissimilar(raw_id_dict[cookie]):
            continue

        domain_dict[cookie[0]].append(cookie[1])

    return domain_dict


# takes in three dictionaries of persistent, non-session cookies
# two from a repeat crawl with the same database and one from a fresh crawl
# with a fresh database. From this, ids are classified as follows:
# between two separate profiles
#   - values of the same length
#   - are not the same and have pairwise similarities < 0.9 (which covers all being equal)
#   - appears in both crawls (otherwise, can't make a definitive statement about it)
#   - length >= 5 and <= 100
# between two crawls with same profile:
#   - values are the same
# returns dictionary with domains as keys and cookie names as values
# INPUT must be of the form: [profile_1_pass_1, profile_1_pass_2, profile_2]
def extract_persistent_ids(cookie_dicts):
    raw_id_dict = defaultdict(list)  # for each cookie, a list of the values across each crawl

    # combine all smaller cookie dictionaries into a larger dictionary
    for cookie_dict in cookie_dicts:
        for cookie in cookie_dict:
            raw_id_dict[cookie].append(cookie_dict[cookie])

    domain_dict = defaultdict(list)  # for each domain,list of candidate ID cookies

    # prune away cookies that fail one of our unique ID heuristics
    for cookie in raw_id_dict:
        if len(raw_id_dict[cookie]) <= 2 or len(raw_id_dict[cookie][0]) <= 5 or len(raw_id_dict[cookie][0]) > 100 \
                or not raw_id_dict[cookie][0] == raw_id_dict[cookie][1] \
                or not census_utils.all_same_len(raw_id_dict[cookie][1:2]) \
                or not census_utils.all_dissimilar(raw_id_dict[cookie][1:2]):
            continue

        domain_dict[cookie[0]].append(cookie[1])

    return domain_dict


# given a dictionary of persistent ids, goes through a database
# and returns a dictionary with the persistent ids and their unique values
# in the database (for those that actually appear)
def extract_known_cookies_from_db(db_name, cookie_dict):
    con = lite.connect(db_name)
    cur = con.cursor()
    cookie_table, _, domain_col = get_cookie_table_name(cur)
    found_cookies = {}
    for domain, name, value in cur.execute('SELECT %s, name, value FROM %s' % (domain_col, cookie_table)):
        domain = domain if len(domain) == 0 or domain[0] != "." else domain[1:]

        # first search for most basic cookies
        if domain in cookie_dict and name in cookie_dict[domain]:
            found_cookies[(domain, name)] = value

            # next, look for potential nested cookies
            if "=" in value:
                for delimiter in ["&", ":"]:
                    parts = value.split(delimiter)
                    for part in parts:
                        params = part.split("=")
                        if len(params) == 2 and name + "#" + params[0] in cookie_dict[domain]:
                            found_cookies[(domain, name + "#" + params[0])] = params[1]
    con.close()
    return found_cookies


def get_cookie_table_name(cur):
    """Return the respective column names for different DBs we handle"""
    try:
        cur.execute('SELECT * FROM moz_cookies LIMIT 1')
        return "moz_cookies", "lastAccessed", "host"
    except:  # would be nice to check this too
        # cur.execute('SELECT * FROM cookies LIMIT 1')
        return "cookies", "accessed", "domain"


# Takes in a known cookie db and attaches the best guess at the
# "owner" of an ID by looking for first use. This is probably quite
# inefficient.
def extract_cookie_owner_from_db(db_name, known_cookies):
    con = lite.connect(db_name)
    cur = con.cursor()
    cookie_table, accessed_col, domain_col = get_cookie_table_name(cur)
    for cookie in known_cookies:
        value = known_cookies[cookie]
        cur.execute('SELECT %s FROM %s WHERE value LIKE ? ORDER BY %s LIMIT 1'
                    % (domain_col, cookie_table, accessed_col), ('%'+value+'%',))
        owner = cur.fetchone()[0]
        owner = owner if len(owner) == 0 or owner[0] != "." else owner[1:]
        known_cookies[cookie] = (value, owner)

    con.close()
    return known_cookies

if __name__ == "__main__":
    c1 = extract_cookie_candidates_from_db("crawl1.sqlite")
    c2 = extract_cookie_candidates_from_db("crawl2.sqlite")
    extracted = extract_persistent_ids([c1, c2])
    known = extract_known_cookies_from_db("crawl1.sqlite", extracted)
    known_owner = extract_cookie_owner_from_db("crawl1.sqlite", extracted)
