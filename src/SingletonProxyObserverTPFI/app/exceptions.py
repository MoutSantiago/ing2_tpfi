"""Módulo que define las excepciones propias del servidor.

Reemplazan a los valores de retorno de error ("Error", False, None) en las
capas inferiores: los DAOs, el proxy y los observers lanzan estas excepciones,
y el Server las captura y las convierte en la respuesta de error para el
cliente.

Patrón: Ninguno

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""
