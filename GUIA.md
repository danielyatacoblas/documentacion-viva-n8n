# 04 · Asistente IA + documentación viva

[![tests](https://img.shields.io/badge/tests-47%20passed-brightgreen)](tests/)
[![fichas](https://img.shields.io/badge/fichas-5%20autogeneradas-blueviolet)](fichas/)
[![IA](https://img.shields.io/badge/IA-Claude%20(opcional)-8A63D2)](src/clasificador.py)
[![licencia](https://img.shields.io/badge/licencia-MIT-blue)](LICENSE)

**Qué requisitos del aviso cubre:** implementar IA generativa (incluyendo **Claude Code**)
para optimizar flujos internos · explorar nuevos casos de uso de IA ·
**documentar los sistemas para que el equipo pueda mantenerlos a futuro**.

---

## Tres automatizaciones + el sistema que las mantiene documentadas

### A · Documentación viva — *la pieza central*

El problema real: la documentación se escribe una vez, el workflow cambia diez
veces, y a los tres meses la documentación miente.

**La solución: derivar la ficha del artefacto real.** El generador lee el JSON
del workflow y extrae solo lo que se puede saber sin intervención humana:

```
python scripts/generar_fichas.py

  ✓ fichas/ficha_leads.md              (del proyecto 01)
  ✓ fichas/ficha_generar_contenido.md  (del proyecto 02)
  ✓ fichas/ficha_publicar_redes.md     (del proyecto 02)
  ✓ fichas/ficha_bandeja_ia.md         (de este proyecto)
  ✓ fichas/ficha_reporte_semanal.md    (de este proyecto)
```

| Sección de la ficha | Quién la escribe |
| --- | --- |
| Qué hace / por qué existe | Humano |
| Dónde corre y con qué etiquetas | Del JSON |
| **Cuándo se dispara** (traduce `0 8 * * *` → "todos los días a las 08:00") | Del JSON |
| **Servicios que toca** y parámetros `REEMPLAZAR_*` pendientes | Del JSON |
| **Pasos en orden real de ejecución** (recorre las conexiones) | Del JSON |
| **Riesgos**: nodos externos sin ruta de error declarada | Del JSON |
| Qué hacer si falla | Humano |

> El sistema **se documenta a sí mismo**: dos de las cinco fichas son de sus
> propios workflows.

### B · Bandeja de entrada inteligente

```
Correo entrante → Claude clasifica + redacta borrador → hoja priorizada
                       │
                       ├─ queja / alianza / urgencia → aviso al equipo (lo contesta una persona)
                       └─ consulta normal → borrador listo para revisar y enviar
```

Sobre los 30 correos ficticios:

```
Correos procesados: 30
Por categoría: inscripcion=14, alianza=5, otro=4, queja=2, voluntariado=2, spam=2, administrativo=1
Prioridad alta: 3 · media: 18 · baja: 9
Requieren persona sí o sí: 8 (quejas, alianzas y urgencias)
Spam filtrado: 2
Borradores listos para revisar: 28
```

**La regla dura está en el código, no solo en el README:** una queja o una
alianza siempre marcan `requiere_humano`, aunque la IA diga lo contrario — y el
nodo de n8n aplica la misma regla. Hay tests para ambos.

### C · Reporte semanal automático

Lee los KPIs del dashboard (proyecto 03) y redacta el resumen del lunes.
**Diseñado para señalar problemas**, no para felicitar:

```markdown
### Lo que bajó
- **Clics de email**: 4.1 % (-24.0 %)
- **Beneficiarios activos**: 58 (-15.9 %)

### Qué revisar esta semana
1. **Clics de email** cayó 24.0 %: revisar el contenido y la ubicación del
   llamado a la acción dentro del correo.
2. **Beneficiarios activos** cayó 15.9 %: confirmar que la asistencia se está
   registrando completa.

### Dato de la semana
El canal que mejor convierte es **referido** (66.7 %) y el que menos,
**facebook** (20.9 %). La diferencia es de 45.8 puntos.
```

---

## Probarlo en 2 minutos (sin API key)

```bash
pip install pytest
python scripts/generar_correos.py       # 30 correos ficticios
python scripts/generar_fichas.py        # documentación de los workflows reales
python scripts/simular_asistente.py     # las tres automatizaciones
python -m pytest tests/ -v              # 47 tests
```

Con Claude (opcional): `pip install anthropic`, exporta `ANTHROPIC_API_KEY` y
usa `--motor claude`. **Si la API falla, el sistema no se cae**: cae al motor de
reglas y lo deja registrado en la columna `motor`.

---

## Con n8n

```bash
docker compose up -d      # http://localhost:5678
```

| Workflow | Nodos | Qué hace |
| --- | --- | --- |
| `workflow_bandeja.json` | 8 | IMAP → Claude → clasificación con respaldo por reglas → hoja → aviso si requiere persona |
| `workflow_reporte_semanal.json` | 5 | Lunes 08:00 → lee KPIs → arma resumen → correo al equipo (con aviso si falla el envío) |

---

## Cómo uso Claude Code (lo que el aviso pide explícitamente)

Este portafolio completo se construyó con Claude Code, y de ahí salen prácticas
que aplicaría desde el primer día en el Club:

- **Lógica duplicada, verificada automáticamente.** Cuando un flujo vive en
  Python *y* en un nodo de n8n, hay un test que ejecuta ambos y compara los
  resultados (`test_paridad_js.py` en el proyecto 01). Sin eso, las dos copias
  se desincronizan en silencio.
- **La política se convierte en test.** "Nada se publica sin aprobación" no es
  una promesa del README: es `pytest.raises(ErrorAprobacion)`.
- **Documentación derivada del artefacto**, no escrita en paralelo (este proyecto).
- **Data ficticia con semilla fija** para que cualquiera reproduzca los mismos
  resultados sin datos reales de personas.

---

## Estructura

```
04_asistente_ia_documentacion/
├── src/
│   ├── fichas.py             # analiza el JSON de n8n y genera la ficha
│   ├── clasificador.py       # bandeja: reglas + Claude opcional
│   └── reporte.py            # resumen semanal en lenguaje natural
├── scripts/
│   ├── generar_correos.py    # 30 correos ficticios (quejas, spam, alianzas)
│   ├── generar_fichas.py     # registro de workflows + campos humanos
│   ├── simular_asistente.py  # corre las tres automatizaciones
│   └── build_workflow.py
├── workflows/                # 2 workflows n8n + su código fuente JS
├── fichas/                   # 5 fichas generadas (documentación viva)
├── tests/                    # 41 tests
├── PLANTILLA_FICHA.md        # el estándar de documentación
└── CASOS_DE_USO_FUTUROS.md   # backlog priorizado por impacto/esfuerzo/riesgo
```

---

## Qué está probado

| Área | Tests |
| --- | --- |
| Clasificación | 9 tipos de correo reales → categoría correcta; ignora tildes y mayúsculas |
| **Regla dura** | **Quejas, alianzas y urgencias SIEMPRE requieren persona** |
| Spam | Se detecta y **no** genera borrador de respuesta |
| Prioridad y orden | La queja va primera, el spam al final |
| Fichas | Detecta disparadores, servicios, `REEMPLAZAR_*` y nodos sin ruta de error |
| Orden de nodos | Recorre cada cadena completa; ningún nodo se pierde |
| Cron | `0 8 * * *` → "todos los días a las 08:00" |
| Reporte | Una baja en "días a respuesta" cuenta como **mejora** (menos es mejor) |
| Reporte | No inventa números y siempre dice algo útil, incluso si todo va bien |

---

## Estado

 **Funcional y probado en local.** 47 tests en verde, 5 fichas generadas desde
workflows reales, 30 correos ficticios y dos workflows n8n importables.
