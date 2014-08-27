The Web Never Forgets: Persistent tracking mechanisms in the wild
=================================================================

In our CCS 2014 paper, [The Web Never Forgets](https://securehomes.esat.kuleuven.be/~gacar/persistent/the_web_never_forgets.pdf), we measure three advanced tracking
mechanisms, canvas fingerprinting, cookie respawning, and cookie syncing and
explore the privacy implications of their use. For a more detailed overview and
access to the data visit the project's [homepage](https://securehomes.esat.kuleuven.be/~gacar/persistent/).

This repository contains scripts for re-running the entire project, and is
broken down into measurement, analysis, and visualization.

Measurement
-----------

Two crawlers, one developed at KU Leuven and one developed at Princeton are
used. The crawlers are both built on top of similar technologies, but are functionally
quite different. The Leuven crawler isolates state between page visits and was
used for all parallel crawls. The Princeton crawler keeps consistent state and
was used for all sequential crawls.

**Sequential**  Version [v0.2.0](https://github.com/citp/OpenWPM/releases) of
OpenWPM is contained in *OpenWPM* along with the necessary crawling scripts. 
You can run these crawls from that directory with `python sequential_crawl.py`

**Parallel** --Coming soon--

Analysis
--------
The analysis performed in the paper can be recreated with the following analysis
scripts. Once the data is downloaded, update the scripts to point to your download
location, and find the analysis output either printed to stdout or to a summary file.

**Canvas Fingerprinting** --Coming soon--

**Cookie Repawning** --Incomplete-- 
- *ccs_respawn_measurements.py* - HTTP Cookies respawned from Flash Objects

**Cookie Syncing** - these analysis scripts and supporting utilities are included 
in *analysis*
- *ccs_sync_measurements.py* - cookie sync analysis + cookie respawn and sync analysis
- *census_util* - supporting utilities for all scripts
- *extract_cookie_ids.py* - extracts id cookies from pairs of databases
- *extract_id_knowledge.py* - supporting algorithms for sync analysis

Visualization
-------------

Code for the generation of graphs, including those in our [blogpost](https://freedom-to-tinker.com/blog/englehardt/the-hidden-perils-of-cookie-syncing/)
is included. Some manual visualization done in [Gephi](https://gephi.github.io/)

Dependencies
------------

OpenWPM's dependencies can be found on the [repo wiki](https://github.com/citp/OpenWPM/wiki/Setting-up-OpenWPM#manual-installation-and-dependencies)

    sudo pip install numpy tld publicsuffix networkx 
