# modCrawler
Crawler based on a modified browser to detect online tracking. Used in the canvas fingerprinting and evercookie detection experiments in our CCS 2014 paper, [The Web Never Forgets](https://securehomes.esat.kuleuven.be/~gacar/persistent/the_web_never_forgets.pdf). Visit [The Web Never Forgets website](https://securehomes.esat.kuleuven.be/~gacar/persistent/) for more info.

# Installation
We strongly suggest you to use a virtual machine, container or similar isolation to install modCrawler.

```
git clone https://github.com/fpdetective/modCrawler
cd modCrawler
./setup.sh
```
### Running the tests
Please run the tests before running the crawler. For simplicity you can run `py.test` from within the `test` directory. py.test will discover and run all the test. Alternatively, you can run individual tests from the command line such as:
```python -m test.runenv_test```

### Command line parameters
Below we give a description of the parameters that are passed to the `agents.py` module.
* `--urls`: path to file that contains the list of URLs to crawl
* `--max_rank`: max line number of the url to be crawled (if urls contain rank info)
* `--min_rank` (optional): min line number of the url to be crawled (if url contains rank info)
* `--max_proc`: maximum number of browsers that will run in parallel
* `--flash`: Flash support (0: disable, 1: enable (default))
* `--cookie`: Cookie support (0: allow all (default), 1: allow 1st party, 2: disable, 3: allow third-party cookies from visited)
* `--upload`: Upload crawl results to a remote server via SSH. 0: don't upload (default), 1: upload (SSH server info should be completed in crawler/common.py)

Example:
* To crawl top 100 urls in the etc/top-1m.csv file using 10 parallel crawlers (Flash disabled).
  * ```python crawl.py --urls etc/top-1m.csv --max_rank 100 --max_proc 10 --flash 0```

* To crawl urls between rank 100-1000 in the etc/top-1m.csv file using 5 parallel crawlers (Flash enabled).
  * ```python crawl.py --urls etc/top-1m.csv --max_rank 1000 --min_rank 100 max_proc 5```

### After the crawl

modCrawler will store the data about the crawls in the jobs directory. For convenience, it places a symlink called **latest** that points to the directory of the most recent crawl.

During the crawl, you can watch the debug.log
```tail -f jobs/latest/debug.log```

Once the crawl has finished, you can find the crawl data in the ```jobs/latest/``` directory.
* **crawl.sqlite**: Sqlite based crawl database.
* **...report.html**: An HTML based report that gives an overview of the results. The name of the file depends on the date and crawl parameters.
* **debug.log**: Debug logs.
* **error.log**: Error logs, file is not created if there is no error.

In addition, the crawl directory is gzipped and stored in the `jobs` directory.

### Building your own browser
The `setup.sh` script will download a modified Firefox which logs canvas fingerprinting related function calls. Alternatively, you can [build your own Firefox](https://developer.mozilla.org/en-US/docs/Simple_Firefox_build) using the provided [browser patch](https://github.com/fpdetective/modCrawler/tree/master/browser_patch). You need to place your freshly built browser to bins/ff-mod directory to make sure it is used by the crawler.
