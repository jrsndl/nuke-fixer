"""Set compression and bit depth on every EXR Write node."""
import nuke

COMPRESSION = "Zip (1 scanline)"   # as shown in the Write node's compression menu
DATATYPE = "16 bit half"

changed = 0
for node in nuke.allNodes("Write", recurseGroups=True):
    if node["file_type"].value() != "exr":
        continue
    for name, value in (("compression", COMPRESSION), ("datatype", DATATYPE)):
        knob = node.knob(name)
        if knob is not None and knob.value() != value:
            knob.setValue(value)
            changed += 1
    nf.log("%s: %s, %s" % (node.fullName(), node["compression"].value(), node["datatype"].value()))

if changed == 0:
    nf.skip_save = True
