import time
import subprocess
import sys

# just polls Google+ for latest updates every 5 minutes

while True:
    print 'Starting poll...'
    subprocess.call([sys.executable, 'gplus.py'])
    time.sleep(300)

