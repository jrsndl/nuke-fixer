"""
tidy_tree.py - tidy up selected Nuke node trees.

What it does (selected nodes only):
  * lays the tree out top-to-bottom: every connection runs down (or sideways), never up
  * source nodes (Read, Constant, CheckerBoard ... anything with no inputs connected)
    go to the top row
  * main-input (B / input 0) chains become straight vertical strings
  * side inputs (A, mask, ...) come in from their own columns through elbow Dots
  * branches (one node feeding several) get a branch Dot and a horizontal "bus" of Dots
  * spacing between nodes is recomputed so nothing overlaps
  * selected nodes with no connections at all are moved into a grid in empty space
    and left selected, so you can just hit Delete

What it never does:
  * rename, delete, disconnect or reconnect your nodes
  * the only graph change is adding Dot nodes. A Dot is inserted into an existing
    connection, so every input still receives exactly the same upstream node as before.
    (Existing Dots that sit on a branch bus may be chained through the new bus Dots;
    they still carry the same upstream node.)

Install (menu.py):
    import tidy_tree
    nuke.menu('Nuke').addCommand('Edit/Tidy Selected Tree', 'tidy_tree.run()', 'alt+shift+t')

Everything is one undo step (Ctrl+Z restores the previous layout).
Works inside Groups too (run it from the Group's node graph).
"""
from __future__ import print_function, division

import math
import sys

import nuke

# --------------------------------------------------------------------------- settings
COL_GAP = 40          # horizontal space between columns
TREE_GAP = 80         # extra space between unrelated trees
ROW_GAP = 40          # minimum vertical space between rows
LANE_GAP = 14         # vertical spacing of branch "bus" lanes between rows
ELBOW_STAGGER = 8     # vertical offset between multiple side inputs of one node
DOT_SIZE = 12
DEFAULT_W = 80        # used when Nuke reports no size (node never drawn yet)
DEFAULT_H = 18
STAMP_H = 78          # fallback height for nodes showing a postage stamp
SIDE_INPUTS = 'left'  # where side inputs (Merge A, etc.) come from: 'left' or 'right'
MASK_INPUTS = 'right' # where mask inputs come from
AVOID_UNSELECTED = True   # shift the result right until it doesn't overlap other nodes
OBSTACLE_MARGIN = 30
ORPHAN_GAP = 30
SELECT_ORPHANS = True     # leave the unconnected nodes selected for easy deleting
IGNORE_CLASSES = ('BackdropNode', 'StickyNote', 'Root')


# --------------------------------------------------------------------------- helpers
def _size(n):
    w = h = 0
    try:
        w, h = n.screenWidth(), n.screenHeight()
    except Exception:
        pass
    if n.Class() == 'Dot':
        return (w or DOT_SIZE), (h or DOT_SIZE)
    if w <= 0:
        w = DEFAULT_W
    if h <= 0:
        h = DEFAULT_H
        k = n.knob('postage_stamp')
        if k is not None and k.value():
            h = STAMP_H
    return w, h


def _connected_inputs(n):
    return [i for i in range(n.inputs()) if n.input(i) is not None]


def _hidden_input(n):
    k = n.knob('hide_input')
    return bool(k is not None and k.value())


def _is_source(n):
    return not _connected_inputs(n)


def _is_orphan(n):
    """No input connected and nothing depends on it (inputs, hidden inputs, expressions)."""
    if _connected_inputs(n):
        return False
    what = nuke.INPUTS | nuke.HIDDEN_INPUTS | nuke.EXPRESSIONS
    if n.dependent(what, False):
        return False
    try:
        if n.dependencies(nuke.EXPRESSIONS):
            return False
    except Exception:
        pass
    return True


def _main_index(n):
    """Input that continues the vertical string: input 0, or the lowest connected one
    if input 0 is empty."""
    ins = _connected_inputs(n)
    if not ins:
        return None
    return 0 if 0 in ins else ins[0]


def _side_of(n, i):
    label = ''
    try:
        label = n.inputLabel(i) or ''
    except Exception:
        try:
            if n.optionalInput() == i and i == n.maxInputs() - 1:
                label = 'mask'
        except Exception:
            pass
    return MASK_INPUTS if 'mask' in label.lower() else SIDE_INPUTS


