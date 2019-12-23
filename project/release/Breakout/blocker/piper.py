from threading import Thread
from queue import Queue, Empty, LifoQueue
import subprocess
import sys
import os
import time
import platform

sys.path.append( os.path.abspath ( '..' ) )
os.chdir( os.path.abspath ( '..' ) )
import agent
os.chdir( os.path.abspath ("./blocker") )
sys.path.append( os.path.abspath ( 'game' ) )

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

ON_POSIX = 'posix' in sys.builtin_module_names
t_start = time.time()
if platform.system() == "Windows":
    p = subprocess.Popen( ["python3", os.path.abspath("game/breakbricks.py") ], stdout=subprocess.PIPE, stdin=subprocess.PIPE,shell=True)
else:
    p = subprocess.Popen( ["python3", os.path.abspath("game/breakbricks.py") ], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
q = LifoQueue()
t = Thread(target=enqueue_output, args=(p.stdout, q))
t.daemon = True # thread dies with the program
t.start()

while p.poll() == None:
    try:  line = q.get_nowait() # or q.get(timeout=.1)
    except Empty:
        pass
    else: # got line
        #print(line)
        move = agent.decide(line)
        if move == 1:
            p.stdin.write(b'R\n') # b'L\n': move left, b'R'\n: move right
        elif move == -1:
            p.stdin.write(b'L\n') # b'L\n': move left, b'R'\n: move right
        
        p.stdin.flush()	


t_end = time.time()
print(t_end-t_start)
with open(os.path.abspath("../score.txt"), "a") as fo:
    fo.write(str(t_end - t_start))
