"""Run T-SQL against the Fabric Warehouse or the lakehouse SQL endpoint using the Azure CLI login.

  python run_sql.py <database> -f file.sql [file2.sql ...]     run script files (batches split on GO)
  python run_sql.py <database> -q "SELECT ..."                 run one query and print the result
"""
import os
import re
import struct
import sys

import pyodbc

token = os.environ["SQL_TOKEN"].encode("utf-16-le")
conn = pyodbc.connect(
    f"Driver={{ODBC Driver 17 for SQL Server}};Server={os.environ['SQL_HOST']},1433;Database={sys.argv[1]};Encrypt=yes;",
    attrs_before={1256: struct.pack(f"<I{len(token)}s", len(token), token)}, autocommit=True)
cur = conn.cursor()


def show(cursor):
    while True:
        if cursor.description:
            cols = [c[0] for c in cursor.description]
            rows = [[("" if v is None else str(v)) for v in r] for r in cursor.fetchall()]
            widths = [min(60, max(len(c), *(len(r[i]) for r in rows))) if rows else len(c) for i, c in enumerate(cols)]
            print("  ".join(c.ljust(w) for c, w in zip(cols, widths)))
            print("  ".join("-" * w for w in widths))
            for r in rows:
                print("  ".join(v[:60].ljust(w) for v, w in zip(r, widths)))
            print(f"({len(rows)} rows)\n")
        if not cursor.nextset():
            break


if sys.argv[2] == "-q":
    cur.execute(sys.argv[3])
    show(cur)
else:
    for path in sys.argv[3:]:
        batches = [b.strip() for b in re.split(r"^\s*GO\s*$", open(path, encoding="utf-8").read(), flags=re.M | re.I) if b.strip()]
        for i, batch in enumerate(batches, 1):
            try:
                cur.execute(batch)
                while cur.nextset():
                    pass
            except pyodbc.Error as e:
                print(f"FAILED {os.path.basename(path)} batch {i}: {e}")
                sys.exit(1)
        print(f"ok {os.path.basename(path)} ({len(batches)} batches)")
