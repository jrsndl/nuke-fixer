"""End-to-end tests of NukePool + nuke_runner.py against a fake Nuke."""
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from nukefixer import paths  # noqa: E402
from nukefixer.runner import NukePool  # noqa: E402

FAKE = [sys.executable, os.path.join(HERE, "fake_nuke", "fake_nuke_exe.py"), "-t"]

USER_SCRIPT = """
import nuke
from nuke import state
state["text"] = state["text"] + "\\nFIXED"
nf.log("fixed " + nf.file)
"""


def read(path):
    with open(path) as fh:
        return fh.read()


def run(pool, files, timeout=60):
    events = []
    pool.start(files)
    t0 = time.time()
    while pool.is_active:
        events.extend(pool.poll())
        time.sleep(0.02)
        if time.time() - t0 > timeout:
            raise AssertionError("pool did not finish")
    events.extend(pool.poll())
    return events


def results(events):
    return {e[1]: e for e in events if e[0] == "result"}


class LaunchGuiTests(unittest.TestCase):
    def test_launch_gui_passes_args_and_script(self):
        from nukefixer.runner import launch_gui
        d = tempfile.mkdtemp()
        try:
            out = os.path.join(d, "argv.txt")
            rec = os.path.join(d, "rec.py")
            with open(rec, "w") as fh:
                fh.write("import sys\nopen(%r, 'w').write('|'.join(sys.argv[1:]))\n" % out)
            proc = launch_gui(sys.executable, "/shots/a b.nk", '"%s" --nukex' % rec)
            proc.wait(20)
            self.assertEqual(read(out), "--nukex|/shots/a b.nk")
        finally:
            shutil.rmtree(d, ignore_errors=True)


class PoolTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def make(self, name, text="script"):
        p = os.path.join(self.d, name).replace("\\", "/")
        with open(p, "w") as fh:
            fh.write(text)
        return p

    def pool(self, script=USER_SCRIPT, **kw):
        kw.setdefault("max_processes", 3)
        kw.setdefault("files_per_process", 4)
        kw.setdefault("hide_console", True)
        return NukePool(FAKE, paths.runner_script(), script, **kw)

    def test_happy_path_saves_and_backs_up(self):
        files = [self.make("s%02d.nk" % i) for i in range(10)]
        events = run(self.pool(), files)
        res = results(events)
        self.assertEqual(len(res), 10)
        self.assertTrue(all(e[2] and e[3] for e in res.values()))
        for f in files:
            self.assertTrue(read(f).endswith("FIXED"))
            self.assertEqual(read(f + ".safecopy"), "script")
        self.assertEqual(len([e for e in events if e[0] == "message"]), 10)
        self.assertTrue(all(e[6] == e[1] + ".safecopy" for e in res.values()))
        fin = [e for e in events if e[0] == "finished"][0][1]
        self.assertEqual((fin["ok"], fin["failed"], fin["not_run"]), (10, 0, 0))

    def test_backup_never_overwritten(self):
        f = self.make("a.nk")
        with open(f + ".safecopy", "w") as fh:
            fh.write("original")
        run(self.pool(), [f])
        self.assertEqual(read(f + ".safecopy"), "original")

    def test_dry_run_and_skip_save(self):
        f1, f2 = self.make("a.nk"), self.make("b.nk")
        ev = run(self.pool(dry_run=True), [f1])
        self.assertIsNone(results(ev)[f1][6])          # dry run: no backup
        self.assertEqual(read(f1), "script")
        self.assertFalse(os.path.exists(f1 + ".safecopy"))
        ev = run(self.pool(script=USER_SCRIPT + "\nnf.skip_save = True\n"), [f2])
        self.assertEqual(read(f2), "script")
        r = results(ev)[f2]
        self.assertTrue(r[2])
        self.assertFalse(r[3])

    def test_errors_crash_and_badload(self):
        good = [self.make("g%d.nk" % i) for i in range(5)]
        crash = self.make("crash.nk", "CRASH")
        bad = self.make("bad.nk", "BADLOAD")
        missing = os.path.join(self.d, "missing.nk").replace("\\", "/")
        files = good[:2] + [crash, bad, missing] + good[2:]
        ev = run(self.pool(max_processes=2, files_per_process=10), files)
        res = results(ev)
        self.assertEqual(set(res), set(files))
        self.assertFalse(res[crash][2])
        self.assertIn("exited unexpectedly", res[crash][4])
        self.assertFalse(res[bad][2])
        self.assertIn("SomeMissingPlugin", res[bad][4])
        self.assertEqual(read(bad), "BADLOAD")          # not saved
        self.assertFalse(res[missing][2])
        for g in good:
            self.assertTrue(res[g][2], g)

    def test_saved_file_has_real_root_name_and_no_temp_left(self):
        f = self.make("a.nk")
        run(self.pool(), [f])
        text = read(f)
        self.assertTrue(text.startswith("#root %s\n" % f), text)
        self.assertNotIn("nukefixer_tmp", text)
        self.assertEqual(sorted(os.listdir(self.d)), ["a.nk", "a.nk.safecopy"])

    def test_identical_save_is_reported_not_saved(self):
        f = os.path.join(self.d, "same.nk").replace("\\", "/")
        f = self.make("same.nk", "#root %s\nSAMESAVE" % f)      # real .nk files contain their path
        before = read(f)
        ev = run(self.pool(), [f])
        r = results(ev)[f]
        self.assertTrue(r[2])
        self.assertFalse(r[3])
        self.assertIn("identical", r[4])
        self.assertEqual(read(f), before)
        self.assertFalse(any("nukefixer_tmp" in n for n in os.listdir(self.d)))

    def test_save_that_writes_nothing_is_a_failure(self):
        f = self.make("nosave.nk", "NOSAVE")
        ev = run(self.pool(), [f])
        r = results(ev)[f]
        self.assertFalse(r[2])
        self.assertIn("did not write", r[4])
        self.assertEqual(read(f), "NOSAVE")

    def test_user_script_exception(self):
        f = self.make("a.nk")
        ev = run(self.pool(script="raise ValueError('nope')"), [f])
        r = results(ev)[f]
        self.assertFalse(r[2])
        self.assertIn("ValueError: nope", r[4])
        self.assertEqual(read(f), "script")

    def test_timeout_kills_and_continues(self):
        hang = self.make("hang.nk", "HANG")
        ok = [self.make("ok%d.nk" % i) for i in range(3)]
        ev = run(self.pool(max_processes=1, files_per_process=10, timeout_per_file=2), [hang] + ok)
        res = results(ev)
        self.assertIn("Timed out", res[hang][4])
        self.assertTrue(all(res[o][2] for o in ok))

    def test_nuke_never_starts_is_fatal(self):
        files = [self.make("s%d.nk" % i) for i in range(6)]
        os.environ["FAKE_NUKE_FAIL_START"] = "1"
        try:
            ev = run(self.pool(max_processes=1, max_start_failures=3), files)
        finally:
            del os.environ["FAKE_NUKE_FAIL_START"]
        self.assertTrue(any(e[0] == "fatal" and "no license" in e[1] for e in ev))
        fin = [e for e in ev if e[0] == "finished"][0][1]
        self.assertEqual(fin["ok"], 0)

    def test_missing_executable_is_fatal(self):
        pool = NukePool(["/no/such/Nuke13.2", "-t"], paths.runner_script(), USER_SCRIPT)
        ev = run(pool, [self.make("a.nk")])
        self.assertTrue(any(e[0] == "fatal" for e in ev))

    def test_graceful_stop(self):
        files = [self.make("s%02d.nk" % i) for i in range(20)]
        pool = self.pool(script=USER_SCRIPT + "\nimport time; time.sleep(0.2)\n",
                         max_processes=2, files_per_process=10)
        pool.start(files)
        events = []
        stopped = False
        t0 = time.time()
        while pool.is_active and time.time() - t0 < 60:
            events.extend(pool.poll())
            if not stopped and any(e[0] == "result" for e in events):
                pool.stop()
                stopped = True
            time.sleep(0.02)
        events.extend(pool.poll())
        fin = [e for e in events if e[0] == "finished"][0][1]
        self.assertGreater(fin["not_run"], 0)
        self.assertEqual(fin["failed"], 0)

    def test_kill(self):
        files = [self.make("s%02d.nk" % i) for i in range(6)]
        pool = self.pool(script="import time; time.sleep(30)", max_processes=2)
        pool.start(files)
        events = []
        t0 = time.time()
        while not any(e[0] == "start" for e in events):
            events.extend(pool.poll())
            time.sleep(0.02)
        pool.stop(kill=True)
        while pool.is_active and time.time() - t0 < 30:
            events.extend(pool.poll())
            time.sleep(0.02)
        self.assertLess(time.time() - t0, 20)
        killed = [e for e in events if e[0] == "result"]
        self.assertTrue(killed and all("Killed by user" in e[4] for e in killed))
        for f in files:
            self.assertEqual(read(f), "script")


if __name__ == "__main__":
    unittest.main()
