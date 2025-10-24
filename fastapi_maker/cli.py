import typer

app = typer.Typer(
    name="fam",
    help="FastAPI Maker: Scaffold FastAPI projects (work in progress)."
)

@app.command()
def hello():
    """Just a placeholder to reserve the CLI name."""
    typer.echo("✅ fastapi-maker is reserved! Full version coming soon.")

if __name__ == "__main__":
    app()
