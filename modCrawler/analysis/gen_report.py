import os
# import json
from tld import get_tld
from Cheetah.Template import Template
import crawler.common as cm
import utils.db_utils as dbu
import utils.census_utils as cu
import analysis.canvas as ca
import utils.file_utils as fu
import analysis.extract_evercookies as ev
from analysis.report_template import template_str

j = os.path.join


def get_xsite_flash_cookies(db_file):
    ec_candidates = dbu.get_db_entry(db_file,
                                     dbu.DBCmd.GET_XSITE_FLASH_COOKIES, False)
    for ec_candidate in ec_candidates:
        print list(ec_candidate)
    return ec_candidates


def get_xsite_local_storage(db_file):
    ls_candidates = dbu.get_db_entry(db_file,
                                     dbu.DBCmd.GET_XSITE_LOCALSTORAGE, False)
#    for ls_candidate in ls_candidates:
#        print list(ls_candidates)
    return ls_candidates


def count_inclusion(db_file, domain):
    # % of sites that include a domain
    includers = set()
    db_rows = dbu.get_db_entry(db_file,
                               dbu.DBCmd.GREP_IN_REQ_URLS, domain)
    for db_row in db_rows:
        rank = db_row[9]
        if rank not in includers:
            if get_tld(db_row[3]) == domain:
                includers.add(rank)  # rank
                # print rank, db_row[3]
    print len(includers), "includes", domain
    return includers


