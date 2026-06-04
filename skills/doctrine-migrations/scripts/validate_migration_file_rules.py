#!/usr/bin/env python3
"""Validate WhatsApp Bridge Doctrine migration file rules."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


DDL_KEYWORDS = {
    'ALTER',
    'COMMENT',
    'CREATE',
    'DROP',
    'REINDEX',
    'RENAME',
    'TRUNCATE',
}

DML_KEYWORDS = {
    'CALL',
    'DELETE',
    'INSERT',
    'MERGE',
    'SELECT',
    'UPDATE',
}

MIGRATION_NAME_PATTERN = re.compile(r'^Version\d{14}_[a-z][a-z0-9]*(?:_[a-z0-9]+)*$')
BARE_VERSION_PATTERN = re.compile(r'^Version\d{14}$')
CAMEL_CASE_VERSION_PATTERN = re.compile(r'^Version\d{14}[A-Z]')
CLASS_PATTERN = re.compile(r'(?:final\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\s+extends\s+AbstractMigration')


@dataclass(frozen=True)
class SqlCall:
    method: str
    sql: str
    line: int


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Validate Doctrine migration DDL/DML file structure rules.',
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


def find_method_body(source: str, method_name: str) -> tuple[str, int] | None:
    pattern = re.compile(rf'function\s+{re.escape(method_name)}\s*\([^)]*\)\s*:\s*void\s*\{{')
    match = pattern.search(source)
    if not match:
        return None

    opening_brace = source.rfind('{', 0, match.end())
    depth = 0

    for index in range(opening_brace, len(source)):
        char = source[index]
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                body = source[opening_brace + 1:index]
                line = source.count('\n', 0, opening_brace) + 1
                return body, line

    return None


def parse_add_sql_calls(body: str, method: str, method_start_line: int) -> list[SqlCall]:
    calls: list[SqlCall] = []
    marker = '$this->addSql'
    index = 0

    while True:
        index = body.find(marker, index)
        if index == -1:
            return calls

        line = method_start_line + body.count('\n', 0, index)
        open_paren = body.find('(', index + len(marker))
        if open_paren == -1:
            index += len(marker)
            continue

        quote_index = next_quote_index(body, open_paren + 1)
        if quote_index is None:
            index = open_paren + 1
            continue

        quote = body[quote_index]
        sql, end_index = read_php_string(body, quote_index + 1, quote)
        calls.append(SqlCall(method=method, sql=sql, line=line))
        index = end_index + 1


def next_quote_index(text: str, start: int) -> int | None:
    for index in range(start, len(text)):
        if text[index] in {"'", '"'}:
            return index
        if not text[index].isspace():
            continue
    return None


def read_php_string(text: str, start: int, quote: str) -> tuple[str, int]:
    chars: list[str] = []
    escaped = False

    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            chars.append(char)
            escaped = False
            continue
        if char == '\\':
            chars.append(char)
            escaped = True
            continue
        if char == quote:
            return ''.join(chars), index
        chars.append(char)

    return ''.join(chars), len(text)


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    quote: str | None = None
    dollar_quote: str | None = None
    escaped = False
    index = 0

    while index < len(sql):
        char = sql[index]
        if escaped:
            current.append(char)
            escaped = False
            index += 1
            continue
        if char == '\\':
            current.append(char)
            escaped = True
            index += 1
            continue
        if dollar_quote:
            if sql.startswith(dollar_quote, index):
                current.append(dollar_quote)
                index += len(dollar_quote)
                dollar_quote = None
                continue
            current.append(char)
            index += 1
            continue
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            index += 1
            continue
        dollar_match = re.match(r'\$[A-Za-z_][A-Za-z0-9_]*\$|\$\$', sql[index:])
        if dollar_match:
            dollar_quote = dollar_match.group(0)
            current.append(dollar_quote)
            index += len(dollar_quote)
            continue
        if char in {"'", '"'}:
            current.append(char)
            quote = char
            index += 1
            continue
        if char == ';':
            statement = ''.join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            index += 1
            continue
        current.append(char)
        index += 1

    statement = ''.join(current).strip()
    if statement:
        statements.append(statement)

    return statements


def strip_sql_comments(statement: str) -> str:
    statement = re.sub(r'/\*.*?\*/', '', statement, flags=re.DOTALL)
    lines = [line for line in statement.splitlines() if not line.strip().startswith('--')]
    return '\n'.join(lines).strip()


def classify_statement(statement: str) -> str:
    cleaned = strip_sql_comments(statement)
    match = re.match(r'([a-zA-Z]+)', cleaned)
    if not match:
        return 'unknown'

    keyword = match.group(1).upper()
    if keyword in DDL_KEYWORDS:
        return 'ddl'
    if keyword in DML_KEYWORDS:
        return 'dml'
    return 'unknown'


def validate_file(path: Path) -> list[Finding]:
    source = path.read_text(encoding='utf-8', errors='replace')
    findings = validate_file_and_class_name(path, source)
    calls: list[SqlCall] = []
    counts = {'up': 0, 'down': 0}

    for method in ('up', 'down'):
        result = find_method_body(source, method)
        if result is None:
            findings.append(Finding(path, 1, f'missing {method}() method'))
            continue
        body, line = result
        method_calls = parse_add_sql_calls(body, method, line)
        counts[method] = len(method_calls)
        calls.extend(method_calls)

    classified: list[tuple[SqlCall, str, str]] = []
    for call in calls:
        statements = split_sql_statements(call.sql)
        if not statements:
            findings.append(Finding(path, call.line, f'{call.method}() contains an empty addSql call'))
            continue
        for statement in statements:
            classified.append((call, statement, classify_statement(statement)))

    categories = {category for _, _, category in classified if category in {'ddl', 'dml'}}
    unknowns = [(call, statement) for call, statement, category in classified if category == 'unknown']

    for call, statement in unknowns:
        preview = ' '.join(strip_sql_comments(statement).split())[:80]
        findings.append(Finding(path, call.line, f'unknown SQL statement type in {call.method}(): {preview}'))

    if categories == {'ddl', 'dml'}:
        findings.append(Finding(path, 1, 'migration mixes DDL and DML; split schema and data changes into separate files'))

    if 'ddl' in categories:
        if counts['up'] != 1:
            findings.append(Finding(path, 1, f'DDL migration must have exactly one addSql in up(); found {counts["up"]}'))
        if counts['down'] != 1:
            findings.append(Finding(path, 1, f'DDL migration must have exactly one addSql in down(); found {counts["down"]}'))

        for method in ('up', 'down'):
            method_ddl_count = sum(
                1 for call, _, category in classified if call.method == method and category == 'ddl'
            )
            if method_ddl_count != 1:
                findings.append(
                    Finding(path, 1, f'DDL migration must have exactly one DDL statement in {method}(); found {method_ddl_count}'),
                )

    return findings


def validate_file_and_class_name(path: Path, source: str) -> list[Finding]:
    findings: list[Finding] = []
    stem = path.stem

    if BARE_VERSION_PATTERN.fullmatch(stem):
        findings.append(
            Finding(path, 1, 'migration file must include an English snake_case suffix after the Version timestamp'),
        )
    elif CAMEL_CASE_VERSION_PATTERN.match(stem):
        findings.append(
            Finding(path, 1, 'migration file suffix must be English snake_case, not camelCase/PascalCase'),
        )
    elif not MIGRATION_NAME_PATTERN.fullmatch(stem):
        findings.append(
            Finding(path, 1, 'migration file name must match VersionYYYYMMDDHHMMSS_english_snake_case_suffix.php'),
        )

    class_match = CLASS_PATTERN.search(source)
    if not class_match:
        findings.append(Finding(path, 1, 'migration class extending AbstractMigration was not found'))
        return findings

    class_name = class_match.group(1)
    class_line = source.count('\n', 0, class_match.start()) + 1
    if class_name != stem:
        findings.append(
            Finding(path, class_line, f'migration class name must match file stem; expected {stem}, found {class_name}'),
        )
    if BARE_VERSION_PATTERN.fullmatch(class_name):
        findings.append(
            Finding(path, class_line, 'migration class must include an English snake_case suffix after the Version timestamp'),
        )
    elif CAMEL_CASE_VERSION_PATTERN.match(class_name):
        findings.append(
            Finding(path, class_line, 'migration class suffix must be English snake_case, not camelCase/PascalCase'),
        )

    return findings


def main() -> int:
    args = parse_args()
    files = collect_files(args.paths)
    if not files:
        print('No migration files found.')
        return 0

    findings = [finding for path in files for finding in validate_file(path)]
    if findings:
        print('Migration file rule violations found:')
        for finding in findings:
            relative = finding.path
            if finding.path.is_relative_to(repo_root()):
                relative = finding.path.relative_to(repo_root())
            print(f'- {relative}:{finding.line}: {finding.message}')
        return 1

    print(f'OK: {len(files)} migration file(s) comply with DDL/DML rules.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
