#!/usr/bin/env python3
"""Validate Doctrine migration file names and class names."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


MIGRATION_NAME_PATTERN = re.compile(r'^Version\d{14}_[a-z][a-z0-9]*(?:_[a-z0-9]+)*$')
BARE_VERSION_PATTERN = re.compile(r'^Version\d{14}$')
CAMEL_CASE_VERSION_PATTERN = re.compile(r'^Version\d{14}[A-Z]')
CLASS_PATTERN = re.compile(r'(?:final\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\s+extends\s+AbstractMigration')


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Validate Doctrine migration file names and class names.',
    )
    parser.add_argument(
        'paths',
        nargs='*',
        type=Path,
        help='Migration files or directories to validate. Defaults to migrations/migrations.',
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def collect_files(paths: list[Path]) -> list[Path]:
    targets = paths or [repo_root() / 'migrations' / 'migrations']
    files: list[Path] = []

    for target in targets:
        target = target.resolve()
        if target.is_dir():
            files.extend(sorted(target.glob('Version*.php')))
            continue
        if target.is_file() and target.suffix == '.php':
            files.append(target)
            continue
        print(f'warning: skipped missing or unsupported path: {target}', file=sys.stderr)

    return sorted(set(files))


def validate_file(path: Path) -> list[Finding]:
    source = path.read_text(encoding='utf-8', errors='replace')
    findings: list[Finding] = []
    stem = path.stem

    if BARE_VERSION_PATTERN.fullmatch(stem):
        findings.append(
            Finding(path, 1, 'file must include an English snake_case suffix after the Version timestamp'),
        )
    elif CAMEL_CASE_VERSION_PATTERN.match(stem):
        findings.append(
            Finding(path, 1, 'file suffix must be English snake_case, not camelCase/PascalCase'),
        )
    elif not MIGRATION_NAME_PATTERN.fullmatch(stem):
        findings.append(
            Finding(path, 1, 'file name must match VersionYYYYMMDDHHMMSS_english_snake_case_suffix.php'),
        )

    class_match = CLASS_PATTERN.search(source)
    if not class_match:
        findings.append(Finding(path, 1, 'class extending AbstractMigration was not found'))
        return findings

    class_name = class_match.group(1)
    class_line = source.count('\n', 0, class_match.start()) + 1

    if class_name != stem:
        findings.append(
            Finding(path, class_line, f'class name must match file stem; expected {stem}, found {class_name}'),
        )
    if BARE_VERSION_PATTERN.fullmatch(class_name):
        findings.append(
            Finding(path, class_line, 'class must include an English snake_case suffix after the Version timestamp'),
        )
    elif CAMEL_CASE_VERSION_PATTERN.match(class_name):
        findings.append(
            Finding(path, class_line, 'class suffix must be English snake_case, not camelCase/PascalCase'),
        )
    elif not MIGRATION_NAME_PATTERN.fullmatch(class_name):
        findings.append(
            Finding(path, class_line, 'class name must match VersionYYYYMMDDHHMMSS_english_snake_case_suffix'),
        )

    return findings


def print_findings(findings: list[Finding]) -> None:
    print('Migration naming violations found:')
    for finding in findings:
        relative = finding.path
        if finding.path.is_relative_to(repo_root()):
            relative = finding.path.relative_to(repo_root())
        print(f'- {relative}:{finding.line}: {finding.message}')


def main() -> int:
    files = collect_files(parse_args().paths)
    if not files:
        print('No migration files found.')
        return 0

    findings = [finding for path in files for finding in validate_file(path)]
    if findings:
        print_findings(findings)
        return 1

    print(f'OK: {len(files)} migration file name(s) and class name(s) comply.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
