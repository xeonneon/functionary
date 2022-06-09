import typer

import plugin

app = typer.Typer()
app.add_typer(plugin.app, name="plugin")

if __name__ == "__main__":
    app()
