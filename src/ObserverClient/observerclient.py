"""Módulo que implementa la lógica del programa suscriptor.

Esta clase no conoce los detalles de la red ni de la salida: delega en
ServerConnection y NotificationWriter, que recibe ya construidos para poder
reemplazarlos por mocks en los tests. No implementa el patrón Observer (ese
vive en el servidor): es el suscriptor remoto.


Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""
