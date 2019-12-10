#!/usr/bin/env python3
import sys
import os

# usage: banWordCheck [target file] [word]

word = sys.argv[2]
filename = sys.argv[1]

cmd = 'grep -q {} {}'.format(word, filename);
if os.system(cmd) == 0:
    print("found key word: {}".format(word))
    quit(1)
else:
    quit(0)
