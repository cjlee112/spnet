import time
import subprocess
import sys
import resource

# enforce maxmem using rlimit
maxmem = 50 * 1024 # 50 MB
resource.setrlimit(resource.RLIMIT_AS, (maxmem * 1024, maxmem * 1024))



# just polls Google+ for latest updates every 5 minutes

while True:
    print 'Starting poll...'
    subprocess.call([sys.executable, 'gplus.py'])
    time.sleep(300)

