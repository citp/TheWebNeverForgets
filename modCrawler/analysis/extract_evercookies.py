import utils.db_utils as dbu
import analysis.extract_cookie_ids as eci
import crawler.common as cm
import base64
import re
from sets import Set
from collections import defaultdict
import os
import itertools

j = os.path.join


def has_json(s):
    return re.findall("\{\'[^']*\'\s?:.+\}", s)


def split_json(js):
    if has_json(js):
        return re.split("[' :{}]", js)
    else:
        return [""]


def decode_if_b64(s):
    try:
        return base64.decodestring(s)
    except:
        return s


def split_lso(lso):
    return filter(lambda x: len(x) > 5, re.split("[{}\n\t '`*.,\"=:&;-]\|", lso))


def split_lsos(lsos):
    return Set(itertools.chain(*[split_lso(lso_db1) for lso_db1 in lsos]))


def extract_persistent_ids_from_dbs(db1, db2, db3):
    c1 = eci.extract_cookie_candidates_from_db(db1)
    c2 = eci.extract_cookie_candidates_from_db(db2)
    c3 = eci.extract_cookie_candidates_from_db(db3)
    return eci.extract_persistent_ids([c1, c2, c3])


def get_evercookies_by_cookies(db1, db2, db3, prof_dir):
    """Try cookie ID heuristic to find ID candidates, then search for LSOs."""
    persistent_ids = extract_persistent_ids_from_dbs(db1, db2, db3)
    print len(persistent_ids), "db1, db2"
    known = eci.extract_known_cookies_from_db(db2, persistent_ids)
    for k, v in known.iteritems():
        print k, v

    persistent_ids = extract_persistent_ids_from_dbs(db1, prof_dir, db3)
    respawned = eci.extract_known_cookies_from_db(prof_dir, persistent_ids)
    for k, v in respawned.iteritems():
        print k, v


def get_flash_cookies_from_dbs(dbs):
    lso_sets = []
    for db in dbs:
        lso_sets.append(split_lsos(get_distinct_items(db, ("content",
                                                           "flash_cookies"))))
    return reduce(lambda x, y: x | y, lso_sets)


def get_flash_evercookies(db1, db2, other_prof_dbs, seed_prof):
    seed_prof_cookie_db = j(seed_prof, "cookies.sqlite")
    lsos_by_visit = defaultdict(list)

    lsos_db1 = split_lsos(get_distinct_items(db1,
                                             ("content", "flash_cookies")))
    lsos_db2 = split_lsos(get_distinct_items(db2,
                                             ("content", "flash_cookies")))
    lsos_db3 = get_flash_cookies_from_dbs(other_prof_dbs)

    # lsos_db3 = get_distinct_items(db3, ("content", "flash_cookies"))

    print len(lsos_db2), "lsos in db 2", len(lsos_db3), "lsos in db 3"
    print len(lsos_db1 & lsos_db2), "common lsos in db 1 & 2"

    for lso_item in dbu.get_db_entry(db1, dbu.DBCmd.GET_FLASH_COOKIES, None):
        content = lso_item[7]
        v_id = lso_item[1]
        lso_id = lso_item[0]
        splitted = split_lso(content)
        for item in splitted:
            if (item and len(item) > 5 and item in lsos_db2 and
                    item not in lsos_db3):
                if "es|utmccn" in content:
                    print "*******", content, lso_id, splitted
                lsos_by_visit[(v_id, lso_id)].append({"item": item,
                                                      "path": lso_item[5],
                                                      "content": content,
                                                      "key": lso_item[6],
                                                      "domain": lso_item[3]})

    print len(lsos_by_visit), "lsos in db 1"
    return grep_in_visit_and_profile_data(seed_prof_cookie_db, (db1, db2),
                                          lsos_by_visit, dbu.DBTable.LSO,
                                          other_prof_dbs)