def _overlaps(a, b, margin):
    return (a[0] < b[2] + margin and a[2] + margin > b[0] and
            a[1] < b[3] + margin and a[3] + margin > b[1])


def _shift_clear(rects, obstacles, margin):
    """How far right the rects must move so none of them touches an obstacle."""
    if not rects or not obstacles:
        return 0.0
    y0 = min(r[1] for r in rects) - margin
    y1 = max(r[3] for r in rects) + margin
    obstacles = [o for o in obstacles if o[3] > y0 and o[1] < y1]
    dx = 0.0
    for _ in range(2000):
        need = None
        for r in rects:
            rr = (r[0] + dx, r[1], r[2] + dx, r[3])
            for o in obstacles:
                if _overlaps(rr, o, margin):
                    n = o[2] + margin - rr[0]
                    if need is None or n > need:
                        need = n
        if need is None:
            return dx
        dx += max(need, 1.0)
    return dx


class _Col(object):
    __slots__ = ('w', 'x')

    def __init__(self):
        self.w = float(DOT_SIZE)
        self.x = 0.0


class _NewDot(object):
    __slots__ = ('cx', 'cy', 'node')

    def __init__(self, cx, cy):
        self.cx, self.cy, self.node = cx, cy, None


# --------------------------------------------------------------------------- layout
class _Layout(object):
    """Pure layout planner. Reads the graph, touches nothing."""

    def __init__(self, nodes):
        self.node = dict((n.fullName(), n) for n in nodes)
        self.names = sorted(self.node)
        self.size = dict((k, _size(n)) for k, n in self.node.items())
        self.ox = dict((k, n.xpos() + self.size[k][0] / 2.0) for k, n in self.node.items())
        self.oy = dict((k, n.ypos() + self.size[k][1] / 2.0) for k, n in self.node.items())
        self.is_dot = dict((k, n.Class() == 'Dot') for k, n in self.node.items())
        self._edges()
        self._ranks()
        self._owners()
        self._classify()
        self._slots()
        self._columns()
        self._rows()

    # graph -----------------------------------------------------------------
    def _edges(self):
        self.ins = dict((k, []) for k in self.names)    # b -> [(i, a)]
        self.outs = dict((k, []) for k in self.names)   # a -> [(b, i)]
        self.main = {}
        for b in self.names:
            n = self.node[b]
            self.main[b] = _main_index(n)
            if _hidden_input(n):
                continue  # hidden pipes are deliberate long links: leave them alone
            for i in range(n.inputs()):
                src = n.input(i)
                if src is None:
                    continue
                a = src.fullName()
                if a in self.node and a != b:
                    self.ins[b].append((i, a))
                    self.outs[a].append((b, i))

    def _input0(self, k):
        for i, a in self.ins[k]:
            if i == 0:
                return a
        return None

    def _ranks(self):
        indeg = dict((k, len(self.ins[k])) for k in self.names)
        ready = [k for k in self.names if indeg[k] == 0]
        order = []
        while ready:
            a = ready.pop()
            order.append(a)
            for b, _ in self.outs[a]:
                indeg[b] -= 1
                if indeg[b] == 0:
                    ready.append(b)
        if len(order) != len(self.names):
            raise RuntimeError('Tidy Tree: the selection contains a loop.')
        rank = {}
        for a in order:                      # as early as possible
            rank[a] = max([rank[s] + 1 for _, s in self.ins[a]] or [0])
        for a in reversed(order):            # then as late as possible, sources pinned on top
            if _is_source(self.node[a]):
                rank[a] = 0
            elif self.outs[a]:
                rank[a] = min(rank[b] for b, _ in self.outs[a]) - 1
        self.rank = rank

    def _owners(self):
        """Each node with outputs is 'owned' by one consumer: the one it sits above.
        Prefer a main-input consumer (vertical string), then whatever was closest."""
        self.owner = {}
        for a in self.names:
            outs = self.outs[a]
            if not outs:
                self.owner[a] = None
                continue
            ox, ra = self.ox[a], self.rank[a]
            self.owner[a] = min(outs, key=lambda e: (
                e[1] != self.main[e[0]], abs(self.ox[e[0]] - ox),
                self.rank[e[0]] - ra, e[0], e[1]))

    def _classify(self):
        """Existing Dots are reused as routing points instead of adding more,
        which also makes running the script twice stable."""
        self.kind = {}
        for k in self.names:
            kind = 'node'
            if self.is_dot[k]:
                src = self._input0(k)
                outs = self.outs[k]
                if src is not None and self.owner[src] != (k, 0):
                    kind = 'relay'      # sits on its source's bus lane
                elif len(outs) >= 2:
                    kind = 'branch'     # is a branch point itself
                elif len(outs) == 1 and outs[0][1] != self.main[outs[0][0]]:
                    kind = 'elbow'      # is the elbow of a side input
            self.kind[k] = kind

    def _lane_root(self, k):
        while self.kind[k] == 'relay':
            k = self._input0(k)
        return k

    def _slots(self):
        self.main_child, self.side, self.slot = {}, {}, {}
        for b in self.names:
            mc = None
            sides = {'left': [], 'right': []}
            for i, a in sorted(self.ins[b]):
                owned = self.owner[a] == (b, i)
                if i == self.main[b]:
                    if owned:
                        mc = a
                else:
                    sides[_side_of(self.node[b], i)].append((owned, a, i))
            self.main_child[b] = mc
            self.side[b] = sides
            for s, items in sides.items():
                for k, (_, a, i) in enumerate(items):
                    self.slot[(b, i)] = (s, k, len(items))

    # columns ---------------------------------------------------------------
    def _columns(self):
        self.col, self.vcol = {}, {}
        roots = [k for k in self.names if not self.outs[k]]
        roots.sort(key=lambda k: (self.ox[k], self.oy[k]))
        old = sys.getrecursionlimit()
        sys.setrecursionlimit(max(old, 5000))
        try:
            x = 0.0
            for r in roots:
                block, _ = self._tree(r)
                for c in block:
                    c.x = x + c.w / 2.0
                    x += c.w + COL_GAP
                x += TREE_GAP
        finally:
            sys.setrecursionlimit(old)

    def _tree(self, b):
        """Every column holds exactly one vertical string, so nothing can collide.
        Side branches get their own columns beside the string they feed."""
        chain = [b]
        while self.main_child[chain[-1]] is not None:
            chain.append(self.main_child[chain[-1]])
        block, anchor = [_Col()], 0
        for n in reversed(chain):            # top of the string first
            c = block[anchor]
            self.col[n] = c
            c.w = max(c.w, float(self.size[n][0]))
            for owned, a, i in self.side[n]['left']:     # nearest input closest
                sub = self._tree(a)[0] if owned else self._vcol(a, n, i)
                block = sub + block
                anchor += len(sub)
            for owned, a, i in self.side[n]['right']:
                sub = self._tree(a)[0] if owned else self._vcol(a, n, i)
                block = block + sub
        return block, anchor

    def _vcol(self, a, b, i):
        c = _Col()
        self.vcol[(a, b, i)] = c
        return [c]

    # rows ------------------------------------------------------------------
    def _rows(self):
        maxr = max(self.rank.values())
        band = [float(DOT_SIZE)] * (maxr + 1)
        for k in self.names:
            r = self.rank[k]
            if self.kind[k] == 'node':
                band[r] = max(band[r], float(self.size[k][1]))
            for s in ('left', 'right'):
                n = len(self.side[k][s])
                if n:
                    band[r] = max(band[r], 2.0 * (n - 1) * ELBOW_STAGGER + DOT_SIZE)

        # bus lanes live in the channel between two rows
        self.lane, count = {}, {}

        def add(r, k):
            count[r] = count.get(r, 0) + 1
            self.lane[k] = (r, count[r] - 1)

        for k in sorted((k for k in self.names
                         if not self.is_dot[k] and len(self.outs[k]) >= 2),
                        key=lambda k: self.col[k].x):
            add(self.rank[k], k)                       # branch Dot below a real node
        for k in sorted((k for k in self.names if self.kind[k] == 'branch'),
                        key=lambda k: self.col[k].x):
            add(self.rank[k] - 1, k)                   # existing branch Dot, above its row

        chan = {}
        for r in range(-1, maxr + 1):
            n = count.get(r, 0)
            base = ROW_GAP if 0 <= r < maxr else 0
            chan[r] = max(base, (n + 1) * LANE_GAP) if n else base
        self.lane_count = count
        self.chan_h = chan
        self.band_top, self.chan_top = {}, {}
        y = 0.0
        self.chan_top[-1] = y
        y += chan[-1]
        for r in range(maxr + 1):
            self.band_top[r] = y
            y += band[r]
            self.chan_top[r] = y
            y += chan[r]
        self.band = band

    def _center(self, k):
        r = self.rank[k]
        return self.band_top[r] + self.band[r] / 2.0

    def _lane_y(self, k):
        r, idx = self.lane[k]
        return self.chan_top[r] + (idx + 1) * self.chan_h[r] / (self.lane_count[r] + 1.0)

    def _elbow_y(self, b, i):
        # farthest input enters level with the node, nearer ones slightly higher:
        # nothing goes up and the elbows' lines don't cross each other
        s, k, n = self.slot[(b, i)]
        return self._center(b) - (n - 1 - k) * ELBOW_STAGGER

    # plan ------------------------------------------------------------------
    def plan(self):
        """Returns (positions {name: (cx, cy)}, new dots [_NewDot], links
        [(target, input, source)]) where targets/sources are names or _NewDots."""
        pos, dots, links = {}, [], []

        def new(cx, cy):
            d = _NewDot(cx, cy)
            dots.append(d)
            return d

        for k in self.names:
            kind = self.kind[k]
            if kind == 'elbow':
                b, i = self.outs[k][0]
                cy = self._elbow_y(b, i)
            elif kind == 'branch':
                cy = self._lane_y(k)
            elif kind == 'relay':
                cy = self._lane_y(self._lane_root(k))
            else:
                cy = self._center(k)
            pos[k] = (self.col[k].x, cy)

        bus, hubs = {}, {}
        for a in self.names:
            outs = self.outs[a]
            if not outs:
                continue
            if not self.is_dot[a] and len(outs) >= 2:
                hub = new(self.col[a].x, self._lane_y(a))
                links.append((hub, 0, a))
            else:
                hub = a
            own = self.owner[a]
            members = []
            for b, i in outs:
                is_main = i == self.main[b]
                if (b, i) == own:
                    if is_main:
                        if hub is not a:
                            links.append((b, i, hub))
                    elif self.kind[a] != 'elbow':
                        e = new(self.col[a].x, self._elbow_y(b, i))
                        links.append((e, 0, hub))
                        links.append((b, i, e))
                else:
                    y = self._lane_y(self._lane_root(a))
                    if is_main:
                        if self.is_dot[b]:
                            members.append(b)          # existing Dot sits on the lane
                        else:
                            d = new(self.col[b].x, y)
                            links.append((b, i, d))
                            members.append(d)
                    else:
                        c = self.vcol[(a, b, i)]
                        d = new(c.x, y)
                        e = new(c.x, self._elbow_y(b, i))
                        links.append((e, 0, d))
                        links.append((b, i, e))
                        members.append(d)
            # every Dot on a lane carries the same upstream node, so all buses that
            # share a lane are merged into one chain (no overlapping lines)
            bus.setdefault(self._lane_root(a), []).extend(members)
            hubs[a] = hub

        for root, members in bus.items():
            if not members:
                continue
            hub = hubs[root]
            hx = self.col[root].x

            def mx(m):
                return m.cx if isinstance(m, _NewDot) else pos[m][0]
            left = sorted([m for m in members if mx(m) < hx], key=lambda m: -mx(m))
            right = sorted([m for m in members if mx(m) >= hx], key=mx)
            for seq in (left, right):
                prev = hub
                for m in seq:
                    links.append((m, 0, prev))
                    prev = m
        return pos, dots, links


