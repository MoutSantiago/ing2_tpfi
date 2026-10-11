"""Módulo que define las excepciones propias del servidor.

Reemplazan a los valores de retorno de error ("Error", False, None) en las
capas inferiores: los DAOs, el proxy y los observers lanzan estas excepciones,
y el Server las captura y las convierte en la respuesta de error para el
cliente.

Sirven además para que las capas superiores no dependan de librerías externas:
los errores de boto3 y de sockets se capturan en la capa que los produce y se
relanzan como alguna de estas excepciones.

Patrón: Ninguno

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

from __future__ import annotations


class DataAccessError(Exception):
    """Excepción base de los errores de acceso a la base de datos.

    Se lanza ante cualquier fallo en el acceso a la base: conexión, permisos,
    tabla inexistente o error propio de DynamoDB.
    Al ser la excepción base de los errores de datos, capturarla cubre
    también a RecordNotFoundError.

    La lanzan CorporateDataDAO y CorporateLogDAO (incluidos sus constructores
    y get_instance()) y, por propagación, CorporateDataProxy.
    La captura el Server, para responder con error al cliente, y main, para
    informar el fallo de arranque si ocurre al crear los DAOs.

    Al relanzar un error de boto3 se encadena la causa original con
    `raise DataAccessError(...) from error`, para no perder el detalle en los
    logs de debug.
    """


class RecordNotFoundError(DataAccessError):
    """Excepción que indica que el registro solicitado no existe.

    Hereda de DataAccessError, de modo que un `except DataAccessError`
    también la captura, pero permite distinguir este caso particular cuando
    haga falta, por ejemplo para armar un mensaje más claro para el cliente.

    La lanza CorporateDataDAO.get y la captura el Server.
    """


class ObserverUnavailableError(Exception):
    """Excepción que indica que un observer no puede recibir la notificación.

    Por ejemplo, cuando el cliente subscripto cerró la conexión.
    No hereda de DataAccessError porque no tiene relación con la base de datos.

    La lanza ClientObserver.update al capturar un OSError del socket, y la
    captura SubscriptionManager.notify_subscribers, que desuscribe y cierra a
    ese observer y continúa con la notificación de los demás.

    Nota: a diferencia de un get de un registro inexistente, un unsubscribe de
    un observer que no estaba subscripto no lanza esta excepción, porque no es
    un caso excepcional sino parte del flujo normal.
    """
