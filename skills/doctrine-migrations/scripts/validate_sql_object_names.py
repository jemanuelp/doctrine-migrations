#!/usr/bin/env python3
"""Validate SQL table and column naming rules in Doctrine migrations."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


IDENT = r'(?:"([^"]+)"|([A-Za-z_][A-Za-z0-9_]*))'
SNAKE = re.compile(r'^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$')
RESERVED = {'user', 'order', 'group', 'select', 'table', 'type', 'date'}
GENERIC = {'date', 'type', 'amount', 'price'}
CONSTRAINT_START = {'CONSTRAINT', 'PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'EXCLUDE'}
CONSTRAINT_WORDS = {'PRIMARY', 'NOT', 'NULL', 'DEFAULT', 'CONSTRAINT', 'UNIQUE', 'CHECK', 'REFERENCES'}


@dataclass(frozen=True)
class SqlCall:
    sql: str
    line: int


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    message: str


@dataclass(frozen=True)
class Column:
    name: str
    definition: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Validate SQL object naming rules.')
    parser.add_argument('paths', nargs='*', type=Path, help='Migration files or directories to validate.')
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
        elif target.is_file() and target.suffix == '.php':
            files.append(target)
        else:
            print(f'warning: skipped missing or unsupported path: {target}', file=sys.stderr)
    return sorted(set(files))


def parse_add_sql_calls(source: str) -> list[SqlCall]:
    calls: list[SqlCall] = []
    index = 0
    while True:
        index = source.find('$this->addSql', index)
        if index == -1:
            return calls
        line = source.count('\n', 0, index) + 1
        open_paren = source.find('(', index)
        quote_index = next_quote_index(source, open_paren + 1)
        if quote_index is None:
            index += 1
            continue
        sql, end = read_php_string(source, quote_index + 1, source[quote_index])
        calls.append(SqlCall(sql=sql, line=line))
        index = end + 1


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
        elif char == '\\':
            chars.append(char)
            escaped = True
        elif char == quote:
            return ''.join(chars), index
        else:
            chars.append(char)
    return ''.join(chars), len(text)


def split_statements(sql: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    depth = 0
    for char in sql:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == ';' and depth == 0:
            statement = ''.join(current).strip()
            if statement:
                parts.append(statement)
            current = []
            continue
        current.append(char)
    statement = ''.join(current).strip()
    return parts + ([statement] if statement else [])


def validate_file(path: Path) -> list[Finding]:
    source = path.read_text(encoding='utf-8', errors='replace')
    findings: list[Finding] = []
    for call in parse_add_sql_calls(source):
        for statement in split_statements(call.sql):
            findings.extend(validate_statement(path, call.line, statement))
    return findings


def validate_statement(path: Path, line: int, statement: str) -> list[Finding]:
    cleaned = strip_comments(statement)
    return (
        validate_create_table(path, line, cleaned)
        + validate_alter_table(path, line, cleaned)
    )


def strip_comments(statement: str) -> str:
    statement = re.sub(r'/\*.*?\*/', '', statement, flags=re.DOTALL)
    return '\n'.join(line for line in statement.splitlines() if not line.strip().startswith('--'))


def validate_create_table(path: Path, line: int, statement: str) -> list[Finding]:
    match = re.search(rf'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?{IDENT}\s*\(', statement, re.I)
    if not match:
        return []
    table = ident(match)
    body = read_parenthesized(statement, match.end() - 1)
    columns, primary_key, foreign_keys = parse_table_body(body)
    findings = validate_table_name(path, line, table)
    for column in columns:
        findings.extend(validate_column(path, line, column))
    findings.extend(validate_primary_key(path, line, table, columns, primary_key))
    for column in foreign_keys:
        findings.extend(validate_foreign_key(path, line, column))
    findings.extend(validate_join_table(path, line, table, columns, primary_key))
    return findings


def read_parenthesized(text: str, open_index: int) -> str:
    depth = 0
    quote: str | None = None
    for index in range(open_index, len(text)):
        char = text[index]
        if quote:
            if char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
        elif char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            if depth == 0:
                return text[open_index + 1:index]
    return ''


def parse_table_body(body: str) -> tuple[list[Column], list[str], list[str]]:
    columns: list[Column] = []
    primary_key: list[str] = []
    foreign_keys: list[str] = []
    for item in split_top_level(body, ','):
        item = item.strip()
        first = item.split(None, 1)[0].upper() if item.split() else ''
        if first in CONSTRAINT_START:
            primary_key.extend(parse_key_columns(item, 'PRIMARY KEY'))
            foreign_keys.extend(parse_key_columns(item, 'FOREIGN KEY'))
            continue
        match = re.match(rf'\s*{IDENT}\s+(.*)', item, re.S)
        if not match:
            continue
        column = ident(match)
        columns.append(Column(column, item))
        if re.search(r'\bPRIMARY\s+KEY\b', item, re.I):
            primary_key.append(column)
    return columns, primary_key, foreign_keys


def split_top_level(text: str, separator: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None
    depth = 0
    for char in text:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        elif char == separator and depth == 0:
            parts.append(''.join(current))
            current = []
            continue
        current.append(char)
    return parts + [''.join(current)]


def parse_key_columns(item: str, keyword: str) -> list[str]:
    match = re.search(rf'\b{keyword}\s*\(([^)]+)\)', item, re.I)
    if not match:
        return []
    return [normalize_identifier(part.strip()) for part in match.group(1).split(',')]


def validate_alter_table(path: Path, line: int, statement: str) -> list[Finding]:
    match = re.search(rf'ALTER\s+TABLE\s+{IDENT}', statement, re.I)
    if not match:
        return []
    findings = validate_table_name(path, line, ident(match))
    rename = re.search(rf'\bRENAME\s+TO\s+{IDENT}', statement, re.I)
    add = re.search(rf'\bADD\s+(?:COLUMN\s+)?{IDENT}\s+([^,;]+)', statement, re.I)
    rename_col = re.search(rf'\bRENAME\s+COLUMN\s+{IDENT}\s+TO\s+{IDENT}', statement, re.I)
    if rename:
        findings.extend(validate_table_name(path, line, ident(rename)))
    if add:
        findings.extend(validate_column(path, line, Column(ident(add), add.group(3))))
    if rename_col:
        findings.extend(validate_column_name(path, line, ident_at(rename_col, 3)))
    return findings


def validate_table_name(path: Path, line: int, name: str) -> list[Finding]:
    findings = validate_identifier(path, line, 'table', name)
    if name in RESERVED:
        findings.append(Finding(path, line, f'table name must avoid reserved or ambiguous word: {name}'))
    if '_has_' in name:
        findings.append(Finding(path, line, f'table name should omit redundant "has": {name}'))
    if not is_plural_name(name):
        findings.append(Finding(path, line, f'table name should be plural snake_case: {name}'))
    return findings


def validate_column(path: Path, line: int, column: Column) -> list[Finding]:
    findings = validate_column_name(path, line, column.name)
    definition = column.definition.upper()
    type_part = column_type(column.definition)
    if is_boolean(type_part) and not column.name.startswith(('is_', 'has_', 'can_')):
        findings.append(Finding(path, line, f'boolean column should start with is_, has_, or can_: {column.name}'))
    if is_timestamp(type_part) and not column.name.endswith('_at'):
        findings.append(Finding(path, line, f'timestamp column should end with _at: {column.name}'))
    if 'FOREIGN KEY' in definition or column.name.endswith('_id'):
        findings.extend(validate_foreign_key(path, line, column.name))
    return findings


def validate_column_name(path: Path, line: int, name: str) -> list[Finding]:
    findings = validate_identifier(path, line, 'column', name)
    if name in RESERVED or name in GENERIC or re.search(r'\d$', name):
        findings.append(Finding(path, line, f'column name must be descriptive and non-ambiguous: {name}'))
    if is_plural_name(name) and name not in {'status'} and not name.endswith('_id'):
        findings.append(Finding(path, line, f'column name should be singular snake_case: {name}'))
    return findings


def validate_identifier(path: Path, line: int, kind: str, name: str) -> list[Finding]:
    if SNAKE.fullmatch(name):
        return []
    return [Finding(path, line, f'{kind} name must be lowercase snake_case: {name}')]


def validate_primary_key(path: Path, line: int, table: str, columns: list[Column], primary_key: list[str]) -> list[Finding]:
    if len(primary_key) == 1 and primary_key[0] != 'id':
        return [Finding(path, line, f'primary key should be named id inside {table}; found {primary_key[0]}')]
    if len(primary_key) > 1 and set(primary_key) != {column.name for column in columns if column.name.endswith('_id')}:
        return [Finding(path, line, f'composite primary key should match join foreign keys in {table}')]
    return []


def validate_foreign_key(path: Path, line: int, column: str) -> list[Finding]:
    if not column.endswith('_id'):
        return [Finding(path, line, f'foreign key should use singular entity name plus _id: {column}')]
    prefix = column[:-3]
    if is_plural_name(prefix):
        return [Finding(path, line, f'foreign key entity name should be singular before _id: {column}')]
    return []


def validate_join_table(path: Path, line: int, table: str, columns: list[Column], primary_key: list[str]) -> list[Finding]:
    fk_columns = [column.name for column in columns if column.name.endswith('_id')]
    if len(columns) != 2 or set(fk_columns) != {column.name for column in columns}:
        return []
    findings: list[Finding] = []
    if '_has_' in table:
        findings.append(Finding(path, line, f'many-to-many table should not include redundant "has": {table}'))
    if len(table.split('_')) < 2 or not all(is_plural_name(part) for part in table.split('_')):
        findings.append(Finding(path, line, f'many-to-many table should combine plural table names: {table}'))
    if set(primary_key) != set(fk_columns):
        findings.append(Finding(path, line, f'many-to-many table should use a composite primary key over its foreign keys: {table}'))
    return findings


def column_type(definition: str) -> str:
    words = definition.split()[1:]
    collected: list[str] = []
    for word in words:
        if word.upper().strip(',') in CONSTRAINT_WORDS:
            break
        collected.append(word)
    return ' '.join(collected).upper()


def is_boolean(type_part: str) -> bool:
    return bool(re.search(r'\b(BOOL|BOOLEAN)\b', type_part))


def is_timestamp(type_part: str) -> bool:
    return bool(re.search(r'\b(TIMESTAMP|TIMESTAMPTZ|DATETIME)\b', type_part))


def is_plural_name(name: str) -> bool:
    last = name.rsplit('_', 1)[-1]
    return last.endswith('s') and last not in {'status'}


def ident(match: re.Match[str]) -> str:
    return normalize_identifier(match.group(1) or match.group(2))


def ident_at(match: re.Match[str], group: int) -> str:
    return normalize_identifier(match.group(group) or match.group(group + 1))


def normalize_identifier(value: str) -> str:
    return value.strip().strip('"')


def print_findings(findings: list[Finding]) -> None:
    print('SQL object naming violations found:')
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
    print(f'OK: {len(files)} migration file(s) comply with SQL object naming rules.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
