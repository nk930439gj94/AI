import random

prepos = (0,0)

def decide(instr):

    global prepos
    l=instr.decode('ascii').split() 

    if len(instr) <= 6:
        return 0

    if int(l[1]) < prepos[1]:
        if int(l[0]) < int(l[2]):
            decision = -1
        elif int(l[0]) > int(l[2]):
            decision = 1
        else:
            decision = 0
    elif int(l[1]) > ( 555 - 3*( int(l[1]) - prepos[1] ) ):
        decision = 0
    else:
        dx = ( 555-int(l[1]) ) * ( float( int(l[0]) - prepos[0] ) / ( int(l[1]) - prepos[1] ) )
        expectpos = int(l[0]) + dx
        if int(l[2]) < expectpos:
            decision = 1
        elif int(l[2]) > expectpos:
            decision = -1
        else:
            decision = 0
    
    prepos = ( int(l[0]), int(l[1]) )
    return decision
