"""
Automated PyInstaller build script for Robo2mation Test Runner.
Run with: python build_exe.py
"""

import importlib.util
import os
from pathlib import Path
import shutil
import stat
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


def _remove_readonly(func, path, excinfo):
    """Clear read-only bit and retry removal on Windows."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def ensure_unlocked_dist(dist_dir: Path):
    """Ensure the dist directory can be cleaned before PyInstaller runs."""
    excel_in_dist = (
        dist_dir
        / "Robo2mation_Runner"
        / "Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx"
    )
    if excel_in_dist.exists():
        try:
            with open(excel_in_dist, "ab"):
                pass
        except PermissionError:
            print(
                "\n[!] WARNING: 'Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx' is open in Excel or locked!",
                flush=True,
            )
            if sys.stdin and sys.stdin.isatty():
                try:
                    input(
                        "    -> Please save & close Excel now, then press ENTER to continue..."
                    )
                except EOFError:
                    pass


REQUIRED_PACKAGES = (
    "selenium",
    "openpyxl",
    "dotenv",
    "allure_commons",
    "pluggy",
    "attrs",
)


def _reexec_in_venv_if_needed() -> None:
    """Re-launch using the project .venv Python if required packages are missing here."""
    missing = [pkg for pkg in REQUIRED_PACKAGES if importlib.util.find_spec(pkg) is None]
    if not missing or os.environ.get("ROBO2_BUILD_REEXEC") == "1":
        return

    current_exe = os.path.normcase(os.path.abspath(sys.executable))
    candidates = (
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT.parent / ".venv" / "Scripts" / "python.exe",
        ROOT.parent.parent / ".venv" / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if not candidate.exists():
            continue
        candidate_exe = os.path.normcase(os.path.abspath(str(candidate)))
        if candidate_exe == current_exe:
            continue
        print(f"[*] Switching to project virtual environment: {candidate}", flush=True)
        env = {**os.environ, "ROBO2_BUILD_REEXEC": "1"}
        rc = subprocess.call(
            [str(candidate), "-u", str(Path(__file__).resolve()), *sys.argv[1:]],
            env=env,
        )
        raise SystemExit(rc)


def _verify_required_packages() -> None:
    """Fail fast if build_exe.py is invoked outside the venv where dependencies live."""
    missing = [pkg for pkg in REQUIRED_PACKAGES if importlib.util.find_spec(pkg) is None]
    if missing:
        print(
            "[!] ERROR: Missing required runtime package(s) in this Python environment: "
            + ", ".join(missing)
        )
        print(f"    Current interpreter: {sys.executable}")
        print(
            "    Run this build script from the project virtual environment (.venv) or install: "
            + " ".join(missing)
        )
        raise SystemExit(1)


def build():
    _reexec_in_venv_if_needed()
    _verify_required_packages()
    kill_old_processes()

    if importlib.util.find_spec("PyInstaller") is None:
        print("[*] Installing PyInstaller...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"]
        )
    else:
        print("[*] PyInstaller verified.")

    dist_dir = ROOT / "dist"
    build_dir = ROOT / "build"

    ensure_unlocked_dist(dist_dir)

    for d in [dist_dir, build_dir]:
        if d.exists():
            try:
                shutil.rmtree(d, onexc=_remove_readonly)
            except TypeError:
                shutil.rmtree(d, onerror=_remove_readonly)
            except Exception as e:
                print(
                    f"[!] Warning: Could not remove {d.name} automatically ({e})."
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
        "--collect-all=allure_commons",
        "--collect-all=pluggy",
        "--collect-all=attrs",
        "--hidden-import=allure_commons",
        "--hidden-import=allure_commons.types",
        "--hidden-import=allure_commons.lifecycle",
        "--hidden-import=allure_commons.logger",
        "--hidden-import=allure_commons.model2",
        "--hidden-import=allure_commons.utils",
        "--hidden-import=pluggy",
        "--hidden-import=attr",
        "--hidden-import=attrs",
        "--hidden-import=allure_viewer",
        f"--add-data={ROOT / 'common.py'}{os.pathsep}.",
        f"--add-data={ROOT / 'dms_config.py'}{os.pathsep}.",
        f"--add-data={ROOT / 'allure_reporter.py'}{os.pathsep}.",
        f"--add-data={ROOT / 'allure_viewer.py'}{os.pathsep}.",
    ]

    pages_dir = ROOT / "pages"
    if pages_dir.exists():
        pyinstaller_cmd.append(f"--add-data={pages_dir}{os.pathsep}pages")

    for tc_file in ROOT.glob("tc*.py"):
        pyinstaller_cmd.append(f"--add-data={tc_file}{os.pathsep}.")

    core_dir = ROOT / "core"
    if core_dir.exists():
        pyinstaller_cmd.append(f"--add-data={core_dir}{os.pathsep}core")

    assets_dir = ROOT / "assets"
    if assets_dir.exists():
        pyinstaller_cmd.append(f"--add-data={assets_dir}{os.pathsep}assets")
        icon = assets_dir / "app.ico"
        if icon.exists():
            pyinstaller_cmd.append(f"--icon={icon}")

    pyinstaller_cmd.append(str(ROOT / "app_gui.py"))
    subprocess.check_call(pyinstaller_cmd, cwd=str(ROOT))

    target_folder = dist_dir / "Robo2mation_Runner"

    print("[*] Copying runtime files into distribution folder...")
    for script_file in (
        list(ROOT.glob("tc*.py"))
        + [
            ROOT / "common.py",
            ROOT / "dms_config.py",
            ROOT / "allure_reporter.py",
            ROOT / "allure_viewer.py",
        ]
    ):
        if script_file.exists():
            shutil.copy2(script_file, target_folder / script_file.name)

    if pages_dir.exists():
        shutil.copytree(pages_dir, target_folder / "pages", dirs_exist_ok=True)

    for asset in [".env", "Robo2mation_26Q1_Sanity_Test_Case_Doc.xlsx"]:
        src = ROOT / asset if (ROOT / asset).exists() else (ROOT.parent / asset)
        if src.exists():
            try:
                shutil.copy2(src, target_folder / asset)
            except PermissionError:
                print(f"[!] Skipped overwriting locked file: {asset}")

    if core_dir.exists():
        shutil.copytree(
            core_dir, target_folder / "core", dirs_exist_ok=True
        )

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
