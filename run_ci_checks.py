#!/usr/bin/env python
"""Run all CI checks locally before pushing."""

import subprocess
import sys


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print("=" * 60)

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"❌ FAILED: {description}")
        return False
    else:
        print(f"✅ PASSED: {description}")
        return True


def main():
    """Run all CI checks."""
    checks = [
        (
            "python -m black --check src/ celery_worker.py main.py sensor_simulator.py start_services.py",
            "Black formatting check",
        ),
        (
            "python -m isort --check-only src/ celery_worker.py main.py sensor_simulator.py start_services.py",
            "isort import sorting check",
        ),
        (
            "python -m flake8 src/ celery_worker.py main.py sensor_simulator.py start_services.py --count --select=E9,F63,F7,F82 --show-source --statistics",
            "Flake8 syntax errors check",
        ),
        (
            "python -m flake8 src/ celery_worker.py main.py sensor_simulator.py start_services.py --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics",
            "Flake8 style check",
        ),
    ]

    all_passed = True
    for cmd, description in checks:
        if not run_command(cmd, description):
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL CHECKS PASSED! Safe to push.")
    else:
        print("❌ SOME CHECKS FAILED! Fix issues before pushing.")
        print("\nTo auto-fix formatting issues, run:")
        print(
            "  python -m black src/ celery_worker.py main.py sensor_simulator.py start_services.py"
        )
        print(
            "  python -m isort src/ celery_worker.py main.py sensor_simulator.py start_services.py"
        )
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
