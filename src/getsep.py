#!/usr/bin/env python

from __future__ import print_function
import sys
import os

try:
    filename = sys.argv[1]
except IndexError:
    print("USAGE: getsep.py outputfile")
    sys.exit(0)

# open the include file
try:
    idfile = open(filename, "w")
except:
    print("Cannot open id file %s for writing" % idfile)
    sys.exit(0)

idfile.write("\n\nc     Path separator, generated by getsep.py\n")
idfile.write("c     Should be used whenever constructing paths\n")
idfile.write(" " * 6 + "character PATHSEP\n")
idfile.write(" " * 6 + 'parameter(PATHSEP="%s")\n\n' % os.path.sep)
idfile.close()
