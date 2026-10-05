"""Módulo principal del servidor.

Es el modulo que contiene el punto de entrada del servidor.
Gestiona las flags y argumentos y llama a los demas modulos.

Patrón: Ninguno

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import typer

app = typer.Typer()


@app.command()
def main(
    port: int = typer.Option(8080, "--port", "-p", help="Puerto del servidor"),
    showLog: bool = typer.Option(
        False, "-v", help="Activar modo de logs detallados"
    ),
):
    """Inicia el servidor en el puerto especificado con opción de logs."""
    if showLog:
        print("[LOG] Modo detallado (showLog) activado.")
    print(f"El servidor se iniciará en el puerto: {port}")


if __name__ == "__main__":
    app()
