# avrUpdifuse, avr UPDI fuse control, V0.8 230203 qrt@qland.de

import os
import subprocess
import msvcrt
import string

DEVICE = 't402'
COM = 'com5'
dudePath = 'c:/progs/avrdude'

cmdBase = 'avrdude -c jtag2updi -p ' + DEVICE + ' -P ' + COM
cmdGetmem = cmdBase + ' -v'
cmdFuse = cmdBase + ' -U '

supdis = [ 'fuses',    'signature', 'prodsig',  'tempsense', 'sernum',          # suppress display
           'osccal16', 'osccal20',  'osc16err', 'osc20err', 
           'data',     'userrow',   'eeprom',   'flash' ]

class Fuse:
    def __init__(self, name, alias, cur=0, new=0):
        self.name = name
        self.alias = alias
        self.cur = cur
        self.new = new

fuses = []

#-------------------------------------------------------------------------------
# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal

COLRES = '\033[0;0m'                                                # color reset
COLSEL = '\033[42m'                                                 #       white on dark green
COLDIF = '\033[41m'                                                 #       white on red

def clear():                                                        # cursor handling
    print(COLRES, end='')
    print('\033[H\033[J', end="")

def cursorUp(n):
    print('\033[{}A'.format(n), end='')

def cursorDown(n):
    print('\033[{}B'.format(n), end='')

def cursorLeft(n):
    print('\033[{}D'.format(n), end='')

def cursorRight(n):
    print('\033[{}C'.format(n), end='')

#-------------------------------------------------------------------------------

def waitGetKey():                                                   # wait for keys and get them
    while True:
        c = ord(msvcrt.getch())
        
        if c == 224:
            c = ord(msvcrt.getch())

            if c == 72:
                return 'up'
            elif c == 80:
                return 'down'            
        elif c == ord('m'):        
            return 'modify'
        elif c == ord('w'):
            return 'write'
        elif c == 27:
            return 'esc'

#-------------------------------------------------------------------------------

def printFuses(ifuse):                                              # print fuses
    clear()
    print('{:16s}{:16s}{}'.format('fuse', 'current  (hex)', 'new'))
    print('-----------------------------------')    

    i = 0
 
    for f in fuses:
        col = COLSEL if ifuse==i else (COLRES if f.cur==f.new else COLDIF)
        print('{}{:16s}{:02x}              {:02x}'.format(col, f.alias, f.cur, f.new))
        i += 1
    
    print(COLRES)
    print('(arrow-up) (arrow-down) (m)odify (w)rite (esc)exit')

#-------------------------------------------------------------------------------

def newValue(ifuse):                                                # set new fuse value
    cursorUp(numFus - ifuse + 2)
    cursorRight(30)
    v = input('->') 

    if v!='' and all(c in string.hexdigits for c in v):   
        v = int(v, 16)

        if v < 256:            
            fuses[ifuse].new = v

#-------------------------------------------------------------------------------

def writeFuses(ifuse):                                              # write modified fuses
    wfuse = 0

    for f in fuses:
        if f.cur != f.new:
            printFuses(ifuse)
            output = subprocess.getoutput(cmdFuse + f.name + ':w:'+ hex(f.new) + ':m')
            output = subprocess.getoutput(cmdFuse + f.name + ':r:fuse.txt:h')            

            with open('fuse.txt') as fp:
                f.cur = int(fp.readlines()[0], 16)
                f.new = f.cur

            printFuses(ifuse)

        wfuse += 1

#===============================================================================

try:                                                                # retrieve memories of MCU
    os.chdir(dudePath)                                                  
except FileNotFoundError:
    print("Error: directory: {0} does not exist".format(dudePath))
except NotADirectoryError:
    print("Error: {0} is not a directory".format(dudePath))
except PermissionError:
    print("Error: no permissions to change to {0}".format(dudePath))

output = subprocess.getoutput(cmdGetmem)

# - - - - - - - - - - - - - - - - - - -

lines = output.splitlines()                                         # analyse output

ifuse = 0

while not 'Memory Type Alias' in lines[ifuse]:
    ifuse += 1

if ifuse == len(lines):
    print('Error: Memories not found')
    exit(0)

if not ' ----------- -----' in lines[ifuse+1]:
    print('Error: Memories not found')
    exit(0)

ifuse += 2

# - - - - - - - - - - - - - - - - - - -

while lines[ifuse]!='' and ifuse<len(lines):                        # store filtered fuses in list
    entry = lines[ifuse].strip().split()

    if not entry[0] in supdis:
        if entry[1].isnumeric():
            alias = entry[0]
            size = entry[6]
        else:
            alias = entry[1]
            size = entry[7]

        fuses.append(Fuse(entry[0], alias, size))    

    ifuse += 1

# - - - - - - - - - - - - - - - - - - -

clear()                                                             # read and list fuse values
print('{:16s}{:16s}{}'.format('fuse', 'current  (hex)', 'new'))
print('-----------------------------------')

for f in fuses:
    output = subprocess.getoutput(cmdFuse + f.name + ':r:fuse.txt:h')

    with open('fuse.txt') as fp:
        f.cur = int(fp.readlines()[0], 16)
        f.new = f.cur

    print('{:16s}{:02x}              {:02x}'.format(f.alias, f.cur, f.new))

# - - - - - - - - - - - - - - - - - - -

ifuse = 0                                                           # main loop
numFus = len(fuses)

while True:
    printFuses(ifuse)

    while True:
        key = waitGetKey()

        if key == 'up':
            ifuse -= 1

            if ifuse < 0:
                ifuse = 0

            break

        elif key == 'down':    
            ifuse += 1

            if ifuse >= numFus:
                ifuse = numFus - 1

            break

        elif key == 'modify':
            newValue(ifuse)
            break

        elif key == 'write':
            writeFuses(ifuse)      
            break  

        elif key == 'esc':
            exit(0)

#-------------------------------------------------------------------------------

# import readline     # pip install pyreadline3 
#
# def inputPret(prompt, text):
#     def hook():
#         readline.insert_text(text)
#         readline.redisplay()
#    
#     readline.set_pre_input_hook(hook)    
#     result = input(prompt)    
#     readline.set_pre_input_hook()
#     return result
