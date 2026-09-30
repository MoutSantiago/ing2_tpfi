"""Módulo principal del servidor."""

import typer

app = typer.Typer()


@app.command()
def main(
    port: int = typer.Option(8080, "--port", "-p", help="Puerto del servidor"),
    showLog: bool = typer.Option(
        False, "--showLog", "-v", help="Activar modo de logs detallados"
    ),
):
    """Inicia el servidor en el puerto especificado con opción de logs."""
    if showLog:
        print("[LOG] Modo detallado (showLog) activado.")
    print(f"El servidor se iniciará en el puerto: {port}")


if __name__ == "__main__":
    app()
