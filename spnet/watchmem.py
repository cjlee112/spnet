import resource
import web
import thread
import view
import time

# runs spnet web server with explicit memory limit
# as workaround for Python memory usage going up and up
# due to Python memory fragmentation
# see http://revista.python.org.ar/2/en/html/memory-fragmentation.html
# run keeprunning.py to call this and automatically restart whenever
# memory usage limit exceeded.

maxmem = 150000 # max RSS in KB
checkInterval = 60 # seconds between mem usage checks

s = web.Server() # initialize db connection, REST apptree etc.
thread.start_new_thread(view.poll_recent_events, (s.papers.klass, s.topics.klass)) # start polling db for "recent events"
s.start() # run web server in separate thread

def mem_usage():
    'report RSS memory usage by our process in KB'
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

while mem_usage() < maxmem: # if exceeded memory limit, exit and restart
    time.sleep(checkInterval) # wait a bit before next check
