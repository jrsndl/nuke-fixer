"""
Nuke 17 - clean BackdropNode1, insert SHlook/SHgrain above renderCompMain.
Headless-safe: works in `nuke -t` (no GUI-only calls).

Will be used with NukeFixer:

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

BACKDROP_NAME = "BackdropNode1"
DELETE_CLASSES = {"ColorCorrect", "Grade", "Cryptomatte", "SoftClip"}
TARGET_GROUP = "renderCompMain"

DOT_NAME = "Dot1"
STOP_CLASS = "PostageStamp"
CHAIN_CLEAN_CLASSES = {"ColorCorrect", "Grade"}
MASK_NODES_TO_DELETE = 2        # how many nodes up the mask pipe get deleted

# tile_color is 0xRRGGBBAA
SHLOOK_COLOR = 0xFF69B4FF   # pink
SHGRAIN_COLOR = 0x87CEEBFF  # light blue

# Node sizes in the DAG. screenWidth()/screenHeight() are unreliable without
# a GUI, so use Nuke's default node footprint instead.
NODE_W, NODE_H = 80, 18
DOT_W, DOT_H = 12, 12


def log(txt):
    nf.log(txt)
    print(txt)


def node_size(n):
    if n.Class() == "Dot":
        return DOT_W, DOT_H
    return NODE_W, NODE_H


def nodes_inside_backdrop(backdrop):
    """Nodes whose centre lies inside the backdrop (pure position test, no GUI)."""
    x1, y1 = backdrop.xpos(), backdrop.ypos()
    x2 = x1 + backdrop["bdwidth"].value()
    y2 = y1 + backdrop["bdheight"].value()
    inside = []
    for n in nuke.allNodes():
        if n is backdrop:
            continue
        w, h = node_size(n)
        cx = n.xpos() + w / 2.0
        cy = n.ypos() + h / 2.0
        if x1 <= cx <= x2 and y1 <= cy <= y2:
            inside.append(n)
    return inside


def delete_and_reconnect(node):
    """Delete a node and wire its input 0 into everything it fed (like the Delete key)."""
    upstream = node.input(0)
    for dep in node.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS, forceEvaluate=False):
        for i in range(dep.inputs()):
            if dep.input(i) is node:
                dep.setInput(i, upstream)
    nuke.delete(node)


def clean_backdrop():
    """Returns True if anything was (or would be) changed."""
    backdrop = nuke.toNode(BACKDROP_NAME)
    if backdrop is None or backdrop.Class() != "BackdropNode":
        log("No backdrop called '{}' - skipping cleanup.".format(BACKDROP_NAME))
        return False

    targets = [n for n in nodes_inside_backdrop(backdrop) if n.Class() in DELETE_CLASSES]
    if not targets:
        log("No ColorCorrect/Grade/Cryptomatte/SoftClip nodes inside {}.".format(BACKDROP_NAME))
        return False

    names = [n.name() for n in targets]

    if nf.dry_run:
        log("Dry run, would delete {} node(s): {}".format(len(names), ", ".join(names)))
        return True

    for n in targets:
        delete_and_reconnect(n)
    log("Deleted {} node(s): {}".format(len(names), ", ".join(names)))
    return True


def mask_input_index(node):
    """Index of the node's mask input (1 for Grade/ColorCorrect)."""
    try:
        idx = node.optionalInput()
        if idx >= 0:
            return idx
    except Exception:
        pass
    return 1


def chain_to_postage_stamp():
    """
    Walk up input 0 from Dot1. Returns the list of nodes strictly between
    Dot1 and the first PostageStamp (nearest Dot1 first), or None if either
    end is missing.
    """
    dot = nuke.toNode(DOT_NAME)
    if dot is None or dot.Class() != "Dot":
        log("No Dot called '{}' - skipping chain cleanup.".format(DOT_NAME))
        return None

    chain = []
    seen = set()
    n = dot.input(0)
    while n is not None and n.name() not in seen:
        if n.Class() == STOP_CLASS:
            return chain
        seen.add(n.name())
        chain.append(n)
        n = n.input(0)

    log("No {} upstream of {} - skipping chain cleanup.".format(STOP_CLASS, DOT_NAME))
    return None


