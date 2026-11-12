"""
Automated PyInstaller build script for Robo2mation Test Runner.
Run with: python build_exe.py
"""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent


def kill_old_processes():
    """Kill any running instances of the app or chromedriver so files aren't locked."""
    print("[*] Checking for running instances...")
    for proc in ["Robo2mation_Runner.exe", "chromedriver.exe"]:
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", proc, "/T"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
    time.sleep(1)


def build():
    kill_old_processes()

    print("[*] Installing/Verifying PyInstaller...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"]
    )

    dist_dir = ROOT / "dist"
    build_dir = ROOT / "build"

    # Clean previous build directories safely
    for d in [dist_dir, build_dir]:
        if d.exists():
            try:
                shutil.rmtree(d)
            except Exception as e:
                print(
                    f"[!] Warning: Could not remove {d.name} automatically ({e}). Please close any open folders."
                )

    print("[*] Compiling Test Automation Suite into Executable...")

    pyinstaller_cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=Robo2mation_Runner",
        "--collect-all=selenium",
        "--collect-all=openpyxl",
        "--collect-all=dotenv",
        f"--add-data={ROOT / 'common.py'}{os.pathsep}.",
        f"--add-data={ROOT / 'dms_helper.py'}{os.pathsep}.",
        f"--add-data={ROOT / 'explorer_helper.py'}{os.pathsep}.",
    ]

    for tc_file in ROOT.glob("tc*.py"):
        pyinstaller_cmd.append(f"--add-data={tc_file}{os.pathsep}.")

    # Logo + app icon live in the assets/ folder
    assets_dir = ROOT / "assets"
    if assets_dir.exists():
        pyinstaller_cmd.append(f"--add-data={assets_dir}{os.pathsep}assets")
        icon = assets_dir / "app.ico"
        if icon.exists():
            pyinstaller_cmd.append(f"--icon={icon}")

    pyinstaller_cmd.append(str(ROOT / "app_gui.py"))
    subprocess.check_call(pyinstaller_cmd)

    target_folder = dist_dir / "Robo2mation_Runner"

    print("[*] Copying runtime files into distribution folder...")
    for script_file in (
        list(ROOT.glob("tc*.py"))
        + list(ROOT.glob("*_helper.py"))
        + [ROOT / "common.py"]
    ):
        if script_file.exists():
            shutil.copy2(script_file, target_folder / script_file.name)

    for asset in [".env", "Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx"]:
        src = ROOT / asset
        if src.exists():
            shutil.copy2(src, target_folder / asset)

    if assets_dir.exists():
        shutil.copytree(
            assets_dir, target_folder / "assets", dirs_exist_ok=True
        )

    test_files_src = ROOT / "test_files"
    if test_files_src.exists():
        shutil.copytree(
            test_files_src, target_folder / "test_files", dirs_exist_ok=True
        )

    print("\n" + "=" * 60)
    print(" BUILD SUCCESSFUL!")
    print(f" Executable Folder: {target_folder.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    build()