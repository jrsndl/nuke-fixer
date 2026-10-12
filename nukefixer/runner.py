"""NukePool - run the user script over many Nuke scripts in parallel (Qt-free).

* At most ``max_processes`` Nuke processes at a time (licences / RAM).
* Each process handles a chunk of up to ``files_per_process`` scripts, so the
  Nuke start-up cost is paid once per chunk, not once per script. Chunks are
  sized so all processes get work even when few scripts are left.
* Per-script timeout and start-up / idle timeout kill hung Nukes.
* If a Nuke process crashes, the script it was working on is marked failed
  and the rest of its chunk goes back to the front of the queue.
* If Nuke repeatedly exits without processing anything (bad path, no
  licence...) the run is aborted instead of looping forever.
* Graceful stop (finish the current scripts) and hard kill.

The GUI calls ``poll()`` from a timer; all state changes happen there, so
there is no locking in the GUI. Reader threads only push stdout lines into a
thread-safe queue.
"""
import io
import json
import logging
import math
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import deque

log = logging.getLogger("nukefixer.runner")

CREATE_NO_WINDOW = 0x08000000

IDLE, RUNNING, STOPPING, FINISHED = "idle", "running", "stopping", "finished"


class _Job(object):
    def __init__(self, jid, files, proc, job_file, results_file):
        self.id = jid
        self.files = list(files)
        self.proc = proc
        self.job_file = job_file
        self.results_file = results_file
        self.started_at = time.time()
        self.last_activity = self.started_at
        self.current = None
        self.current_started = None
        self.started_files = set()
        self.reported = set()
        self.tail = deque(maxlen=40)
        self.eof = False
        self.exit_seen = None
        self.kill_reason = None
        self.user_killed = False