def get_html_from_moz_cookies(rows):
    # TODO: mix of presentation and logic. Instead send a list
    # and generate the markup in gen_report.
    return "<ul>%s</ul>" % ("\n".join(["<li><i>%s</i> %s: %s</li>" %
                                       (row[6], row[4], row[5])
                                       for row in rows]))


def get_html_from_visit_cookies(rows):
    # TODO: mix of presentation and logic. Instead send a list
    # and generate the markup in gen_report.
    return "<ul>%s</ul>" % ("\n".join(["<li><b>%s</b> <i>%s</i> %s: %s</li>" %
                                       (row[2], row[6], row[4], row[5])
                                       for row in rows]))


def grep_in_visit_and_profile_data(seed_cookie_db, visit_dbs, lsos_by_visit,
                                   exclude_table, other_prof_dbs):
    looked_items = Set()
    for (v_id, _), lso_dicts in lsos_by_visit.iteritems():
        for lso_dict in lso_dicts:
            match = lso_dict["item"]
            if match in looked_items:
                continue

            looked_items.add(match)
            # find the cookies in the original seeded profile that match the common LSO IDs.
            cookies = dbu.get_db_entry(seed_cookie_db, dbu.DBCmd.GREP_IN_PROFILE_DATA,
                                       (match, v_id, exclude_table))
            # since the cookies are removed from the profile before seeding,
            # the cookies in found in the subsequent visits must have been
            # respawned. By "seeding" we mean copying the LSOs from a profile
            # to another computer to allow sites to exploit LSOs but nothing
            # else (e.g. cookies). See Section 4 of the paper for a detailed
            # explanation of the method.
            # https://securehomes.esat.kuleuven.be/~gacar/persistent/the_web_never_forgets.pdf
            if len(cookies["cookie"]):
                vis1_cookies = dbu.get_db_entry(visit_dbs[0],
                                                dbu.DBCmd.GREP_IN_VISIT_COOKIES,
                                                match)
                vis2_cookies = dbu.get_db_entry(visit_dbs[1],
                                                dbu.DBCmd.GREP_IN_VISIT_COOKIES,
                                                match)
                if len(vis1_cookies) and len(vis2_cookies):
                    # the cookie should not be found in visit data from an
                    # unrelated profile.
                    other_vis_cookies = dbu.get_db_entry(other_prof_dbs[0],
                                                         dbu.DBCmd.GREP_IN_VISIT_COOKIES,
                                                         match)
                    if not len(other_vis_cookies):
                        prof_cookies_ul =\
                            get_html_from_moz_cookies(cookies["cookie"])
                        visit1_cookies_ul =\
                            get_html_from_visit_cookies(vis1_cookies)
                        visit2_cookies_ul =\
                            get_html_from_visit_cookies(vis2_cookies)
                        yield match, lso_dict["key"], lso_dict["content"],\
                            lso_dict["domain"], lso_dict["path"],\
                            prof_cookies_ul, visit1_cookies_ul,\
                            visit2_cookies_ul
                    else:
                        print "Found in other db", match


def get_distinct_items(db, item_type):
    return Set([item[0] for item in dbu.get_db_entry(db,
                dbu.DBCmd.GET_DISTINCT_FROM_DB, item_type)])


if __name__ == '__main__':
    prof1_db2 = j(cm.BASE_DATA_DIR,
                  "crawl1.sqlite")
    prof1_db1 = j(cm.BASE_DATA_DIR,
                  "crawl2.sqlite")
    # data from crawls with unrelated profiles, to remove non-ID strings
    other_prof_dbs = (j(cm.BASE_DATA_DIR,
                        "crawl_unrelated.sqlite"),
                      j(cm.BASE_DATA_DIR, "crawl_unrelated2.sqlite"))

    seed_prof = j(cm.BASE_DATA_DIR,
                  "full_profile")
    for l in get_flash_evercookies(prof1_db1, prof1_db2,
                                   other_prof_dbs, seed_prof):
        print l
