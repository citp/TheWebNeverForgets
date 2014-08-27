from automation import TaskManager
import time
import os

# The list of sites that we wish to crawl
NUM_BROWSERS = 1
with open(os.path.join(os.path.dirname(__file__),'sites.txt'), 'r') as f:
    sites = f.read().split('\n')

# Saves a crawl output DB to the Desktop
db_loc  = os.path.expanduser('~/Desktop/openwpm_demo.sqlite')

# Loads 3 copies of the default browser preference dictionaries
browser_params = TaskManager.load_default_params(NUM_BROWSERS)

#Launch the first browser headless
browser_params[0]['headless'] = True
browser_params[0]['disable_flash'] = False

# Instantiates the measurement platform
# Launches two (non-headless) Firefox instances and one headless instance
# logging data with MITMProxy
# Commands time out by default after 60 seconds
manager = TaskManager.TaskManager(db_loc, browser_params, NUM_BROWSERS)

# Visits the sites with both browsers simultaneously, 5 seconds between visits
for site in sites:
    site = 'http://' + site
    start_time = time.time()
    manager.get(site)
    manager.dump_storage_vectors(site, start_time)

# Shuts down the browsers and waits for the data to finish logging
manager.dump_profile(os.path.expanduser('~/Desktop/demo_profile/'),close_webdriver=True)
manager.close()