class NukePool(object):
    def __init__(self, command, runner_script, user_script_text, script_dir=None,
                 max_processes=2, files_per_process=10, timeout_per_file=600,
                 startup_timeout=300, make_backup=True, backup_suffix=".safecopy",
                 dry_run=False, hide_console=True, env=None, max_start_failures=3):
        """command: program + leading args, e.g. ['C:/.../Nuke13.2.exe', '-t']."""
        self.command = list(command)
        self.runner_script = runner_script
        self.user_script_text = user_script_text
        self.script_dir = script_dir
        self.max_processes = max(1, int(max_processes))
        self.files_per_process = max(1, int(files_per_process))
        self.timeout_per_file = max(0, int(timeout_per_file))
        self.startup_timeout = max(0, int(startup_timeout))
        self.make_backup = bool(make_backup)
        self.backup_suffix = backup_suffix or ".safecopy"
        self.dry_run = bool(dry_run)
        self.hide_console = bool(hide_console)
        self.env = env
        self.max_start_failures = max(1, int(max_start_failures))

        self.state = IDLE
        self.pending = deque()
        self.jobs = {}
        self.run_dir = None
        self.stop_file = None
        self.user_script_file = None
        self.ok_count = 0
        self.fail_count = 0
        self.total = 0
        self.fatal_error = None
        self._lines = queue.Queue()
        self._events = []
        self._next_id = 1
        self._start_failures = 0
        self._started_at = None

    # ------------------------------------------------------------------ api
    @property
    def running_count(self):
        return len(self.jobs)

    @property
    def is_active(self):
        return self.state in (RUNNING, STOPPING)

    def start(self, files):
        if self.state != IDLE:
            raise RuntimeError("pool already started")
        if not os.path.isfile(self.runner_script):
            raise IOError("Runner script not found: %s" % self.runner_script)
        self.run_dir = tempfile.mkdtemp(prefix="nukefixer_")
        self.stop_file = os.path.join(self.run_dir, "STOP")
        self.user_script_file = os.path.join(self.run_dir, "user_script.py")
        with io.open(self.user_script_file, "w", encoding="utf-8") as fh:
            fh.write(self.user_script_text)
        self.pending = deque(files)
        self.total = len(self.pending)
        self.state = RUNNING
        self._started_at = time.time()
        log.info("Run started: %d script(s), up to %d Nuke process(es), %d script(s) per process%s",
                 self.total, self.max_processes, self.files_per_process,
                 " [DRY RUN]" if self.dry_run else "")
        self._spawn()

    def stop(self, kill=False):
        """Graceful: running Nukes finish their current script. kill: now."""
        if self.state not in (RUNNING, STOPPING):
            return
        self.pending.clear()
        try:
            io.open(self.stop_file, "w").close()
        except OSError:
            pass
        self.state = STOPPING
        if kill:
            for job in self.jobs.values():
                job.user_killed = True
                if job.kill_reason is None:
                    job.kill_reason = "Killed by user"
                self._kill(job)

    def poll(self):
        """Advance the state machine. Returns a list of event tuples:

        ('start', path)
        ('result', path, ok, saved, message, duration, backup_path_or_None)
        ('message', path, text)            user script nf.log()
        ('output', path_or_None, line)     raw Nuke output
        ('log', level, text)
        ('fatal', text)
        ('finished', summary_dict)
        """
        now = time.time()
        while True:
            try:
                jid, line = self._lines.get_nowait()
            except queue.Empty:
                break
            job = self.jobs.get(jid)
            if job is None:
                continue
            if line is None:
                job.eof = True
            else:
                self._handle_line(job, line, now)

        for job in list(self.jobs.values()):
            self._check_timeouts(job, now)
            rc = job.proc.poll()
            if rc is None:
                continue
            if job.exit_seen is None:
                job.exit_seen = now
            # wait for the reader to hit EOF (all output consumed), but don't
            # hang forever if a child process kept the pipe open
            if job.eof or now - job.exit_seen > 3.0:
                self._finish_job(job, rc)

        if self.state == RUNNING:
            self._spawn()
        if self.state in (RUNNING, STOPPING) and not self.jobs and \
                (self.state == STOPPING or not self.pending):
            self._finish()

        events, self._events = self._events, []
        return events

    # ------------------------------------------------------------ internals
    def _emit(self, *event):
        self._events.append(event)

    def _spawn(self):
        while self.state == RUNNING and self.pending and len(self.jobs) < self.max_processes:
            free = self.max_processes - len(self.jobs)
            size = max(1, min(self.files_per_process, int(math.ceil(len(self.pending) / float(free)))))
            files = [self.pending.popleft() for _ in range(min(size, len(self.pending)))]
            jid = self._next_id
            self._next_id += 1
            job_file = os.path.join(self.run_dir, "job_%04d.json" % jid)
            results_file = os.path.join(self.run_dir, "job_%04d.results" % jid)
            with io.open(job_file, "w", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "files": files,
                    "user_script": self.user_script_file,
                    "script_dir": self.script_dir,
                    "results_file": results_file,
                    "stop_file": self.stop_file,
                    "make_backup": self.make_backup,
                    "backup_suffix": self.backup_suffix,
                    "dry_run": self.dry_run,
                }, indent=1))
            cmd = self.command + [self.runner_script, job_file]
            env = dict(self.env if self.env is not None else os.environ)
            env["PYTHONUNBUFFERED"] = "1"
            kwargs = {}
            if sys.platform.startswith("win") and self.hide_console:
                kwargs["creationflags"] = CREATE_NO_WINDOW
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL, cwd=self.run_dir, env=env, **kwargs)
            except OSError as exc:
                self.pending.extendleft(reversed(files))
                self._fatal("Cannot start Nuke (%s): %s" % (self.command[0] if self.command else "?", exc))
                return
            job = _Job(jid, files, proc, job_file, results_file)
            self.jobs[jid] = job
            reader = threading.Thread(target=self._reader, args=(jid, proc.stdout),
                                      name="nuke-reader-%d" % jid)
            reader.daemon = True
            reader.start()
            self._emit("log", logging.DEBUG, "Nuke #%d started (pid %d) with %d script(s): %s"
                       % (jid, proc.pid, len(files), " ".join('"%s"' % c for c in cmd)))

    def _reader(self, jid, stream):
        try:
            for raw in iter(stream.readline, b""):
                self._lines.put((jid, raw.decode("utf-8", "replace").rstrip("\r\n")))
        except (OSError, ValueError):
            pass
        finally:
            try:
                stream.close()
            except OSError:
                pass
            self._lines.put((jid, None))

    def _handle_line(self, job, line, now):
        job.last_activity = now
        tag, _, payload = line.partition(" ")
        if tag.startswith("NF_"):
            try:
                data = json.loads(payload) if payload else {}
            except ValueError:
                data = None
            if isinstance(data, dict):
                if tag == "NF_START":
                    self._on_start(job, data.get("file"), now)
                    return
                if tag == "NF_RESULT":
                    self._report(job, data)
                    return
                if tag == "NF_MSG":
                    self._emit("message", data.get("file"), data.get("text", ""))
                    return
                if tag == "NF_READY":
                    self._emit("log", logging.DEBUG, "Nuke #%d ready (pid %s, Nuke %s)"
                               % (job.id, data.get("pid"), data.get("nuke")))
                    return
                if tag == "NF_STOPPED":
                    self._emit("log", logging.DEBUG, "Nuke #%d stopped on request" % job.id)
                    return
        job.tail.append(line)
        self._emit("output", job.current, line)

    def _on_start(self, job, path, now):
        if not path or path in job.started_files:
            return
        job.current = path
        job.current_started = now
        job.started_files.add(path)
        self._start_failures = 0
        self._emit("start", path)

    def _report(self, job, data):
        path = data.get("file")
        if not path or path in job.reported:
            return
        job.reported.add(path)
        job.started_files.add(path)
        if job.current == path:
            job.current = None
        ok = bool(data.get("ok"))
        if ok:
            self.ok_count += 1
        else:
            self.fail_count += 1
        self._emit("result", path, ok, bool(data.get("saved")), data.get("message", ""),
                   data.get("duration"), data.get("backup"))

    def _check_timeouts(self, job, now):
        if job.kill_reason is not None or job.proc.poll() is not None:
            return
        if job.current and self.timeout_per_file and now - job.current_started > self.timeout_per_file:
            job.kill_reason = "Timed out after %d s" % self.timeout_per_file
        elif not job.current and self.startup_timeout and now - job.last_activity > self.startup_timeout:
            job.kill_reason = "Nuke made no progress for %d s (start-up / idle timeout)" % self.startup_timeout
        if job.kill_reason:
            self._emit("log", logging.WARNING, "Nuke #%d: %s - killing it" % (job.id, job.kill_reason))
            self._kill(job)

    def _kill(self, job):
        try:
            job.proc.kill()
        except OSError:
            pass

    def _reconcile_results_file(self, job):
        """Results file is the source of truth if stdout lines got lost."""
        try:
            with io.open(job.results_file, "r", encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except (IOError, OSError):
            return
        for line in lines:
            tag, _, payload = line.partition(" ")
            try:
                data = json.loads(payload)
            except ValueError:
                continue
            if tag == "NF_START":
                job.started_files.add(data.get("file"))
                if data.get("file") not in job.reported:
                    job.current = data.get("file")
            elif tag == "NF_RESULT":
                self._report(job, data)

    def _finish_job(self, job, rc):
        del self.jobs[job.id]
        self._reconcile_results_file(job)
        tail = "\n".join(list(job.tail)[-15:])

        if job.current and job.current not in job.reported:
            reason = job.kill_reason or ("Nuke exited unexpectedly (exit code %s) while processing this script." % rc)
            if tail and not job.user_killed:
                reason += "\n--- last Nuke output ---\n" + tail
            self._report(job, {"file": job.current, "ok": False, "saved": False,
                               "message": reason, "duration": time.time() - (job.current_started or job.started_at)})

        unstarted = [f for f in job.files if f not in job.started_files]
        if unstarted and self.state == RUNNING:
            self.pending.extendleft(reversed(unstarted))

        if not job.started_files and job.files and not job.user_killed:
            self._start_failures += 1
            self._emit("log", logging.WARNING,
                       "Nuke #%d exited (code %s) without processing any script (%d/%d)%s"
                       % (job.id, rc, self._start_failures, self.max_start_failures,
                          (":\n" + tail) if tail else ""))
            if self._start_failures >= self.max_start_failures:
                self._fatal("Nuke exited %d times in a row without processing any script. "
                            "Check the Nuke executable, licences and arguments.\n\nLast output:\n%s"
                            % (self._start_failures, tail or "(none)"))
        elif rc not in (0, None) and not job.user_killed and not job.kill_reason:
            self._emit("log", logging.DEBUG, "Nuke #%d exited with code %s" % (job.id, rc))
        else:
            self._emit("log", logging.DEBUG, "Nuke #%d finished (exit code %s)" % (job.id, rc))

    def _fatal(self, message):
        if self.fatal_error is None:
            self.fatal_error = message
            self._emit("fatal", message)
        self.stop(kill=True)

    def _finish(self):
        self.state = FINISHED
        elapsed = time.time() - (self._started_at or time.time())
        summary = {
            "total": self.total,
            "ok": self.ok_count,
            "failed": self.fail_count,
            "not_run": self.total - self.ok_count - self.fail_count,
            "elapsed": elapsed,
            "fatal": self.fatal_error,
        }
        if self.run_dir:
            shutil.rmtree(self.run_dir, ignore_errors=True)
        self._emit("finished", summary)


def split_args(text):
    """Split a user-typed argument string (quotes allowed)."""
    import shlex
    if not text or not text.strip():
        return []
    is_win = sys.platform.startswith("win")
    return [a.strip('"') if is_win else a for a in shlex.split(text, posix=not is_win)]


def build_command(nuke_executable, interactive_license=False, extra_args=""):
    """[exe, '-t' | '-ti', *extra]. -t uses a render licence (nuke_r)."""
    return [nuke_executable, "-ti" if interactive_license else "-t"] + split_args(extra_args)


def launch_gui(nuke_executable, script_path, extra_args=""):
    """Open one script in an interactive Nuke that outlives NukeFixer."""
    cmd = [nuke_executable] + split_args(extra_args) + [script_path]
    kwargs = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
              "stderr": subprocess.DEVNULL, "close_fds": True}
    if sys.platform.startswith("win"):
        # own console (like starting Nuke from the Start menu) + own process group,
        # so closing NukeFixer never takes Nuke down with it
        kwargs["creationflags"] = 0x00000010 | 0x00000200   # CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    return subprocess.Popen(cmd, **kwargs)
