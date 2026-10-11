"""Módulo que define las excepciones propias del cliente observer.

Define la excepción propia de ObserverClient. Reemplaza a los valores de
retorno de error (False, None) en la comunicación con el servidor.

Sirve además para que las capas superiores no dependan de los errores de bajo
nivel del módulo socket: los OSError se capturan en ServerConnection y se
relanzan como ConnectionLostError.

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""


class ConnectionLostError(Exception):
    """Se lanza cuando surgen problemas con la conexión del servidor.

    Cubre estos casos:
    El servidor no está disponible al intentar conectar.
    El servidor cierra la conexión mientras el cliente espera una notificación.
    Falla el envío o la recepción por un error del socket.

    Quién la lanza: ServerConnection (connect, send y receive).
    Quién la captura: ObserverClient (run), que cierra la conexión, espera el
    intervalo de reintento (30 s por defecto) y vuelve a conectar, reenviando
    la acción subscribe.
    """
