"""Tests for the Qt-free core. Run:  python -m unittest discover -s tests -v"""
import os
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nukefixer import config, eta, queue_io, scanner, versions  # noqa: E402


def touch(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        for shot in ("sh010", "sh020"):
            for v in (1, 2, 10):
                touch(os.path.join(self.root, shot, "work", "comp", "%s_comp_v%03d.nk" % (shot, v)))
            touch(os.path.join(self.root, shot, "work", "comp", "renders", "%s_comp_v999.nk" % shot))
            touch(os.path.join(self.root, shot, "work", "light", "%s_comp_v001.nk" % shot))
            touch(os.path.join(self.root, shot, "work", "comp", "%s_comp_v001.nk~" % shot))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_scan_filters_and_excludes(self):
        res = scanner.scan(self.root, "*_comp_v???.nk", contains="/work/comp/",
                           excludes=["renders"], threads=4)
        names = sorted(f.name for f in res.files)
        self.assertEqual(len(names), 6)
        self.assertNotIn("sh010_comp_v999.nk", names)
        self.assertTrue(all(f.size == 1 and f.mtime for f in res.files))
        self.assertFalse(res.cancelled)

    def test_scan_without_exclude_finds_renders(self):
        res = scanner.scan(self.root, "*_comp_v???.nk", contains="/work/comp/")
        self.assertEqual(len(res.files), 8)

    def test_max_depth(self):
        res = scanner.scan(self.root, "*.nk", max_depth=1)
        self.assertEqual(res.files, [])

    def test_bad_inputs(self):
        with self.assertRaises(ValueError):
            scanner.scan("", "*.nk")
        with self.assertRaises(ValueError):
            scanner.scan(os.path.join(self.root, "nope"), "*.nk")
        with self.assertRaises(ValueError):
            scanner.scan(self.root, "  ")

    def test_cancel(self):
        ev = threading.Event()
        ev.set()
        res = scanner.scan(self.root, "*.nk", cancel=ev)
        self.assertTrue(res.cancelled)


class VersionTests(unittest.TestCase):
    def files(self, *names, folder="/p/sh010/work/comp"):
        return [scanner.FoundFile(folder + "/" + n) for n in names]

    def test_numeric_sort_and_modes(self):
        rx, err = versions.compile_version_regex(r"_v(\d+)\.nk$")
        self.assertIsNone(err)
        fs = self.files("a_v99.nk", "a_v100.nk", "a_v002.nk", "notes.nk")
        last, unmatched = versions.select_versions(fs, rx, "last")
        self.assertEqual([c.file.name for c in last], ["a_v100.nk"])
        self.assertEqual(unmatched, 1)
        first, _ = versions.select_versions(fs, rx, "first")
        self.assertEqual(first[0].version, "002")
        allv, _ = versions.select_versions(fs, rx, "all")
        self.assertEqual([c.version for c in allv], ["002", "99", "100"])

    def test_folder_without_match_does_not_crash(self):
        rx, _ = versions.compile_version_regex(r"_v(\d+)\.nk$")
        out, unmatched = versions.select_versions(self.files("foo.nk", "bar.nk"), rx, "last")
        self.assertEqual(out, [])
        self.assertEqual(unmatched, 2)

    def test_regex_errors(self):
        self.assertIsNotNone(versions.compile_version_regex("_v(\\d+")[1])
        self.assertIsNotNone(versions.compile_version_regex("_v\\d+")[1])   # no group
        self.assertIsNotNone(versions.compile_version_regex("")[1])

    def test_legacy_regex_still_works(self):
        rx, err = versions.compile_version_regex(r".*_v(\d{3}).nk")
        self.assertIsNone(err)
        out, _ = versions.select_versions(self.files("x_v001.nk", "x_v003.nk"), rx, "last")
        self.assertEqual(out[0].version, "003")


class QueueIOTests(unittest.TestCase):
    def test_roundtrip_and_running_reset(self):
        d = tempfile.mkdtemp()
        try:
            items = [queue_io.QueueItem("C:\\a\\b.nk", status=queue_io.RUNNING, size=3),
                     queue_io.QueueItem("/x/y.nk", enabled=False, status=queue_io.FAILED, message="boom")]
            p = os.path.join(d, "q.json")
            queue_io.save_queue(p, items)
            back = queue_io.load_queue(p)
            self.assertEqual(back[0].path, "C:/a/b.nk")
            self.assertEqual(back[0].status, queue_io.PENDING)
            self.assertFalse(back[1].enabled)
            self.assertEqual(back[1].message, "boom")
            txt = os.path.join(d, "q.txt")
            with open(txt, "w") as fh:
                fh.write("# comment\n/a/one.nk\n\n\"/a/two.nk\"\n")
            self.assertEqual([i.path for i in queue_io.load_queue(txt)], ["/a/one.nk", "/a/two.nk"])
            queue_io.export_csv(os.path.join(d, "r.csv"), back)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_human(self):
        self.assertEqual(queue_io.human_size(512), "512 B")
        self.assertEqual(queue_io.human_size(2048), "2.0 KB")
        self.assertEqual(queue_io.human_time(3725), "1:02:05")
        self.assertEqual(queue_io.human_time(65), "1:05")


class RollbackTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def item(self, name, modified="fixed", backup="original", status=queue_io.DONE, suffix=".safecopy"):
        path = os.path.join(self.d, name)
        touch(path, modified)
        if backup is not None:
            touch(path + suffix, backup)
        it = queue_io.QueueItem(path, status=status)
        it.refresh_stat()
        return it

    def test_plan_and_rollback(self):
        ok = self.item("ok.nk")
        nobak = self.item("nobak.nk", backup=None)
        pending = self.item("pending.nk", status=queue_io.PENDING)
        changed = self.item("changed.nk")
        changed.mtime -= 60                       # file got edited after the run
        custom = self.item("custom.nk", suffix=".bak")
        custom.backup = custom.path + ".bak"      # backup path reported by the run
        plan = {it.name: v for it, _, v in queue_io.plan_rollback(
            [ok, nobak, pending, changed, custom], ".safecopy")}
        self.assertEqual(plan, {"ok.nk": queue_io.RB_OK, "nobak.nk": queue_io.RB_NO_BACKUP,
                                "pending.nk": queue_io.RB_NOT_DONE, "changed.nk": queue_io.RB_CHANGED,
                                "custom.nk": queue_io.RB_OK})
        good, msg = queue_io.rollback_file(ok.path, ok.path + ".safecopy")
        self.assertTrue(good, msg)
        with open(ok.path) as fh:
            self.assertEqual(fh.read(), "original")
        self.assertFalse(os.path.exists(ok.path + ".safecopy"))
        bad, msg = queue_io.rollback_file(nobak.path, nobak.path + ".safecopy")
        self.assertFalse(bad)
        with open(nobak.path) as fh:
            self.assertEqual(fh.read(), "fixed")       # untouched

    def test_backup_roundtrips_in_queue_file(self):
        it = queue_io.QueueItem("/a/b.nk", backup="/a/b.nk.safecopy")
        p = os.path.join(self.d, "q.json")
        queue_io.save_queue(p, [it])
        self.assertEqual(queue_io.load_queue(p)[0].backup, "/a/b.nk.safecopy")


class EtaTests(unittest.TestCase):
    def test_eta(self):
        t = eta.EtaTracker()
        t.reset(10, now=0)
        self.assertIsNone(t.eta(now=5))
        for i in range(1, 6):
            t.add_done(now=i * 2.0)
        est = t.eta(now=10.0)
        self.assertAlmostEqual(est, 10.0, delta=1.0)    # 5 left at 0.5/s
        for i in range(6, 11):
            t.add_done(now=i * 2.0)
        self.assertEqual(t.eta(now=20), 0.0)


class ConfigTests(unittest.TestCase):
    def test_coerce(self):
        self.assertTrue(config.coerce("true", False))
        self.assertFalse(config.coerce("0", True))
        self.assertEqual(config.coerce("3", 1), 3)
        self.assertEqual(config.coerce("junk", 7), 7)
        self.assertEqual(config.coerce(["a", "b"], ""), "a, b")
        self.assertEqual(config.coerce(None, "d"), "d")
        self.assertEqual(config.legacy_version_mode("0", "1", "0"), "last")
        self.assertEqual(config.legacy_version_mode("1", "0", "0"), "first")
        self.assertEqual(config.parse_list("a, b;c\n d"), ["a", "b", "c", "d"])


if __name__ == "__main__":
    unittest.main()