def clean_dot_chain():
    """Returns True if anything was (or would be) changed."""
    chain = chain_to_postage_stamp()
    if chain is None:
        return False

    targets = [n for n in chain if n.Class() in CHAIN_CLEAN_CLASSES]
    if not targets:
        log("No ColorCorrect/Grade between {} and {}.".format(STOP_CLASS, DOT_NAME))
        return False

    # Never delete anything on the main pipe via the mask branch
    protected = {n.name() for n in chain} | {DOT_NAME}

    for cc in targets:
        cc_name = cc.name()

        # Collect up to N nodes up the mask pipe
        mask_nodes = []
        m = cc.input(mask_input_index(cc))
        while m is not None and len(mask_nodes) < MASK_NODES_TO_DELETE:
            if m.name() in protected or m.Class() == STOP_CLASS:
                log("  {}: mask pipe reaches main pipe node {} - not deleting it.".format(
                    cc_name, m.name()))
                break
            mask_nodes.append(m)
            m = m.input(0)

        mask_names = [x.name() for x in mask_nodes]

        if nf.dry_run:
            if mask_names:
                log("Dry run, would delete mask nodes of {}: {}".format(
                    cc_name, ", ".join(mask_names)))
            log("Dry run, would delete {}".format(cc_name))
            continue

        for x in mask_nodes:
            delete_and_reconnect(x)
        if mask_names:
            log("Deleted mask nodes of {}: {}".format(cc_name, ", ".join(mask_names)))

        delete_and_reconnect(cc)
        log("Deleted {}".format(cc_name))

    return True


def create_passthrough_group(name):
    """Empty group with just Input1 -> Output1 so it can be wired into the tree."""
    grp = nuke.nodes.Group(name=name)
    grp.begin()
    inp = nuke.nodes.Input(name="Input1")
    out = nuke.nodes.Output(name="Output1")
    out.setInput(0, inp)
    grp.end()
    return grp


def insert_groups():
    """Returns True if anything was (or would be) changed."""
    target = nuke.toNode(TARGET_GROUP)
    if target is None or target.Class() != "Group":
        log("Group '{}' not found - skipping insert.".format(TARGET_GROUP))
        return False

    if nf.dry_run:
        log("Dry run, would insert SHlook -> SHgrain upstream of {}.".format(TARGET_GROUP))
        return True

    original_input = target.input(0)  # whatever currently feeds renderCompMain

    sh_grain = create_passthrough_group("SHgrain")
    sh_look = create_passthrough_group("SHlook")
    sh_grain["tile_color"].setValue(SHGRAIN_COLOR)
    sh_look["tile_color"].setValue(SHLOOK_COLOR)

    # original_input -> SHlook -> SHgrain -> renderCompMain
    sh_look.setInput(0, original_input)
    sh_grain.setInput(0, sh_look)
    target.setInput(0, sh_grain)

    # Place above renderCompMain (same node width, so same xpos lines them up)
    x = target.xpos()
    sh_grain.setXYpos(x, target.ypos() - 60)
    sh_look.setXYpos(x, target.ypos() - 120)

    log("Inserted SHlook -> SHgrain upstream of {}.".format(TARGET_GROUP))
    return True


def run():
    with nuke.root():   # work at root level, not inside a group
        changed = clean_backdrop()
        changed = clean_dot_chain() or changed
        changed = insert_groups() or changed

    if not changed:
        nf.skip_save = True
        log("Nothing changed - not saving.")


# Undo only makes sense with a GUI; in nuke -t NukeFixer won't save a failed
# script anyway, so there's nothing to roll back.
if nuke.GUI:
    _undo = nuke.Undo()
    _undo.begin("Clean BackdropNode1 + insert SHlook/SHgrain")
    try:
        run()
    except Exception:
        _undo.cancel()
        raise
    else:
        _undo.end()
else:
    run()
