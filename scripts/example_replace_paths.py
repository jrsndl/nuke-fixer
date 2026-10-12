"""Search & replace text in every file path knob (Read, Write, ReadGeo, Camera, ...).

Typical use: a project or server moved.
Edit OLD / NEW below. Only scripts that actually change are saved.
"""
import nuke

OLD = "C:/projects/OldServer/"
NEW = "C:/projects/NewServer/"

changed = 0
for node in nuke.allNodes(recurseGroups=True):
    for knob in node.knobs().values():
        if not isinstance(knob, nuke.File_Knob):
            continue
        value = knob.value() or ""
        if OLD in value:
            knob.setValue(value.replace(OLD, NEW))
            changed += 1
            nf.log("%s.%s -> %s" % (node.fullName(), knob.name(), knob.value()))

if changed == 0:
    nf.skip_save = True
nf.log("%d path(s) replaced" % changed)
