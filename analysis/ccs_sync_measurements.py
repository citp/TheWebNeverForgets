import extract_cookie_ids
import extract_id_knowledge
import census_util
import sqlite3 as lite
import Queue
import re
import os
import numpy

# Location of downloaded files
DATA_DIR = os.path.expanduser('~/Desktop')

# BFS HOP ANALYSIS
# for a given domain, returns a sorted list of sites within <hops> steps away in the sync graph
def build_hop_neighborhood(seed_domain, hop, domain_to_id, id_to_domain):
    domains_explored = set()  # list of domains we've visited
    search_queue = Queue.Queue()  # list of the sites that we'll be visiting
    search_queue.put((seed_domain, 0))  # seeds the search with the initial domain

    # performs the BFS neighborhood search
    while not search_queue.empty():
        curr_domain, curr_depth = search_queue.get()

        # break the search if the nodes are too far away
        if curr_depth > hop:
            break

        # don't explore the node if we've already seen it
        if curr_domain in domains_explored:
            continue

        domains_explored.add(curr_domain)

        # don't expand out to neighbors if we are at the edge of the neighborhood
        if curr_depth == hop:
            continue

        # update the search queue
        for cookie_id in domain_to_id[curr_domain]:
            for domain in id_to_domain[cookie_id]:
                search_queue.put((domain, curr_depth + 1))

    neighborhood = list(domains_explored)
    neighborhood.sort()
    return neighborhood

# OVERALL COOKIE SYNC SCRIPT
# prints off the relevant statistics for the cookie syncing studies, given two crawl databases
# <db_to_analyze> specifies whether to extract from db1 or db2
def output_sync_measurements(db1, db2, db_to_analyze=1):
    
    print "Extracting persistent identifiers from each crawl..."
    # extract the cookie ids on a per-database basis
    cookies_db1 = extract_cookie_ids.extract_persistent_ids_from_dbs([db1])
    cookies_db2 = extract_cookie_ids.extract_persistent_ids_from_dbs([db2])
    
    print "Grabbing cookies..."

    # get the cookies that appear to be consistent ids and extract their values from db1
    id_cookies = extract_cookie_ids.extract_common_id_cookies([cookies_db1, cookies_db2])
    
    if db_to_analyze == 1:
        domain_to_fp_map = census_util.build_domain_map(db1)
        known_ids = extract_cookie_ids.extract_known_cookies_from_db(db1, id_cookies)
    else:
        domain_to_fp_map = census_util.build_domain_map(db2)
        known_ids = extract_cookie_ids.extract_known_cookies_from_db(db2, id_cookies)

    # remove known opt-out cookie strings
    for key in known_ids.keys():
        if (known_ids[key] == '0' \
            or known_ids[key] == '00000000-0000-0000-0000-000000000000' \
            or known_ids[key] == '0000000000000000' \
            or known_ids[key] == 'AAAAAAAAAAAAAAAAAAAAAA'):
            del known_ids[key]

    print "Build mapping between cookies, domains, and first parties..."

    # build the three maps that are most fundamental to the analysis
    id_to_cookie_map = extract_cookie_ids.map_ids_to_cookies(known_ids)
    id_to_cookie_map_pruned = census_util.prune_list_dict(id_to_cookie_map)

    if db_to_analyze == 1:
        id_to_domain_map = extract_id_knowledge.build_id_knowledge_dictionary(id_to_cookie_map, db1)
    else:
        id_to_domain_map = extract_id_knowledge.build_id_knowledge_dictionary(id_to_cookie_map, db2)
    id_to_domain_map = census_util.prune_list_dict(id_to_domain_map)

    domain_to_id_map = extract_id_knowledge.map_domains_to_known_ids(id_to_domain_map)
    domain_to_id_map_pruned = census_util.prune_list_dict(domain_to_id_map)

    print "Dumping results..."
    print "==========================================================================================="
    print "\nID and # of domains with knowledge of it:"

    id_to_domain_counts = census_util.sort_tuples([(key, len(id_to_domain_map[key])) for key in id_to_domain_map])
    print id_to_domain_counts
    id_to_dm = list()
    for x in id_to_domain_counts:
        id_to_dm.append(x[1])
        print str(x[0]) + "\t" + str(x[1])
    
    print "==========================================================================================="
    print "\nDomain and IDs that it has knowledge of:"

    domain_to_id_counts = census_util.sort_tuples([(key, len(domain_to_id_map[key])) for key in domain_to_id_map])
    print domain_to_id_counts

    print "==========================================================================================="
    print "\nDomain and number of visits from history known:"

    dm_to_id = list()
    for domain, count in domain_to_id_counts:
        neigh1 = build_hop_neighborhood(domain, 1, domain_to_id_map, id_to_domain_map)
        depth1 = len(neigh1)
        num_doms1 = len(census_util.get_values_from_keys(neigh1, domain_to_fp_map))

        neigh2 = build_hop_neighborhood(domain, 2, domain_to_id_map, id_to_domain_map)
        depth2 = len(neigh2)
        num_doms2 = len(census_util.get_values_from_keys(neigh2, domain_to_fp_map))

        dm_to_id.append(count)
        print str(domain) + "\t" + str(count) + "\t" + str(depth1) + "\t" + str(num_doms1) + "\t" + str(depth2) + "\t" + str(num_doms2)
    
    # BASIC STATS
    print "==========================================================================================="
    print "\n Summary statistics:"
    print "NUMBER OF IDS: " + str(len(id_to_cookie_map))
    print "NUMBER OF ID COOKIES: " + str(len(known_ids))
    print "NUMBER OF IDS IN SYNCS: " + str(len(id_to_domain_map))
    print "NUMBER OF ID COOKIES IN SYNC: " + str(sum([len(id_to_cookie_map[key]) for key in id_to_domain_map]))
    print "NUMBER OF DOMAINS IN SYNC " + str(len(domain_to_id_map))
    print "ID TO DOMAIN " + str(min(id_to_dm)) + " | "  + str(numpy.mean(id_to_dm)) + ' | ' + str(numpy.median(id_to_dm)) + " | " + str(max(id_to_dm))
    print "DOMAIN TO ID " + str(min(dm_to_id)) + " | "  + str(numpy.mean(dm_to_id)) + ' | ' + str(numpy.median(dm_to_id)) + " | " + str(max(dm_to_id))

