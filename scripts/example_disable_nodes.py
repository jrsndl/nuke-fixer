"""Disable (or delete) all nodes of the given classes."""
import nuke

CLASSES = ("DeepRecolor_Broken", "OFXuk.co.thefoundry.furnace.f_steadiness_v403")  # edit me
DELETE = False                  # True deletes the nodes instead of disabling them

changed = 0
for node in nuke.allNodes(recurseGroups=True):
    if node.Class() not in CLASSES:
        continue
    if DELETE:
        nuke.delete(node)
    elif "disable" in node.knobs() and not node["disable"].value():
        node["disable"].setValue(True)
    else:
        continue
    changed += 1

if changed == 0:
    nf.skip_save = True
nf.log("%s %d node(s)" % ("deleted" if DELETE else "disabled", changed))
