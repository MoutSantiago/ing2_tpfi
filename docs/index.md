# Trabajo Práctico Final Integrador

Ingeniería de Software II - UADER-FCyT-IS2 (2024)

Implementación del patrón Proxy/Singleton/Observer en entorno AWS, utilizando dos tablas en DynamoDB (`CorporateData` y `CorporateLog`).

## Componentes

Se implementan tres programas aplicativos en Python:

- `singletonclient.py` — cliente que consulta o actualiza `CorporateData`.
- `observerclient.py` — cliente que se suscribe y recibe notificaciones de cambios.
- `singletonproxyobserver.py` — servidor de aplicaciones que opera como proxy, singleton y observer, generando pista de auditoría.

## Contenido

```{toctree}
:maxdepth: 2
:caption: Guías

installation
usage
```

```{toctree}
:maxdepth: 2
:caption: Referencia

api
```

## Índices y tablas

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`