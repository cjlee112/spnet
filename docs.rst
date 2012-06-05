=================
ArXiv RSS docs
=================

This simple script pulls from the various available ArXiv categories, parses the paper information into dictionaries, and stores the dictionaries in a pickle file arxiv.pickle.

Invoking the script with:

    python arxiv_rss.py

downloads new papers from each category and adds new papers to the pickle file. To simply load the cache, use load_cache(). To get new papers and load the cache use get_papers(). get_papers takes an optional parameter download=False which defaults the behavior to load_cache().

Because the robots.txt file of the ArXiv specifies a wait time of 20 seconds, between each feed the download function sleeps for 20 seconds, so if you call the downloader from another piece of code, expect this behavior. Loading the cache with load_cache() does not invoke this behavior.



