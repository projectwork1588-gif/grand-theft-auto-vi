"""Tiny helper that runs a .sql file through mysql-connector-python.

mysql-connector executes one statement per call, so we split the file into
statements ourselves. The splitter understands quotes and comments, which means a
semicolon inside a string such as 'a;b' does not break a statement.
"""
from pathlib import Path


def split_statements(sql_text):
    """Return a list of SQL statements from the text of a .sql file."""
    statements = []
    current = []
    i = 0
    n = len(sql_text)
    quote = None  # the quote character we are currently inside, if any

    while i < n:
        ch = sql_text[i]
        nxt = sql_text[i + 1] if i + 1 < n else ""

        if quote:
            current.append(ch)
            if ch == "\\" and quote != "`" and nxt:
                current.append(nxt)  # backslash escape, keep the next char
                i += 2
                continue
            if ch == quote:
                if nxt == quote:  # doubled quote ('') is an escaped quote
                    current.append(nxt)
                    i += 2
                    continue
                quote = None
            i += 1
            continue

        if ch in ("'", '"', "`"):
            quote = ch
            current.append(ch)
        elif ch == "-" and nxt == "-" and sql_text[i + 2:i + 3] in (" ", "\t", "\n", "\r", ""):
            while i < n and sql_text[i] != "\n":  # line comment
                i += 1
            continue
        elif ch == "#":
            while i < n and sql_text[i] != "\n":
                i += 1
            continue
        elif ch == "/" and nxt == "*":
            end = sql_text.find("*/", i + 2)
            i = n if end == -1 else end + 2  # block comment
            continue
        elif ch == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(ch)
        i += 1

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def run_sql_file(connection, path):
    """Execute every statement in the file. Returns the number executed."""
    statements = split_statements(Path(path).read_text(encoding="utf-8"))
    cursor = connection.cursor()
    try:
        for statement in statements:
            cursor.execute(statement)
    finally:
        cursor.close()
    return len(statements)
