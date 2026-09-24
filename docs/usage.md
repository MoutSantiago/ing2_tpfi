# Uso

El servidor de aplicaciones se inicia con:

```sh
python src/singletonproxyobserver.py {-p=port} {-v}
```

Si no se informa el puerto, se toma `*:8080`.

## Cliente singleton

Consultar o actualizar un registro de `CorporateData`:

```sh
python src/singletonclient.py -i=input.json {-o=output.json} {-v}
```

Formato del `input.json`:

```json
{
    "UUID": "XXXXXXXXXXXXXXXXXXXXXXX",
    "ID": "ZZZZZZZZZZZZZZZZZZZZZZZ",
    "ACTION": "get"
}
```

Acciones soportadas: `get`, `set` y `list`.

- Para `set` se deben incluir los campos del tuple `CorporateData`.
- Para `list` no se indica `ID`.

## Cliente observer

Suscribirse para recibir notificaciones de cambios:

```sh
python src/observerclient.py {-s=hostname} {-p=port} {-o=output.json} {-v}
```

Si no se informan host y puerto, se toman `localhost` y `8080`. El cliente mantiene el puerto abierto y reintenta la conexión cada 30 segundos (parametrizable) si el socket se interrumpe.