# RESPAWN / SYNC SCRIPT
# checks for respawning and syncing of cookie data
# baseline is a list of at least one database used to perform the diffs (but we don't actually care about spawning here)
# pre_clear is the first database of some sort of crawl run before we make a clear command
# post_clear is the second datbase of some crawl after the clear - here we care about the chance of respawning
def perform_respawn_resync_study(baseline_db, pre_clear_db, post_clear_db):
    print "Extracting initial set of ID cookies"
    cookies_baseline = extract_cookie_ids.extract_persistent_ids_from_dbs([baseline_db])
    cookies_pre_clear = extract_cookie_ids.extract_persistent_ids_from_dbs([pre_clear_db])

    print "Extracting the pre-clear IDs"
    id_cookies = extract_cookie_ids.extract_common_id_cookies([cookies_baseline, cookies_pre_clear])
    pre_clear_ids = extract_cookie_ids.extract_known_cookies_from_db(baseline_db, id_cookies) # CHANGE THIS LINE DEPENDING ON Q

    print "Build the sync maps on the post_clear db"
    # build the three maps that are most fundamental to the analysis
    id_to_cookie_map = extract_cookie_ids.map_ids_to_cookies(pre_clear_ids)
    id_to_cookie_map_pruned = census_util.prune_list_dict(id_to_cookie_map)

    id_to_domain_map = extract_id_knowledge.build_id_knowledge_dictionary(id_to_cookie_map, post_clear_db)
    #id_to_domain_map = census_util.prune_list_dict(id_to_domain_map)

    domain_to_id_map = extract_id_knowledge.map_domains_to_known_ids(id_to_domain_map)
    domain_to_id_map_pruned = census_util.prune_list_dict(domain_to_id_map)

    print id_to_domain_map

