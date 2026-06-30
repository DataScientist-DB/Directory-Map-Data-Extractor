from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(title: str, command: list[str]) -> bool:
    print(f"\n=== {title} ===")

    result = subprocess.run(
        command,
        cwd=ROOT,
    )

    return result.returncode == 0


def main() -> int:
    ok = True

    ok &= run(
        "Smoke Test",
        [sys.executable, "tests/smoke_test.py"],
    )

    ok &= run(
        "Regression Test",
        [
            sys.executable,
            "tests/regression.py",
            "storage/key_value_stores/default/chambermaster_costamesa_test.xlsx",
            "tests/chambermaster/costa_mesa/expected.json",
        ],
    )

    print("\n======================================")
    print("UBDI RELEASE VALIDATION")
    print("======================================")

    print("Overall:", "PASS" if ok else "FAIL")

    print("======================================")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())