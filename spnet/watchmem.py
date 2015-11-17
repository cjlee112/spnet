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
maxtime = 60 * 60 # restart after one hour
checkInterval = 1 # seconds between mem usage checks

def limit_vsz(maxvsz):
    'enforce maxmem using rlimit'
    resource.setrlimit(resource.RLIMIT_AS, (maxvsz * 1024, maxvsz * 1024))

def get_vsz():
    'get this process current VSZ as int'
    pid = os.getpid()
    t = subprocess.check_output(['ps', '-p%d' % pid, '-o', 'vsz']).split()
    return int(t[-1])

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
    if f:
        f.write(msg + '\n')
        f.flush()
        os.fsync(f.fileno())

#logfile = open('watchmem.log', 'a') # need data to see why still running out of memory!!
logfile = None
log(logfile, 'starting...')

time.sleep(10) # let web server fully start up
vsz = get_vsz() # measure baseline VSZ
limit_vsz(vsz + maxmem)
print 'setrlimit VSZ =', vsz + maxmem

mem = 0
startTime = time.time()
while mem < maxmem and time.time() - startTime < maxtime: # if exceeded memory limit, exit and restart
    time.sleep(checkInterval) # wait a bit before next check
    mem = mem_usage()
    log(logfile, str(mem))

log(logfile, 'shutting down...')
s.shutdown()

