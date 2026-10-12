"""NukeFixer script template.

This file runs once for every Nuke script in the queue, inside Nuke
(nuke -t), right after the Nuke script has been opened.

Available names
    nuke          the Nuke python module
    nf.file       path of the Nuke script being processed
    nf.dry_run    True when "Dry run" is on (NukeFixer will not save)
    nf.skip_save  set to True to NOT save this script (e.g. nothing changed)
    nf.log(text)  message shown in NukeFixer's Log tab

Rules
    * Raise an exception to mark the script as FAILED - it is not saved.
    * NukeFixer makes a backup copy before saving (see Settings).
    * Don't call nuke.scriptSave()/scriptClose() yourself - NukeFixer does it.
    * Several Nuke scripts can run in the same Nuke session, one after the
      other. Don't leave global state behind (callbacks, sys.path changes...),
      or set "Scripts per Nuke process" to 1.
"""
import nuke

changed = 0

for node in nuke.allNodes(recurseGroups=True):
    # example: inspect / modify nodes here
    pass

if changed == 0:
    nf.skip_save = True          # nothing to do - leave the file untouched

nf.log("changed %d node(s)" % changed)
