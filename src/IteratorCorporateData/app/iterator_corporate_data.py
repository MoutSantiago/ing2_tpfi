"""Módulo que implementa la lógica del programa cliente del patrón iterator.

IteratorCorporateData es la clase cliente: obtiene un iterador de la
colección, lo recorre, arma el resultado y lo muestra con JsonWrite. Solo
conoce las interfaces Collection e Iterator, por lo que no sabe si recorre
toda la tabla o un único registro, ni cómo se accede a la base. Recibe sus
dependencias ya construidas para poder reemplazarlas por mocks en los tests.

Patrón: Iterator

Ingeniería de Software II - UADER FCyT (2026)
Autores:
 - Laiño Valentino
 - Mout Santiago
 - Sandillú Axel
Copyright (c) 2026. Licencia MIT (ver LICENSE).
"""

import logging
from typing import Any

from IteratorCorporateData.app.iterable_collection import Collection
from IteratorCorporateData.app.json_write import JsonWrite
from IteratorCorporateData.app.record_iterator import Iterator

logger = logging.getLogger(__name__)


class IteratorCorporateData:
    """Cliente que recorre CorporateData y emite el resultado en JSON.

    Obtiene un iterador de la colección, recopila los registros, arma el
    resultado según la consulta pedida y lo muestra con JsonWrite. No captura
    excepciones: los errores de los iteradores y del escritor se propagan al
    main.
    """

    _collection: Collection
    """Atributo privado de instancia con la colección de la que se obtiene
    el iterador."""

    _writer: JsonWrite
    """Atributo privado de instancia con el objeto que emite el resultado."""

    _single_record: bool
    """Atributo privado de instancia que indica que se pidió un registro
    puntual (--id), por lo que el resultado es el registro como objeto y no
    una lista. Por defecto, False."""

    def __init__(
        self,
        collection: Collection,
        writer: JsonWrite,
        single_record: bool = False,
    ) -> None:
        """Método constructor de la clase.

        Recibe las dependencias y la bandera, y las guarda en los atributos
        correspondientes. No consulta la base de datos.

        Args:
            collection (Collection): Colección de la que se obtiene el
                iterador.
            writer (JsonWrite): Objeto que emite el resultado.
            single_record (bool): Indica que se pidió un registro puntual.
                Por defecto, False.
        """
        self._collection = collection
        self._writer = writer
        self._single_record = single_record
        logger.debug("IteratorCorporateData inicializado con sus dependencias")

    def run(self) -> Any:
        """Ejecuta la consulta completa y retorna el resultado.

        Los pasos, en este orden:
        Obtiene un iterador con _collection.create_iterator().
        Recopila los registros con _collect().
        Arma el resultado: si no hay registros, {"id": None}; si
            _single_record es True, el primer registro como objeto; en caso
            contrario, la lista de registros.
        Lo muestra con _writer.write() y lo retorna.

        Returns:
            Any: Resultado emitido: una lista de registros, un registro o el
                objeto {"id": None}.
        """
        logger.debug("Obteniendo iterador de la colección")
        iterator = self._collection.create_iterator()

        records = self._collect(iterator)

        if not records:
            logger.debug("No se encontraron registros")
            result: Any = {"id": None}
        elif self._single_record:
            logger.debug("Armando resultado como registro único")
            result = records[0]
        else:
            logger.debug("Armando resultado como lista de registros")
            result = records

        logger.debug("Escribiendo resultado")
        self._writer.write(result)

        return result

    def _collect(self, iterator: Iterator) -> list[dict]:
        """Recorre el iterador y acumula sus registros en una lista.

        Args:
            iterator (Iterator): Iterador sobre los registros de
                CorporateData.

        Returns:
            list[dict]: Registros entregados por el iterador, en orden.
        """
        logger.debug("Recolectando registros")
        records: list[dict] = []

        while iterator.has_more():
            records.append(iterator.next())

        logger.debug("Registros recopilados: %d", len(records))

        return records
