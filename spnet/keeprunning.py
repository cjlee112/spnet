import subprocess
import sys

while True:
    print 'Starting server...'
    subprocess.call([sys.executable, 'watchmem.py'])

