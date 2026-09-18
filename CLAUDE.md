# blog-ai

## Regla de proceso: toda función nueva explica su caso vacío

**Toda función nueva lleva, justo encima, un comentario que explica qué devuelve cuando no
encuentra resultados.**

Aplica a funciones y a métodos, `def` y `async def`. El comentario empieza por
`Sin resultados:` y va **pegado** a la declaración: una línea en blanco en medio lo separa
de la función y ya no cuenta.

```python
# Sin resultados: devuelve una lista vacía, no None.
async def embeber(textos: list[str]) -> list[list[float]]:
    ...

# Sin resultados: devuelve la frase «No lo encuentro en los artículos del blog».
async def responder(consulta: str, resultados: list[ResultadoBusqueda]) -> str:
    ...
```

El docstring no sirve para esto: va debajo del `def` y la regla pide encima. Los dos
conviven, el comentario para el caso vacío y el docstring para lo demás. Si la función no
busca nada, el comentario lo dice igualmente: `# Sin resultados: no aplica, no consulta
nada.` El caso vacío es lo que se escribe, no el que se salta.

La regla es para código nuevo. El que ya estaba en el repositorio no hay que ir a
comentarlo.

### Qué la hace cumplir

`.claude/hooks/regla_sin_resultados.py` recorre los `.py` que has tocado, se queda solo con
las líneas que no están en `HEAD` y avisa de cada función sin su comentario, con archivo y
línea.

- **Automático:** el hook `PostToolUse` de `.claude/settings.json` lo lanza después de cada
  `Write`, `Edit` y `Bash`. Si falta algún comentario, sale con código 2 y el aviso vuelve
  a Claude, que tiene que arreglarlo antes de seguir.
- **A mano:** `make regla`. Sale 0 y en silencio si todo está en orden.
