from multiprocessing import Pool
MAX_SLEEP = 45


def run_in_parallel(inputs, worker, no_of_processes=4):
    """Run given worker function in parallel with number of processes given."""
    p = Pool(no_of_processes)
    try:
        p.map(worker, inputs)
    except OSError as ose:
        print "Exception while running crawl worker", ose
