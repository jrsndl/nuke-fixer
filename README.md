# NukeFixer

Batch-apply a Python script to many Nuke scripts: find `.nk` files across a
project, pick the first / last / all versions per folder, queue them, and run
your script on every one of them in parallel Nuke processes.

## Run

```
pip install -r requirements.txt     # PySide6 (PySide2 5.15 also works)
python nuke_fixer.py                 # or run.bat
```

Build a standalone exe with `build.bat` (PyInstaller, `NukeFixer.spec`).
The result is `dist/NukeFixer/NukeFixer.exe` with the example `scripts/`
folder next to it.

## Workflow

1. **Find Nuke Scripts** - set the search root, an "only if contains" path
   filter (e.g. `/work/comp/`), a file pattern (`*_comp_v???.nk`) and the
   version regex (`_v(\d+)\.nk$` - the first group is the version, compared
   as a number). Searching runs in the background and starts shortly after
   you stop typing (or press Enter / Search). Pick First / Last / All
   versions, check the rows you want and press **Add to Queue**.
2. **Python Script** - write or **Load...** the script to run (the dialog
   opens in `scripts/`, which has examples). **Check Syntax** before running.
3. **Queue** - everything that will be processed, with status, size,
   modification date, processing time and the error message (hover it for
   the full traceback). Save / load the queue (JSON, or a plain text list of
   paths), export a CSV report, retry failed scripts. The queue is autosaved
   and restored on the next start.
   **Roll Back...** undoes a run: for the selected (or all Done) scripts it
   deletes the modified script and renames its backup back to the original
   name, in one step. Scripts edited after NukeFixer saved them are flagged
   and can be skipped; scripts without a backup are never touched. Rolled-back
   scripts return to Pending.
   **Open in Nuke** (Queue and Find tabs, also in the right-click menu) opens
   the selected scripts in interactive Nuke, one session per script; it asks
   first when more than 5 would start. Extra launch arguments (e.g.
   `--nukex`) are set on the Settings tab.
4. **Execute** (bottom) - the button says how many Nuke scripts will be
   modified. While running it shows progress, elapsed time, seconds per
   script and an ETA that is recalculated as scripts finish. Click it again
   (or Ctrl+.) to stop: either finish the scripts in progress or kill Nuke.
5. **Log** - everything that happened, filterable by verbosity and text;
   raw Nuke output can be shown too. Also written to `NukeFixer.log`.
6. **Settings** - Nuke executable, parallel processes, scripts per process,
   timeouts, backups, dry run, search excludes/threads, log level.

## Writing a script

Your script runs inside Nuke after each Nuke script is opened:

| name | meaning |
| --- | --- |
| `nuke` | the Nuke module |
| `nf.file` | path of the script being processed |
| `nf.dry_run` | `True` when Dry run is on (nothing is saved) |
| `nf.skip_save = True` | don't save this script (e.g. nothing changed) |
| `nf.log("text")` | message in the Log tab |

* Raise an exception to mark the script **failed** - it is not saved.
* Don't call `nuke.scriptSave()` / `scriptClose()` - NukeFixer does that.
* A backup `script.nk.safecopy` is made before saving; an existing backup is
  never overwritten, so it always holds the original.
* A script that fails to *load* (missing plugins...) is never saved, so
  unknown nodes can't be silently lost.
* One Nuke process handles several scripts in a row (faster). If your script
  leaves global state behind, set *Scripts per Nuke process* to 1.

See `scripts/example_*.py`.

## How it runs

`Execute` starts up to *Parallel Nuke processes* instances of
`Nuke -t nukefixer/nuke_runner.py job.json` (`-t` uses a render licence;
`-ti` / interactive licence is an option). Each process gets a batch of
scripts and reports every result back. A hung script is killed after the
per-script timeout, a crashed Nuke marks only its current script as failed
and the rest of its batch goes back to the queue, and if Nuke can't start at
all (path, licence) the run is aborted after three attempts.

## Development

```
nuke_fixer.py            entry point
nukefixer/               the application package
    scanner.py versions.py queue_io.py eta.py runner.py   Qt-free core
    nuke_runner.py       executed inside Nuke (py2.7 / py3 compatible)
    *_tab.py main_window.py models.py                     Qt GUI
scripts/                 example user scripts
tests/                   python -m unittest discover -s tests -t .
```

The tests run the real process pool against a fake Nuke (`tests/fake_nuke`),
including crashes, hangs, licence failures, stop and kill.
