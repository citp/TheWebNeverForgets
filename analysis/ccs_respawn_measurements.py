#This is a script for measuring the level of cookie respawning
import extract_cookie_ids as ecid
import sqlite3 as lite
import os

# DATA_DIR - the directory that contains all downloaded datafiles
DATA_DIR = os.path.expanduser('~/Desktop/')

# FLASH RESPAWN SCRIPT
# checks for matched flash content
# seed_base - the database that the original flash content comes from
# seed_recrawl - the recrawl db that the original flash content comes from
# unrelated_base - fresh db from an unrelated machine to remove common ids
# test_respawn - the database that loaded flash from seed_base
# flash_dbs = [seed_base, seed_recrawl, unrelated_base, test_respawn]
def check_for_respawned_flash(flash_dbs):
    set_list = []

    # First, find the HTTP cookies in the seed that are potential IDs
    cookies_db0 = ecid.extract_persistent_ids_from_dbs([flash_dbs[0]])
    cookies_db1 = ecid.extract_persistent_ids_from_dbs([flash_dbs[1]])
    cookies_db2 = ecid.extract_persistent_ids_from_dbs([flash_dbs[2]])
    id_cookies = ecid.extract_common_id_cookies([cookies_db0, cookies_db1, cookies_db2])
    HTTP_base_IDs = ecid.extract_known_cookies_from_db(flash_dbs[0], id_cookies)
  
    # builds up the list of sets of flash content
    for flash_db in flash_dbs:
        content_set = set()
        conn = lite.connect(flash_db)
        cur = conn.cursor()
        for url, domain, content in cur.execute('SELECT page_url, domain, content FROM flash_cookies'):
            content_set.add((url, domain, content))
        set_list.append(content_set)

    seed_set = set_list[0]
    unrel_set = set_list[2]
    resp_set = set_list[3]
    
    # the intersection of values (potentially respawned) from seed_base and test_respawn
    full_set = seed_set.intersection(resp_set)
    
    # remove common identifiers
    full_set = full_set.difference(unrel_set)

    # Make sure that ID showed up as an ID in HTTP cookies of base (thus passes all ID tests)
    output_set = set()
    for item in full_set:
        print "Checking for " + item[2] + " in original HTTP cookies"
        for val_string in HTTP_base_IDs.values():
            if val_string in item[2]:
                output_set.add(item)
                break

    return output_set

if __name__=='__main__':
    db1 = os.path.join(DATA_DIR,'alexa3k_05062014_fresh_triton.sqlite')
    db2 = os.path.join(DATA_DIR,'alexa3k_05072014_recrawl_triton.sqlite')
    db3 = os.path.join(DATA_DIR,'alexa3k_05062014_fresh_kingpin.sqlite')
    db4 = os.path.join(DATA_DIR,'alexa3k_05072014_HTTP_cookies_snoop.sqlite')

    output_set = check_for_respawned_flash([db1,db2,db3,db4])
    for line in output_set:
        print line
