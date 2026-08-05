<h1 align="center">Documentación viva + asistente de IA</h1>

<p align="center"><i>La documentación se escribe sola leyendo los workflows</i></p>

<p align="center">
  <img alt="tests" src="https://img.shields.io/badge/tests-47%20passed-brightgreen">
  <img alt="fichas" src="https://img.shields.io/badge/fichas-5%20autogeneradas-blueviolet">
  <img alt="IA" src="https://img.shields.io/badge/IA-Claude%20(opcional">-8A63D2) <img alt="licencia" src="https://img.shields.io/badge/licencia-MIT-blue">
</p>

---

## Demo en video

<!-- ────────────────────────────────────────────────────────────────────
     ESPACIO RESERVADO PARA EL VIDEO

     Cuando lo tengas subido a YouTube (recomiendo "no listado"), reemplaza
     este bloque por la miniatura clickeable:

     [![Ver la demo](https://img.youtube.com/vi/TU_VIDEO_ID/maxresdefault.jpg)](https://youtu.be/TU_VIDEO_ID)

     Y borra el aviso de abajo.
     ──────────────────────────────────────────────────────────────────── -->

> *Video de la demo en camino.* Mientras tanto, el proyecto corre completo
> en local en menos de dos minutos siguiendo [Probarlo](#probarlo-en-2-minutos).

---

## El problema

La documentación se escribe una vez, el flujo cambia diez veces, y a los tres meses la documentación miente. Cuando algo falla un sábado, quien está de turno no tiene dónde mirar.

## Qué hace este proyecto

1. **Fichas que se derivan del artefacto real**: el generador lee el JSON del workflow y extrae disparadores, servicios, parámetros pendientes, orden real de ejecución y riesgos.
2. **Solo dos campos los escribe una persona**: qué hace y qué hacer si falla. Todo lo demás se regenera con un comando.
3. **Bandeja de entrada inteligente**: clasifica correos y redacta borradores, pero quejas, alianzas y urgencias siempre las contesta alguien.
4. **Reporte semanal** en lenguaje natural, diseñado para señalar problemas.

---

## Cómo funciona

```mermaid
flowchart TD
    subgraph A ["Documentación viva"]
        W["workflow.json"] --> G["Generador"]
        G --> F["Ficha en Markdown"]
        H["Qué hace<br/>Qué hacer si falla"] --> F
    end
    subgraph B ["Bandeja inteligente"]
        M["Correo entrante"] --> K["Clasificar + redactar"]
        K --> D{"¿Queja, alianza<br/>o urgencia?"}
        D -->|sí| P["Lo contesta<br/>una persona"]
        D -->|no| Q["Borrador listo<br/>para revisar"]
    end
    subgraph C ["Reporte semanal"]
        R["KPIs del panel"] --> S["Qué mejoró<br/>qué empeoró<br/>qué revisar"]
    end
```

---

## Probarlo en 2 minutos

```bash
pip install pytest
python scripts/generar_correos.py     # 30 correos ficticios
python scripts/generar_fichas.py      # documentación de los workflows reales
python scripts/simular_asistente.py   # las tres automatizaciones
python -m pytest -v                   # 47 tests
```

Funciona **sin API key**: el clasificador tiene un motor de reglas
equivalente. Si la IA falla, el sistema cae a él y lo deja registrado.

---

### El sistema se documenta a sí mismo

De las cinco fichas que genera, **dos son de sus propios workflows**. Y la integración continua verifica que sigan al día: si alguien cambia un flujo y no regenera la documentación, el build falla.

El generador traduce lo técnico a lenguaje humano — `0 8 * * 1` se convierte en *"cada lunes a las 08:00"*— y señala riesgos que nadie escribiría a mano, como los nodos que llaman a servicios externos sin declarar qué hacer si fallan.

---

## Estructura

```
├── src/
│   ├── fichas.py             # analiza el JSON de n8n y genera la ficha
│   ├── clasificador.py       # bandeja: reglas + Claude opcional
│   └── reporte.py            # resumen semanal en lenguaje natural
├── fichas/                   # 5 fichas generadas (documentación viva)
├── workflows/                # 2 workflows n8n + su código fuente
├── scripts/                  # data ficticia y simulación
└── tests/                    # 47 tests
```

---

## Flujo de trabajo con Git

El repositorio sigue **Git Flow**: `main` siempre desplegable, `develop` como
integración, y una rama por cambio. Los merges son `--no-ff` para que cada
funcionalidad quede como un bloque legible en el historial, y cada versión
lleva su tag.

```mermaid
gitGraph
   commit id: "chore: repo setup"
   branch develop
   checkout develop
   branch feature/core
   commit id: "feat: core logic"
   checkout develop
   merge feature/core
   branch feature/tests
   commit id: "test: suite"
   checkout develop
   merge feature/tests
   checkout main
   merge develop tag: "v1.0.0"
   checkout develop
   branch fix/review
   commit id: "fix: review findings"
   checkout develop
   merge fix/review
   checkout main
   merge develop tag: "v1.1.0"
```

| Rama | Para qué |
| --- | --- |
| `main` | Solo versiones liberadas. Cada merge lleva su tag. |
| `develop` | Integración de todo lo terminado. |
| `feature/*` | Una funcionalidad nueva. |
| `fix/*` | Una corrección concreta. |
| `release/*` | Preparación de la versión, luego se fusiona a `main` y `develop`. |

Los mensajes siguen [Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `test:`, `docs:`, `chore:` — con el porqué del cambio en el
cuerpo, no solo el qué.

---

## Documentación

| Documento | Contenido |
| --- | --- |
| [`GUIA.md`](GUIA.md) | Guía técnica completa: arquitectura, decisiones, configuración y puesta en marcha |
| [`PLANTILLA_FICHA.md`](PLANTILLA_FICHA.md) | El estándar de documentación: qué genera la máquina y qué escribe una persona |
| [`CASOS_DE_USO_FUTUROS.md`](CASOS_DE_USO_FUTUROS.md) | Backlog de IA priorizado por impacto, esfuerzo y riesgo, con lo descartado y su motivo |

---

## Licencia

[MIT](LICENSE) · Daniel Yataco Blas

> Proyecto de demostración construido con **datos ficticios**. No es un sistema
> en producción de ninguna organización.
