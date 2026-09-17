from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def wait_for_pid(pid: int, timeout: float = 45.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pid <= 0:
            return
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True,
                    text=True,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if str(pid) not in result.stdout:
                    return
            else:
                os.kill(pid, 0)
        except Exception:
            return
        time.sleep(0.5)
    raise RuntimeError("NOVA가 종료되지 않아 업데이트를 적용하지 못했습니다.")


def overlay(source: Path, target: Path) -> None:
    source = source.resolve()
    target = target.resolve()
    if not source.exists():
        raise RuntimeError("업데이트 payload가 없습니다.")
    target.mkdir(parents=True, exist_ok=True)

    for src in source.rglob("*"):
        relative = src.relative_to(source)
        dst = target / relative
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_name(dst.name + ".nova_new")
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--restart-exe", required=True)
    parser.add_argument("--restart-arg", action="append", default=[])
    parser.add_argument("--requirements")
    args = parser.parse_args()

    try:
        wait_for_pid(args.pid)
        overlay(Path(args.source), Path(args.target))
        if args.requirements:
            req = Path(args.requirements)
            if req.exists():
                install = subprocess.run([args.restart_exe, "-m", "pip", "install", "-r", str(req)], cwd=args.target)
                if install.returncode != 0:
                    raise RuntimeError("업데이트 의존성 설치에 실패했습니다.")
        subprocess.Popen([args.restart_exe, *args.restart_arg], cwd=args.target)
        return 0
    except Exception as e:
        try:
            log = Path(os.getenv("LOCALAPPDATA", Path.home())) / "NOVA" / "update" / "updater_error.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(str(e), encoding="utf-8")
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
