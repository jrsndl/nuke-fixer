import os
import sys
import nuke
import runme

if os.path.exists(sys.argv[1]):
    nuke.scriptOpen(sys.argv[1])
    runme.main()