from urlparse import urlparse
from publicsuffix import PublicSuffixList
psl = PublicSuffixList()
import networkx
import datetime
import cPickle
import sqlite3
import os
import re

# Bugfixes to dynamic graph output
from gexf import write_gexf

# Load the list of ID cookies
id_cookies = cPickle.load(open(os.path.join(os.path.dirname(__file__),"id_cookies.p")))

#TODO: update with real data name
con = sqlite3.connect(os.path.expanduser('~/Desktop/alexa3k_05062014_fresh_triton.sqlite'))
cur = con.cursor()

G = networkx.DiGraph()

#Create a tracking graph
def create_tracker_graph():
    cur.execute(("SELECT r.url, r.referrer, r.top_url, c.name, c.value "
                "FROM http_requests as r, http_cookies as c "
                "WHERE r.id = c.header_id "
                "AND c.http_type = 'request' "
                "AND top_url IN "
                "(SELECT DISTINCT top_url FROM http_requests LIMIT 1500)"))
    for url, ref, top, name, value in cur.fetchall():
        if ref is None or ref == '': # Empty referrer
            continue
        
        req_host = psl.get_public_suffix(urlparse(url).hostname)
        ref_host = psl.get_public_suffix(urlparse(ref).hostname)
        top_host = psl.get_public_suffix(urlparse(top).hostname)

        if top_host != ref_host: # Request that doesn't have knowledge of top url
            continue
        if ref_host == req_host: # Self loops
            continue
        if req_host == 'facebook.com': # Facebook
            continue

        # Check if identifying cookie
        for item in id_cookies.keys():
            if req_host.endswith(item) and name in id_cookies[item]:
                # If so, add nodes and edge
                G.add_node(req_host)
                G.add_node(ref_host)
                G.add_edge(ref_host, req_host)
                break
    networkx.write_gexf(G,os.path.expanduser('~/Desktop/05062014_triton.gexf'))

# Create respawn graph
def create_respawn_graph():
    counter = 0
    post_clear = 0
    tracker_start_time = None
    cur.execute(("SELECT r.url, r.referrer, r.top_url, r.time_stamp, c.name, c.value "
                "FROM http_requests as r, http_cookies as c "
                "WHERE r.id = c.header_id "
                "AND c.http_type = 'request' "
                "AND top_url IN "
                "(SELECT DISTINCT top_url FROM http_requests LIMIT 1500) "
                "ORDER BY time_stamp"))
    temp = cur.fetchall()
    cookie_clear_point = len(temp)/2
    for url, ref, top, time_stamp, name, value in temp:
        counter += 1
        if ref is None or ref == '': # Empty referrer
            continue
        
        #Convert the timestamp
        time_stamp = datetime.datetime.strptime(time_stamp.split('.')[0],'%Y-%m-%d %H:%M:%S')
        time_stamp = float(time_stamp.strftime('%s'))

        if tracker_start_time is None:
            tracker_start_time = time_stamp

        req_host = psl.get_public_suffix(urlparse(url).hostname)
        ref_host = psl.get_public_suffix(urlparse(ref).hostname)
        top_host = psl.get_public_suffix(urlparse(top).hostname)

        if top_host != ref_host: # Request that doesn't have knowledge of top url
            continue
        if ref_host == req_host: # Self loops
            continue

        if counter >= cookie_clear_point:
            post_clear = 1
            tracker_start_time = time_stamp

        # Check if identifying cookie
        for item in id_cookies.keys():
            if req_host.endswith(item) and name in id_cookies[item]:
                # If so, add nodes and edge
                G.add_node(req_host + str(post_clear), start=tracker_start_time)
                G.add_node(ref_host, start=time_stamp)
                G.add_edge(ref_host, req_host + str(post_clear), start=time_stamp)
                break
    write_gexf(G,os.path.expanduser('~/Desktop/05062014_triton_respawn.gexf'))

if __name__ == '__main__':
    create_respawn_graph()
