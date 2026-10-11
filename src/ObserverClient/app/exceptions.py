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