def gen_crawl_report(db_file, db_pass2=None, db_other_profs=None,
                     prof_dir=None):
    """ visits_cnt, cookies, localstorage, flash cookies, cache, indexeddb,
    http reqs/resps
    canvas: list distinct FPers, linked to the sites that include this FPer
    evercookie: list potential evercookies by searching ID-like common strings
    among different vectors"""
    out_dir = os.path.dirname(db_file)
    crawl_name = os.path.basename(os.path.dirname(db_file))
    figs = []  # figures to be plotted, removed for now.
    respawned = []

    if db_pass2 and db_other_profs and prof_dir:
        respawned = ev.get_flash_evercookies(db_file, db_pass2,
                                             db_other_profs, prof_dir)

    start, end = dbu.get_db_entry(db_file, dbu.DBCmd.GET_VISIT_DATES, False)
    visits_cnt = dbu.get_db_entry(db_file, dbu.DBCmd.COUNT_VISITS, False)[0]
    completed_visits_cnt = dbu.get_db_entry(db_file,
                                            dbu.DBCmd.COUNT_VISITS, True)[0]
    cookies = dbu.get_db_entry(db_file, dbu.DBCmd.COUNT_COOKIES, 0)
    localstorage = dbu.get_db_entry(db_file, dbu.DBCmd.COUNT_LOCALSTORAGE, 0)
    print "genreport len(localstorage)", len(localstorage)
    xsite_flash_cookies = get_xsite_flash_cookies(db_file)
    xsite_local_storage = get_xsite_local_storage(db_file)

    try:
        flash_cookie_count = dbu.get_db_entry(db_file, dbu.DBCmd.COUNT_LSO, 0)
    except:
        flash_cookie_count = [""]

    canvas_meta_rows = dbu.get_db_entry(db_file, dbu.DBCmd.GET_CANVAS_META, 0)
    canvas_scr_domains = {}
    canvas_events_per_script = {}
    canvas_url_counts = {}
    canvas_domain_counts = {}
    canvas_script_urls = dbu.get_db_entry(db_file,
                                          dbu.DBCmd.GET_CANVAS_SCRIPTS, 0)
    false_positives = []
    for canvas_script_url_tup in canvas_script_urls:
        canvas_script_url = canvas_script_url_tup[0]
        canvas_events = dbu.get_db_entry(db_file,
                                         dbu.DBCmd.GET_CANVAS_EVENTS_BY_SCRIPT,
                                         canvas_script_url)
        if not ca.is_canvas_false_positive(canvas_events):
            scr_evs = dbu.get_db_entry(db_file,
                                       dbu.DBCmd.GET_CANVAS_EVENTS_BY_SCRIPT,
                                       canvas_script_url)
            canvas_events_per_script[canvas_script_url] = scr_evs
            url_cnts = dbu.get_db_entry(db_file,
                                        dbu.DBCmd.COUNT_SITES_BY_CANVAS_SCRIPT,
                                        canvas_script_url)
            canvas_url_counts[canvas_script_url] = url_cnts
            domain = cu.extract_domain(canvas_script_url)
            if domain in canvas_scr_domains:
                canvas_scr_domains[domain].append(canvas_script_url)
            else:
                canvas_scr_domains[domain] = [canvas_script_url]
        else:
            false_positives.append(canvas_script_url_tup)
            # print canvas_script_url_tup

    # Remove false positives
    for false_positive in false_positives:
        canvas_script_urls.remove(false_positive)
    # total_canvas_fp_count = sum()
    all_canvasfp_ranks = {}
    all_canvasfp_ranks_urls = {}
    for canvas_scr_domain, canvas_scr_urls in canvas_scr_domains.iteritems():
        script_ranks_and_urls =\
            dbu.get_db_entry(db_file,
                             dbu.DBCmd.GET_RANK_AND_URLS_BY_CANVAS_SCRIPTS,
                             canvas_scr_urls)
        canvas_domain_counts[canvas_scr_domain] = len(script_ranks_and_urls)
        all_canvasfp_ranks[canvas_scr_domain] = map(lambda x: x[0],
                                                    script_ranks_and_urls)
        all_canvasfp_ranks_urls[canvas_scr_domain] = script_ranks_and_urls

    # print all_canvasfp_ranks
    # fu.write_to_file(j(out_dir, "%s-canvas.json" % crawl_name),
    #                 json.dumps(all_canvasfp_ranks))

    total_canvas_fp_count = sum(canvas_domain_counts.itervalues())

    # print "Total canvas FP count", total_canvas_fp_count
    rank_set = set()
    for _, v in all_canvasfp_ranks.iteritems():
        for rank in v:
            rank_set.add(rank)

    # print "Total canvas FP count - uniq", len(rank_set)

    nameSpace = {'title': "Crawl Report",
                 'visits_cnt': visits_cnt,
                 'completed_visits_cnt': completed_visits_cnt,
                 'cookies': cookies[0],
                 'localstorage': localstorage[0],
                 'flash_cookie_count': flash_cookie_count[0],
                 'canvas_meta_rows': canvas_meta_rows,
                 'start': start,
                 'end': end,
                 'canvas_domain_counts': canvas_domain_counts,
                 'canvas_url_counts': canvas_url_counts,
                 'canvas_events_per_script': canvas_events_per_script,
                 'canvas_scr_domains': canvas_scr_domains,
                 'total_canvas_fp_count': total_canvas_fp_count,
                 'canvas_script_urls': canvas_script_urls,
                 'get_tld': cu.extract_domain,
                 'xsite_flash_cookies': xsite_flash_cookies,
                 'xsite_local_storages': xsite_local_storage,
                 'respawned': respawned,
                 'figs': figs,
                 'canvasfp_ranks_urls': all_canvasfp_ranks_urls,
                 # '3rdp_cookies': 3rdp_cookies,
                 }
    report_template = Template(template_str, searchList=[nameSpace])
    fu.write_to_file(j(out_dir, "%s-report.html" % crawl_name),
                     str(report_template))


if __name__ == '__main__':
    prof1_db1 = j(cm.BASE_DATA_DIR, "crawl1.sqlite")
    prof1_db2 = j(cm.BASE_DATA_DIR, "crawl2.sqlite")
    # data from crawls with unrelated profiles, to remove non-ID strings
    other_prof_dbs = (j(cm.BASE_DATA_DIR, "crawl_unrelated.sqlite"),
                      j(cm.BASE_DATA_DIR, "crawl_unrelated2.sqlite"))
    seed_prof = j(cm.BASE_DATA_DIR, "full_profile")
    # To detect evercookies you need other profile data
    # gen_crawl_report(prof1_db1, prof1_db2, other_prof_dbs, seed_prof)
    gen_crawl_report(cm.BASE_JOBS_DIR + "/latest/crawl.sqlite")

