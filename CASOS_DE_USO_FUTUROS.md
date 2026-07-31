# Backlog de casos de uso de IA — priorizado

> Responde a *"apoyar en la exploración de nuevos casos de uso de IA para el
> programa"*. Cada idea está evaluada por **impacto**, **esfuerzo** y **riesgo**,
> no por lo llamativa que suena.

## Cómo se prioriza

```
Prioridad = (horas ahorradas al mes × criticidad) / (esfuerzo × riesgo)
```

Y una regla que descarta ideas antes de empezar:

> **Si un error del sistema puede dañar a una familia, a un menor o a la
> reputación del Club, la IA no decide: solo propone.**

---

## 🟢 Listos para construir (impacto alto, riesgo bajo)

### 1. Transcripción y resumen de reuniones
**Qué:** subir el audio de una reunión → transcripción + resumen con acuerdos y
responsables → se envía al equipo y se archiva.
**Ahorra:** ~4 h/mes de redacción de actas.
**Riesgo:** bajo (solo uso interno). **Esfuerzo:** bajo (Whisper + Claude).

### 2. Respuestas frecuentes con base de conocimiento
**Qué:** el clasificador ya identifica el tipo de consulta; agregar una base con
las respuestas oficiales (horarios, costos, requisitos) para que el borrador
salga con los datos correctos ya puestos.
**Ahorra:** ~6 h/mes y elimina el "te confirmo el horario" que nunca llega.
**Riesgo:** medio → mitigación: la base la mantiene coordinación, la IA solo cita.

### 3. Reporte mensual para donantes
**Qué:** el reporte semanal ya existe; generar la versión mensual con el formato
que piden los auspiciadores (impacto, beneficiarios, fotos del período).
**Ahorra:** ~5 h/mes en cada cierre.
**Riesgo:** bajo (siempre pasa por revisión antes de enviarse).

---

## 🟡 Vale la pena explorar (impacto alto, requiere cuidado)

### 4. Detección temprana de deserción
**Qué:** con el histórico de asistencia, señalar qué participantes llevan dos
faltas seguidas para que el equipo los contacte antes de que abandonen.
**Impacto:** alto — retener es más barato que captar.
**Riesgo:** **alto**. Involucra datos de menores y puede etiquetar mal a una
familia. Reglas obligatorias: solo agregados para el análisis, la lista de
contacto la revisa una persona, y **nunca** se comunica una "predicción" a la
familia. Empezar con un umbral simple (dos faltas) antes que con un modelo.

### 5. Asistente de búsqueda sobre la documentación interna
**Qué:** preguntar en lenguaje natural "¿cómo se reprocesa un lead fallido?" y
que responda citando la ficha correspondiente.
**Impacto:** medio-alto cuando el equipo crece.
**Requisito previo:** que las fichas estén completas (proyecto 04 ✅).

### 6. Traducción de materiales a quechua/aimara
**Qué:** versiones de convocatorias y materiales para comunidades andinas.
**Riesgo:** alto en calidad — **obligatorio** que un hablante nativo revise.
La IA hace el primer borrador, nunca la versión final.

---

## 🔴 Descartados por ahora (y por qué)

| Idea | Por qué no |
| --- | --- |
| Chatbot público que responde solo | Ante una consulta sensible de una familia, un error del bot cuesta más que las horas que ahorra |
| Generación de imágenes de niños con IA | Inaceptable: representar beneficiarios con imágenes sintéticas es engañoso |
| Puntuación automática de leads que descarte algunos | Un lead descartado por error es una familia que no recibió respuesta |
| Publicación 100 % automática sin revisión | Contradice la política de revisión del proyecto 02 |

---

## Próximo paso sugerido

Empezar por **el caso 1** (transcripción de reuniones): impacto inmediato,
riesgo casi nulo y sirve para que el equipo vea el valor de la IA en algo
cotidiano antes de tocar procesos sensibles. Construir confianza primero,
automatizar lo delicado después.
