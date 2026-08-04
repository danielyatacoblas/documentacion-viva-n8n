# Plantilla · Ficha de automatización

> Estándar de documentación del Club STEM. **Las secciones 2 a 6 las genera
> el script** leyendo el JSON del workflow (`python scripts/generar_fichas.py`);
> las secciones 1 y 7 las escribe una persona.
>
> Regla: si el workflow cambia, se regenera la ficha. Documentación que hay
> que actualizar a mano es documentación que va a mentir.

---

# Ficha · [Nombre del workflow]

> Generada automáticamente desde el JSON del workflow.
> Última revisión: **[fecha]** · Responsable: **[área o persona]**

## 1. Qué hace  *humano*

Un párrafo en lenguaje no técnico: qué problema resuelve, para quién, y qué
pasaría si no existiera. Debe entenderlo alguien que no sabe qué es n8n.

Incluir siempre un **"Por qué existe"**: el contexto se pierde antes que el
código.

## 2. Dónde corre  *automático*

Instancia, nombre del archivo del workflow y etiquetas.

## 3. Cuándo se dispara  *automático*

Webhook (con su método y ruta), programación (traducida a lenguaje humano:
"todos los días a las 08:00"), o manual.

## 4. Servicios que toca  *automático*

Lista de servicios externos (Sheets, Mailchimp, Telegram, APIs) y los
**parámetros pendientes de configurar** detectados en el JSON.

## 5. Pasos (orden de ejecución)  *automático*

Los nodos en el orden real en que corren, siguiendo las conexiones, con las
notas que tenga cada nodo.

## 6. Riesgos detectados automáticamente  *automático*

Nodos que llaman a servicios externos **sin ruta de error declarada**: si esa
API falla, la ejecución se detiene.

## 7. Qué hacer si falla  *humano*

Lista numerada de **síntoma → qué revisar → cómo arreglarlo**. Esta es la
sección que salva a quien recibe una alerta un sábado.

Debe cubrir como mínimo:

1. Qué se ve cuando falla (dónde aparece el error)
2. Las 2-3 causas más probables, en orden de frecuencia
3. Cómo reprocesar lo que quedó pendiente
4. Qué **no** hacer (los arreglos que rompen más de lo que solucionan)

---

## Convenciones del estándar

| Regla | Motivo |
| --- | --- |
| Una ficha por workflow, nombre `ficha_<tema>.md` | Fácil de encontrar |
| Nombres de workflow `[área] Acción — detalle` | Ordenan solos en la lista de n8n |
| Toda credencial va al credential store, nunca al JSON | El JSON se versiona en git |
| Cada nodo de servicio externo declara su ruta de error | Que nada falle en silencio |
| Las notas van en el campo `notes` del nodo | El script las levanta a la ficha |

## Dónde viven las fichas

- **En el repo** (`fichas/`): versionadas, revisables en cada cambio.
- **En Drive/Notion**: copia publicada para el equipo no técnico.

La copia se genera desde el repo, nunca al revés: una sola fuente de verdad.
