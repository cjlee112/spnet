import time
import subprocess

# just polls Google+ for latest updates every 5 minutes

while True:
    print 'Starting poll...'
    subprocess.call(['python', 'gplus.py'])
    time.sleep(300)

