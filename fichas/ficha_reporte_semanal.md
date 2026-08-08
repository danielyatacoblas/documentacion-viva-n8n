# Ficha · Club STEM · Reporte semanal automático

> Generada automáticamente desde el JSON del workflow.<br>
> Regenerar con: `python scripts/generar_fichas.py`<br>
> Responsable: **Coordinación**<br>
> Última generación: **2026-08-08**

## 1. Qué hace

Cada lunes a las 08:00 lee los KPIs publicados por el dashboard, separa lo que mejoró de lo que bajó, arma la lista de qué revisar esa semana y envía el resumen por correo al equipo.

**Por qué existe:** antes el resumen se armaba a mano los lunes y, cuando había mucho trabajo, simplemente no se hacía.

## 2. Dónde corre

n8n · instancia del Club STEM  
Workflow: `workflow_reporte_semanal.json`
Etiquetas: club-stem, reportes

## 3. Cuándo se dispara

- **Cada lunes 08:00** — Programado — cada lunes a las 08:00

## 4. Servicios que toca

- Gmail
- HTTP (API externa)
- Telegram

> **Antes de activarlo hay que configurar:**

- `REEMPLAZAR_CHAT_ID`
- `REEMPLAZAR_CORREO_EQUIPO`
- `REEMPLAZAR_URL_VERCEL`

## 5. Pasos (orden de ejecución)

1. **Cada lunes 08:00** · Programado
2. **Leer KPIs del dashboard** · HTTP (API externa)  
   _El dashboard del proyecto 03 publica este JSON_
3. **Armar el resumen** · Código
4. **Enviar al equipo** · Gmail
5. **Avisar si no se pudo enviar** · Telegram

## 6. Riesgos detectados automáticamente

Estos nodos llaman a servicios externos y **no declaran ruta de error**; si la API falla, la ejecución se detiene:

- Leer KPIs del dashboard
- Avisar si no se pudo enviar

## 7. Qué hacer si falla

1. **No llegó el reporte del lunes:** revisar en n8n → Executions si el schedule corrió; si no, verificar que el workflow esté activo.
2. **Error al leer los KPIs:** confirmar que la URL del dashboard responde y que `datos.json` se generó (workflow de GitHub Actions).
3. **El reporte llegó vacío:** el `datos.json` existe pero sin KPIs; revisar el pipeline del proyecto 03.
4. **Generarlo a mano:** `python scripts/simular_asistente.py` deja el reporte en `reportes/reporte_semanal.md`.

---

*Ficha derivada de 5 nodos. Los campos 1 y 7 los escribe una
persona: el resto se regenera solo cuando el workflow cambia.*
