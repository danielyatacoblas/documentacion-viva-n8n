# Ficha · Club STEM · Bandeja de entrada con IA

> Generada automáticamente desde el JSON del workflow.
> Regenerar con: `python scripts/generar_fichas.py`
> Responsable: **Coordinación**
> Última generación: **2026-07-31**

## 1. Qué hace

Lee la bandeja de contacto del Club, pide a Claude que clasifique cada correo (inscripción, voluntariado, alianza, queja, administrativo, spam) y redacte un borrador de respuesta, y deja todo en una hoja priorizada. Si el correo es una queja, una propuesta de alianza o trae señales de urgencia, avisa al equipo por Telegram para que lo conteste una persona.

**Ningún correo se responde solo:** el borrador siempre espera revisión. Si la API de Claude falla, un nodo de respaldo clasifica por reglas para que ningún correo se quede sin procesar.

## 2. Dónde corre

n8n · instancia del Club STEM  
Workflow: `workflow_bandeja.json`
Etiquetas: club-stem, ia

## 3. Cuándo se dispara

- **Correo entrante** — Correo entrante (IMAP)

## 4. Servicios que toca

- Google Sheets
- HTTP (API externa)
- Telegram

> ⚠️ **Antes de activarlo hay que configurar:**

- `REEMPLAZAR_CHAT_ID`
- `REEMPLAZAR_ID_HOJA`

## 5. Pasos (orden de ejecución)

1. **Correo entrante** · Correo entrante (IMAP)  
   _Bandeja de contacto del Club. Credencial IMAP en n8n._
2. **Preparar correo** · Código
3. **Claude · Clasificar y redactar** · HTTP (API externa)  
   _Si la IA falla, el siguiente nodo clasifica por reglas_
4. **Clasificar (con respaldo por reglas)** · Código  
   _Aplica la regla dura: quejas y alianzas siempre requieren persona_
5. **Bandeja · Guardar en hoja** · Google Sheets
6. **¿Requiere persona?** · Condición
7. **Avisar al equipo** · Telegram
8. **Queda en cola para revisión** · Sin operación  
   _El borrador espera aprobación; nunca se envía solo_

## 6. Riesgos detectados automáticamente

Estos nodos llaman a servicios externos y **no declaran ruta de error**; si la API falla, la ejecución se detiene:

- Bandeja · Guardar en hoja
- Avisar al equipo

## 7. Qué hacer si falla

1. **No entran correos:** revisar la credencial IMAP en n8n y que la casilla no haya cambiado de contraseña.
2. **Todos los correos salen como `otro`:** probablemente Claude está fallando y entró el respaldo por reglas. Revisar la API key.
3. **No llegan avisos de quejas:** revisar el chat ID de Telegram; el bot debe estar agregado al grupo.
4. **Procesar la bandeja a mano mientras tanto:** `python scripts/simular_asistente.py` clasifica el lote sin n8n.

---

*Ficha derivada de 8 nodos. Los campos 1 y 7 los escribe una
persona: el resto se regenera solo cuando el workflow cambia.*
