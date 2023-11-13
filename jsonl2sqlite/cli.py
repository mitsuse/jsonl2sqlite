from __future__ import annotations

import typer

app = typer.Typer()


@app.command()
def main() -> None:
    ...


if __name__ == "__main__":
    app()
