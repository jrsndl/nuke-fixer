"""Read-only report: never saves. Lists node counts and Read paths that don't exist.

Run it on the whole queue (Dry run is not even needed - nf.skip_save is set).
The output is in the Log tab and the log file.
"""
import os
from collections import Counter

import nuke

nf.skip_save = True

counts = Counter(n.Class() for n in nuke.allNodes(recurseGroups=True))
nf.log("nodes: " + ", ".join("%s=%d" % kv for kv in counts.most_common(8)))

for node in nuke.allNodes("Read", recurseGroups=True):
    path = node["file"].evaluate()           # resolves %04d / #### to the current frame
    if path and not os.path.exists(path):
        nf.log("MISSING  %s  %s" % (node.fullName(), node["file"].value()))
