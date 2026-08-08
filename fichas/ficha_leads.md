# Ficha · Club STEM · Leads (producción)

> Generada automáticamente desde el JSON del workflow.<br>
> Regenerar con: `python scripts/generar_fichas.py`<br>
> Responsable: **Comunicaciones**<br>
> Última generación: **2026-08-08**

## 1. Qué hace

Recibe los leads del formulario web y de Podium, los limpia (normaliza teléfono y correo), descarta duplicados contra el CRM, los clasifica en talleres / voluntariado / donación / general y dispara tres acciones: registrar en la hoja CRM, suscribir al newsletter con la etiqueta del segmento y avisar al equipo por Telegram. Si nadie contacta al lead en 48 horas, envía un recordatorio automático.

**Por qué existe:** antes cada lead se copiaba a mano a la hoja y a la lista de correo; se perdían leads y se duplicaban registros.

## 2. Dónde corre

n8n · instancia del Club STEM  
Workflow: `workflow_leads.json`
Etiquetas: club-stem, leads

## 3. Cuándo se dispara

- **Webhook · Nuevo lead** — Webhook (lo dispara un sistema externo) — `POST /lead`
- **Cada 6 horas** — Programado — cada 6 horas

## 4. Servicios que toca

- Google Sheets
- Mailchimp
- Telegram

> **Antes de activarlo hay que configurar:**

- `REEMPLAZAR_CHAT_ID`
- `REEMPLAZAR_ID_HOJA`
- `REEMPLAZAR_ID_LISTA`

## 5. Pasos (orden de ejecución)

1. **Webhook · Nuevo lead** · Webhook (lo dispara un sistema externo)
2. **CRM · Leer hoja** · Google Sheets  
   _Hoja CRM: columnas nombre,email,telefono,mensaje,canal,fecha,segmento,estado_
3. **Procesar lead** · Código
4. **¿Es lead nuevo?** · Condición
5. **CRM · Registrar lead** · Google Sheets
6. **Duplicado · Solo log** · Sin operación
7. **Newsletter · Suscribir** · Mailchimp  
   _Alternativa gratuita: HTTP Request a la API de Brevo_
8. **Equipo · Avisar por Telegram** · Telegram
9. **Cada 6 horas** · Programado
10. **CRM · Leer para seguimiento** · Google Sheets
11. **Filtrar > 48 h sin contacto** · Código
12. **Equipo · Recordatorio de seguimiento** · Telegram

## 6. Riesgos detectados automáticamente

Estos nodos llaman a servicios externos y **no declaran ruta de error**; si la API falla, la ejecución se detiene:

- CRM · Leer hoja
- CRM · Registrar lead
- Newsletter · Suscribir
- Equipo · Avisar por Telegram
- CRM · Leer para seguimiento
- Equipo · Recordatorio de seguimiento

## 7. Qué hacer si falla

1. **No llegan avisos de leads nuevos:** revisar en n8n → Executions si el webhook está recibiendo. Si no hay ejecuciones, el formulario dejó de apuntar a la URL correcta.
2. **Error 403 de Google Sheets:** la credencial expiró. Reconectarla en n8n → Credentials → Google Sheets.
3. **Los leads llegan pero no se suscriben al newsletter:** revisar que el ID de lista de Mailchimp siga vigente.
4. **Llegan duplicados:** verificar que la hoja CRM conserve las columnas `email` y `telefono` con esos nombres exactos.
5. **Reproceso manual:** se puede reejecutar una ejecución fallida desde n8n → Executions → Retry.

---

*Ficha derivada de 12 nodos. Los campos 1 y 7 los escribe una
persona: el resto se regenera solo cuando el workflow cambia.*