# --------------------------------------------------------------------------- main
def run():
    try:
        group = nuke.lastHitGroup()
    except Exception:
        group = nuke.root()
    with group:
        sel = [n for n in nuke.selectedNodes() if n.Class() not in IGNORE_CLASSES]
        if not sel:
            nuke.message('Tidy Tree: select some nodes first.')
            return
        undo = nuke.Undo()
        undo.begin('Tidy Tree')
        try:
            _tidy(sel)
        finally:
            undo.end()


def _tidy(sel):
    sel_names = set(n.fullName() for n in sel)
    orphans = [n for n in sel if _is_orphan(n)]
    orphan_names = set(n.fullName() for n in orphans)
    nodes = [n for n in sel if n.fullName() not in orphan_names]

    obstacles = []
    if AVOID_UNSELECTED:
        for n in nuke.allNodes():
            if n.fullName() in sel_names or n.Class() in ('BackdropNode', 'Root'):
                continue
            w, h = _size(n)
            obstacles.append((n.xpos(), n.ypos(), n.xpos() + w, n.ypos() + h))

    anchor_src = nodes or orphans
    ax = min(n.xpos() for n in anchor_src)
    ay = min(n.ypos() for n in anchor_src)

    moves = []          # (node, x, y)
    placed = []         # rects of everything laid out
    dots, links, lay = [], [], None
    if nodes:
        lay = _Layout(nodes)
        pos, dots, links = lay.plan()
        rects = []
        for k, (cx, cy) in pos.items():
            w, h = lay.size[k]
            rects.append((cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0))
        for d in dots:
            rects.append((d.cx - DOT_SIZE / 2.0, d.cy - DOT_SIZE / 2.0,
                          d.cx + DOT_SIZE / 2.0, d.cy + DOT_SIZE / 2.0))
        # connection lines also count as occupied space (thin boxes)
        center = dict((k, v) for k, v in pos.items())
        for d in dots:
            center[d] = (d.cx, d.cy)
        final = {}
        for b in lay.names:
            for i, a in lay.ins[b]:
                final[(b, i)] = a
        for target, i, source in links:
            final[(target, i)] = source
        lines = []
        for (b, i), a in final.items():
            (x0, y0), (x1, y1) = center[a], center[b]
            lines.append((min(x0, x1) - 1, min(y0, y1) - 1, max(x0, x1) + 1, max(y0, y1) + 1))
        ox = ax - min(r[0] for r in rects)
        oy = ay - min(r[1] for r in rects)
        rects = [(r[0] + ox, r[1] + oy, r[2] + ox, r[3] + oy) for r in rects]
        lines = [(r[0] + ox, r[1] + oy, r[2] + ox, r[3] + oy) for r in lines]
        dx = _shift_clear(rects + lines, obstacles, OBSTACLE_MARGIN)
        ox += dx
        placed = [(r[0] + dx, r[1], r[2] + dx, r[3]) for r in rects]
        for k, (cx, cy) in pos.items():
            w, h = lay.size[k]
            moves.append((lay.node[k], cx + ox - w / 2.0, cy + oy - h / 2.0))
        for d in dots:
            d.cx += ox
            d.cy += oy

    if orphans:
        orphans.sort(key=lambda n: (n.ypos(), n.xpos()))
        sizes = [_size(n) for n in orphans]
        per_row = int(math.ceil(math.sqrt(len(orphans))))
        cw = max(s[0] for s in sizes) + ORPHAN_GAP
        chh = max(s[1] for s in sizes) + ORPHAN_GAP
        sx = (max(r[2] for r in placed) + 3 * COL_GAP) if placed else ax
        sy = min(r[1] for r in placed) if placed else ay
        cells = []
        for idx, (n, (w, h)) in enumerate(zip(orphans, sizes)):
            x = sx + (idx % per_row) * cw
            y = sy + (idx // per_row) * chh
            cells.append((n, x, y, (x, y, x + w, y + h)))
        dx = _shift_clear([c[3] for c in cells], obstacles + placed, OBSTACLE_MARGIN)
        for n, x, y, _ in cells:
            moves.append((n, x + dx, y))

    # ---- apply: create Dots, insert them into the connections, move nodes
    for d in dots:
        d.node = nuke.nodes.Dot()
        d.node.setSelected(False)
        d.node.setXYpos(int(round(d.cx - DOT_SIZE / 2.0)), int(round(d.cy - DOT_SIZE / 2.0)))

    def ref(x):
        return x.node if isinstance(x, _NewDot) else lay.node[x]

    for target, i, source in links:
        ref(target).setInput(i, ref(source))
    for n, x, y in moves:
        n.setXYpos(int(round(x)), int(round(y)))

    for n in nuke.selectedNodes():
        n.setSelected(False)
    for n in (orphans if (SELECT_ORPHANS and orphans) else sel):
        n.setSelected(True)

    print('Tidy Tree: arranged {} node(s), added {} Dot(s), moved {} unconnected node(s){}.'
          .format(len(nodes), len(dots), len(orphans),
                  ' (left selected)' if SELECT_ORPHANS and orphans else ''))
