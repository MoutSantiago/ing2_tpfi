# Uso

El servidor de aplicaciones se inicia con:

```sh
python src/SingletonProxyObserverTPFI/singletonproxyobserver.py {-p=port} {-v}
```

Si no se informa el puerto, se toma `*:8080`.

## Cliente singleton

Consultar o actualizar un registro de `CorporateData`:

```sh
python src/SingletonClient/singletonclient.py -i=input.json {-o=output.json} {-v}
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
python src/ObserverClient/observerclient.py {-s=hostname} {-p=port} {-o=output.json} {-r=seconds} {-v}
```

Si no se informan host y puerto, se toman `localhost` y `8080`. El cliente mantiene la conexión
abierta y reintenta cada 30 segundos (parametrizable con `-r`) si el socket se interrumpe.

Cuando el servidor registra la suscripción, responde con un mensaje de confirmación
(`{"UUID": "<uuid>", "ACTION": "ok"}`). El cliente lo muestra únicamente por la terminal y no lo
guarda en el archivo de salida.

### Formato de las notificaciones

Cada notificación se muestra por pantalla como un JSON multilínea. Si se configura `-o`, las
notificaciones se guardan dentro de un array JSON en ese archivo:

```json
[
    {
        "UUID": "123",
        "ACTION": "change",
        "ID": "1",
        "CUIT": "30-12345678-9"
    }
]
```

Si el archivo apuntado por `-o` tiene el formato antiguo (una notificación JSON por línea), el
cliente lo migra automáticamente al array.
