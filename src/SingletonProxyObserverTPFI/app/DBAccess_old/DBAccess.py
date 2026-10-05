class SingletonMeta(type):
    """Clase base para implementación de patron singleton."""

    """Instancia actual de la calse en memoria

    Returns:
        dict: Intancia almacenada
    """
    _instances = {}

    def __call__(cls, *args, **kwargs) -> dict:
        """Clase base para la implementación del patrón singleton.

        Returns:
            dict: Instancia ya inicializada (si existe)
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class DBAccess(metaclass=SingletonMeta):
    """Clase con los metodos de acceso a la base de datos.

    Implementada usando el patrón Singleton.
    """

    def DireccionMemoria(self) -> str:
        """Retorna la dirección de memoria de la instancia en hexadecimal."""
        return hex(id(self))
