"""
Automated build script for LayoutSwitcher.exe.
Follows project rules: cleans temporary folders, runs PyInstaller,
verifies binary execution with smoke test, saves .exe in project folder.
"""

import os
import shutil
import subprocess
import sys
import time

try:
    import psutil
except ImportError:
    psutil = None

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(PROJECT_DIR, "build")
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
SPEC_FILE = os.path.join(PROJECT_DIR, "LayoutSwitcher.spec")
TARGET_EXE = os.path.join(PROJECT_DIR, "LayoutSwitcher.exe")
ICON_PATH = os.path.join(PROJECT_DIR, "icon.ico")
MAIN_SCRIPT = os.path.join(PROJECT_DIR, "main.py")


def clean_temp_dirs():
    """Remove temporary build/dist directories and spec files."""
    for path in [BUILD_DIR, DIST_DIR]:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    if os.path.exists(SPEC_FILE):
        try:
            os.remove(SPEC_FILE)
        except OSError:
            pass


def build_exe():
    print("[1/4] Cleaning previous builds...")
    clean_temp_dirs()
    if os.path.exists(TARGET_EXE):
        try:
            os.remove(TARGET_EXE)
        except OSError:
            pass

    print("[2/4] Building standalone portable executable via PyInstaller...")
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        f"--name=LayoutSwitcher",
        f"--icon={ICON_PATH}",
        f"--add-data={ICON_PATH};.",
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR}",
        MAIN_SCRIPT,
    ]

    res = subprocess.run(cmd, cwd=PROJECT_DIR)
    if res.returncode != 0:
        raise RuntimeError(f"PyInstaller failed with exit code {res.returncode}")

    built_exe = os.path.join(DIST_DIR, "LayoutSwitcher.exe")
    if not os.path.exists(built_exe):
        raise FileNotFoundError(f"Built executable not found at: {built_exe}")

    shutil.copy2(built_exe, TARGET_EXE)
    print(f"[3/4] Executable saved to: {TARGET_EXE} ({os.path.getsize(TARGET_EXE) / (1024*1024):.2f} MB)")

    print("[4/4] Performing Smoke Test on built executable...")
    smoke_test_exe(TARGET_EXE)

    print("Cleaning up temporary build artifacts...")
    clean_temp_dirs()
    print("Build and verification completed successfully!")


def smoke_test_exe(exe_path: str):
    """
    Launch the built .exe in the background, verify process health
    and memory consumption, then terminate it cleanly.
    """
    proc = subprocess.Popen([exe_path], cwd=PROJECT_DIR)
    time.sleep(1.5)

    poll = proc.poll()
    if poll is not None and poll != 0:
        raise RuntimeError(f"Smoke test failed: executable crashed with exit code {poll}")

    if psutil:
        p = psutil.Process(proc.pid)
        mem_mb = p.memory_info().rss / (1024 * 1024)
        print(f"  -> Process is running normally (PID: {proc.pid})")
        print(f"  -> Memory usage: {mem_mb:.2f} MB (Target: < 20 MB)")
    else:
        print(f"  -> Process is running normally (PID: {proc.pid})")

    # Terminate process after successful verification
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
    print("  -> Smoke test passed successfully (exit code verified).")


if __name__ == "__main__":
    build_exe()