# GRAPH RE-SPAWN SCRIPT
def connect_graph_through_sync(baseline_db, pre_sync_db, post_sync_db):
    print "Extracting initial set of ID cookies"
    cookies_baseline = extract_cookie_ids.extract_persistent_ids_from_dbs([baseline_db])
    cookies_pre_sync = extract_cookie_ids.extract_persistent_ids_from_dbs([pre_sync_db])
    cookies_post_sync = extract_cookie_ids.extract_persistent_ids_from_dbs([post_sync_db])

    print "Extracting the domain to first-party mappings"
    fp_map_pre_sync = census_util.build_domain_map(pre_sync_db)
    fp_map_post_sync = census_util.build_domain_map(post_sync_db)

    print "Building the sync graphs"
    mappings = [] # first mapping is ID to domain - second is domain to ID; 0 is pre_sync 1 is post_sync
    for cookie_database, cookies in [(pre_sync_db, cookies_pre_sync), (post_sync_db, cookies_post_sync)]:
        print "Building the graph for " + cookie_database
        id_cookies = extract_cookie_ids.extract_common_id_cookies([cookies_baseline, cookies])
        id_cookies_with_val = extract_cookie_ids.extract_known_cookies_from_db(cookie_database, id_cookies)
        
        print "Building id to cookie mapping"
        id_to_cookie_map = extract_cookie_ids.map_ids_to_cookies(id_cookies_with_val)

        print "Building id to domain mappings"
        id_to_domain_map = extract_id_knowledge.build_id_knowledge_dictionary(id_to_cookie_map, cookie_database)
        id_to_domain_map = census_util.prune_list_dict(id_to_domain_map)

        print "Building domain to id mappings"
        domain_to_id_map = extract_id_knowledge.map_domains_to_known_ids(id_to_domain_map)
        #domain_to_id_map = census_util.prune_list_dict(domain_to_id_map)

        mappings.append((id_to_cookie_map, id_to_domain_map, domain_to_id_map))

    print "Pull out respawned and resynced IDs"
    respawned_id_to_domain_map = extract_id_knowledge.build_id_knowledge_dictionary(mappings[0][0], post_sync_db)
    respawned_id_to_domain_map = census_util.prune_list_dict(respawned_id_to_domain_map)
    
    respawned_domain_to_id_map = extract_id_knowledge.map_domains_to_known_ids(respawned_id_to_domain_map)  
    respawned_domain_to_id_map = census_util.prune_list_dict(respawned_domain_to_id_map)

    print "Printing all possible ids"
    old_ids = mappings[0][1].keys()
    old_domains = mappings[0][2].keys()
    new_ids = mappings[1][1].keys()
    new_domains = mappings[1][2].keys()
    all_ids = set(old_ids).union(set(new_ids))
    all_domains = set(old_domains).union(set(new_domains))
    print "IDS:\t" + str(len(old_ids)) + "\t" + str(len(new_ids)) + "\t" + str(len(all_ids))
    print "DOMAINS:\t" + str(len(old_domains)) + "\t" + str(len(new_domains)) + "\t" + str(len(all_domains))
    
    print "Examining graph linkage"
    for respawned_id in respawned_id_to_domain_map:
        old_neighborhood = build_hop_neighborhood(respawned_id, float("inf"), mappings[0][1], mappings[0][2])
        old_neighborhood_domains = census_util.get_values_from_keys(old_neighborhood, mappings[0][1])
        old_fp_domains = census_util.get_values_from_keys(old_neighborhood_domains, fp_map_pre_sync)

        new_neighborhood = build_hop_neighborhood(respawned_id, float("inf"), mappings[1][1], mappings[1][2])
        new_neighborhood_domains = census_util.get_values_from_keys(new_neighborhood, mappings[1][1])   
        new_fp_domains = census_util.get_values_from_keys(new_neighborhood_domains, fp_map_post_sync)

        full_neighborhood = set(old_neighborhood).union(set(new_neighborhood))
        full_neighborhood_domains = set(old_neighborhood_domains).union(set(new_neighborhood_domains))
        full_fp_domains = set(old_fp_domains).union(set(new_fp_domains))

        print respawned_id + "\t" + str(len(old_neighborhood)) + "\t" + str(len(new_neighborhood)) + "\t" + str(len(full_neighborhood))
        print respawned_id + "\t" + str(len(old_neighborhood_domains)) + "\t" + str(len(new_neighborhood_domains)) + "\t" + str(len(full_neighborhood_domains))
        print respawned_id + "\t" + str(len(old_fp_domains)) + "\t" + str(len(new_fp_domains)) + "\t" + str(len(full_fp_domains))

if __name__ == "__main__":
    P4 = os.path.join(DATA_DIR, 'alexa3k_05062014_fresh_triton.sqlite')
    P6 = os.path.join(DATA_DIR, 'alexa3k_05072014_recrawl_triton.sqlite')
    
    # 2 crawl method
    #output_sync_measurements(triton, kingpin) #3p allow
    output_sync_measurements(P4, P6) #block 3p
    
    #connect_graph_through_sync(triton1, kingpin1, kingpin3)
