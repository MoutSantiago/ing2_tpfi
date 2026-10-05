"""Módulo encargado de recibir peticiones y retornar respuestas.

Escucha conexiones TCP, interpreta el JSON de cada petición y la deriva al
proxy (get, set, list) o al publisher (subscribe), sin conocer los DAOs.

Patrón: Ninguno

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""
