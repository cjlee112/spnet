import resource
import web
from threading import Thread
import view
import time
import os

# runs spnet web server with explicit memory limit
# as workaround for Python memory usage going up and up
# due to Python memory fragmentation
# see http://revista.python.org.ar/2/en/html/memory-fragmentation.html
# run keeprunning.py to call this and automatically restart whenever
# memory usage limit exceeded.

maxmem = 150000 # max RSS in KB
checkInterval = 1 # seconds between mem usage checks

s = web.Server() # initialize db connection, REST apptree etc.
poll = Thread(target=view.poll_recent_events,
              args=(s.papers.klass, s.topics.klass))
poll.daemon = True # ensure thread will exit automatically
poll.start() # start polling db for "recent events"
s.start() # run web server in separate thread

def mem_usage():
    'report RSS memory usage by our process in KB'
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

def log(f, msg):
    'append message and flush to disk'
    f.write(msg + '\n')
    f.flush()
    os.fsync(f.fileno())

logfile = open('watchmem.log', 'a') # need data to see why still running out of memory!!
log(logfile, 'starting...')

mem = 0    
while mem < maxmem: # if exceeded memory limit, exit and restart
    time.sleep(checkInterval) # wait a bit before next check
    mem = mem_usage()
    log(logfile, str(mem))

log(logfile, 'shutting down...')
s.shutdown()

