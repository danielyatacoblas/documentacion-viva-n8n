# Ficha · Club STEM · 2. Publicar aprobados

> Generada automáticamente desde el JSON del workflow.<br>
> Regenerar con: `python scripts/generar_fichas.py`<br>
> Responsable: **Comunicaciones**<br>
> Última generación: **2026-08-08**

## 1. Qué hace

Cada hora revisa la cola de aprobación y publica en Instagram, Facebook y LinkedIn **solo** los posts que una persona aprobó y cuya fecha programada ya llegó. Marca cada publicación como publicada; si la API de una red falla, marca el post como fallido, avisa al equipo y lo deja disponible para reintento.

**Regla de oro:** el filtro exige estado `aprobado` **y** un revisor registrado. Sin ambos, no publica. Está cubierto por tests.

## 2. Dónde corre

n8n · instancia del Club STEM  
Workflow: `workflow_2_publicar.json`
Etiquetas: club-stem, redes

## 3. Cuándo se dispara

- **Cada hora** — Programado — cada 1 hora

## 4. Servicios que toca

- Google Sheets
- HTTP (API externa)
- LinkedIn
- Telegram

> **Antes de activarlo hay que configurar:**

- `REEMPLAZAR_CHAT_ID`
- `REEMPLAZAR_ID_HOJA`
- `REEMPLAZAR_ORG_ID`

## 5. Pasos (orden de ejecución)

1. **Cada hora** · Programado
2. **Cola · Leer aprobados** · Google Sheets
3. **Filtrar publicables** · Código  
   _Solo pasa lo aprobado por una persona y con fecha cumplida_
4. **Enrutar por red** · Bifurcación
5. **Publicar · Instagram** · HTTP (API externa)  
   _Meta Graph API. Alternativa gratuita para demo: Buffer_
6. **Publicar · Facebook** · HTTP (API externa)
7. **Publicar · LinkedIn** · LinkedIn
8. **Otras redes (manual)** · Sin operación
9. **Cola · Marcar publicado** · Google Sheets
10. **Registrar fallo para reintento** · Google Sheets  
   _El post NO se pierde: queda visible para reintento manual_
11. **Avisar fallo al equipo** · Telegram

## 6. Riesgos detectados automáticamente

Estos nodos llaman a servicios externos y **no declaran ruta de error**; si la API falla, la ejecución se detiene:

- Cola · Leer aprobados
- Cola · Marcar publicado
- Registrar fallo para reintento
- Avisar fallo al equipo

## 7. Qué hacer si falla

1. **No publica nada:** revisar en la hoja que los posts tengan estado `aprobado` Y la columna `revisor` con un nombre.
2. **Error de token de Meta:** los tokens de página caducan cada 60 días. Regenerar en Meta for Developers y actualizar la credencial.
3. **Publicó a destiempo:** revisar la zona horaria de la instancia de n8n (`GENERIC_TIMEZONE=America/Lima`).
4. **Un post quedó en `fallido`:** corregir la causa y cambiar el estado de vuelta a `aprobado`; el workflow lo tomará en la siguiente corrida.
5. **Nunca** cambiar el estado directamente a `publicado` a mano: se pierde el registro de qué se publicó realmente.

---

*Ficha derivada de 11 nodos. Los campos 1 y 7 los escribe una
persona: el resto se regenera solo cuando el workflow cambia.*
