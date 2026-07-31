# Ficha · Club STEM · 1. Generar borradores con IA

> Generada automáticamente desde el JSON del workflow.
> Regenerar con: `python scripts/generar_fichas.py`
> Responsable: **Comunicaciones**
> Última generación: **2026-07-31**

## 1. Qué hace

Cada mañana revisa el calendario de contenido y, para cada pieza pendiente, genera con Claude un borrador adaptado a cada red social (largo, tono, emojis y hashtags propios de cada una). Deja los borradores en la hoja de aprobación y avisa al equipo.

**Importante:** este workflow NO publica nada. Solo redacta y encola para revisión humana.

## 2. Dónde corre

n8n · instancia del Club STEM  
Workflow: `workflow_1_generar.json`
Etiquetas: club-stem, redes

## 3. Cuándo se dispara

- **Cada día 08:00** — Programado — todos los días a las 08:00

## 4. Servicios que toca

- Google Sheets
- HTTP (API externa)
- Telegram

> ⚠️ **Antes de activarlo hay que configurar:**

- `REEMPLAZAR_CHAT_ID`
- `REEMPLAZAR_ID_HOJA`

## 5. Pasos (orden de ejecución)

1. **Cada día 08:00** · Programado
2. **Calendario · Leer contenidos** · Google Sheets  
   _Columnas: id,tipo,titulo,detalle,lugar,cupos,fecha,redes,objetivo_
3. **¿Falta generarlo?** · Condición
4. **Preparar prompts por red** · Código
5. **Claude · Redactar borrador** · HTTP (API externa)  
   _Credencial: Header Auth con x-api-key = ANTHROPIC_API_KEY.
Sin API key, usar el motor de plantillas del repo._
6. **Armar fila de aprobación** · Código
7. **Cola · Agregar para aprobación** · Google Sheets
8. **Avisar al equipo que hay borradores** · Telegram

## 6. Riesgos detectados automáticamente

Estos nodos llaman a servicios externos y **no declaran ruta de error**; si la API falla, la ejecución se detiene:

- Calendario · Leer contenidos
- Claude · Redactar borrador
- Cola · Agregar para aprobación
- Avisar al equipo que hay borradores

## 7. Qué hacer si falla

1. **No se generaron borradores:** revisar que las filas del calendario tengan la columna `generado` vacía y la fecha correcta.
2. **Error 401 de la API de Claude:** la API key venció o se agotó el crédito. Actualizar la credencial Header Auth en n8n.
3. **Los textos salen cortados:** subir `max_tokens` en el nodo de Claude o revisar que el prompt no pida más de lo que cabe.
4. **Mientras se arregla:** se puede generar con el motor de plantillas del repo (`python scripts/simular_publicacion.py`) y pegar los textos a mano en la hoja.

---

*Ficha derivada de 8 nodos. Los campos 1 y 7 los escribe una
persona: el resto se regenera solo cuando el workflow cambia.*
