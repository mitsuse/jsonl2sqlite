from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

app = typer.Typer()


@app.command()
def main(
    jsonlines: Path = typer.Option(
        ...,
        help="the path of a directory which stores JSONLines files",
    ),
    sqlite: Path = typer.Option(
        ...,
        help="the output path of a SQLite database",
    ),
) -> None:
    import json
    import os
    import sqlite3
    from functools import reduce

    from pypika import Column, Query

    sqlite.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(sqlite)
    cursor = db.cursor()

    seq_name = os.listdir(jsonlines)
    seq_name = filter(lambda s: s.endswith(".jsonl"), seq_name)
    seq_path_table = tuple(jsonlines / n for n in seq_name)

    for p in seq_path_table:
        table = p.name.rstrip(".jsonl")

        with p.open() as f:
            iter_schema = (extract_schema_from(json.loads(x)) for x in f)
            schema = reduce(merge_schema, iter_schema)
            seq_key = sorted(schema)

        seq_column = tuple(
            Column(n, t, nullable=nullable) for n, (t, nullable) in schema.items()
        )

        query = (
            Query.create_table(table).columns(*seq_column).primary_key("id").get_sql()
        )

        cursor.execute(query)
        db.commit()

        with p.open() as f:
            for x in f:
                json_ = json.loads(x)
                seq_value = tuple(json_.get(k) for k in seq_key)

                query = Query.into(table).columns(*seq_key).insert(*seq_value).get_sql()

                cursor.execute(query)

            db.commit()


__type_mapping = {
    type(None): "NULL",
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bool: "INTEGER",
}


def extract_schema_from(x: Any) -> dict[str, tuple[str, bool]]:
    if not isinstance(x, dict):
        raise TypeError(f"Expected an JSON object (dict) but there is {type(x)}.")

    schema: dict[str, tuple[str, bool]] = {}

    for k, v in x.items():
        t = __type_mapping.get(type(v))
        if t is None:
            raise TypeError(f"Unsupported type {type(type(v))}.")

        schema[k] = (t, t == "NULL")

    return schema


def merge_schema(
    x: dict[str, tuple[str, bool]],
    y: dict[str, tuple[str, bool]],
) -> dict[str, tuple[str, bool]]:
    set_key_x = frozenset(x.keys())
    set_key_y = frozenset(y.keys())
    set_key = set_key_x.union(set_key_y)

    schema: dict[str, tuple[str, bool]] = {}
    for k in set_key:
        t_x, nullable_x = x.get(k, ("NULL", True))
        t_y, nullable_y = y.get(k, ("NULL", True))

        if t_x == "NULL" or t_x is None:
            t = t_y
        elif t_y == "NULL" or t_y is None:
            t = t_x
        elif t_x == t_y:
            t = t_x
        else:
            raise ValueError(f"Incompatible schemas: {x}, {y}.")

        schema[k] = t, nullable_x or nullable_y

    return schema


if __name__ == "__main__":
    app()
