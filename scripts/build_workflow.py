#!/usr/bin/env python3
"""Construye los workflows n8n del asistente.

    python scripts/build_workflow.py

Genera:
  workflow_bandeja.json          → correo entrante → Claude → clasificación → hoja
  workflow_reporte_semanal.json  → cada lunes → KPIs → resumen → correo al equipo
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "workflows" / "src"
OUT = ROOT / "workflows"
HOJA = "REEMPLAZAR_ID_HOJA"


def _node(nid, name, ntype, tv, pos, params, extra=None):
    n = {"parameters": params, "id": nid, "name": name, "type": ntype,
         "typeVersion": tv, "position": pos}
    if extra:
        n.update(extra)
    return n


def build_bandeja(js: str) -> dict:
    nodes = [
        _node("imap", "Correo entrante", "n8n-nodes-base.emailReadImap", 2,
              [-260, 300],
              {"format": "simple", "options": {"allowUnauthorizedCerts": False}},
              {"notes": "Bandeja de contacto del Club. Credencial IMAP en n8n."}),
        _node("prep", "Preparar correo", "n8n-nodes-base.code", 2,
              [-40, 300],
              {"jsCode": (
                  "// Normaliza el correo entrante a la forma que espera el prompt\n"
                  "return $input.all().map((item) => {\n"
                  "  const j = item.json;\n"
                  "  const remitente = j.from || j.fromEmail || '';\n"
                  "  return { json: { correo: {\n"
                  "    id: j.messageId || j.id || String(Date.now()),\n"
                  "    remitente,\n"
                  "    nombre: (remitente.split('@')[0] || '').split('.')[0],\n"
                  "    asunto: j.subject || '',\n"
                  "    cuerpo: (j.textPlain || j.text || '').slice(0, 4000),\n"
                  "  }}};\n"
                  "});\n")}),
        _node("claude", "Claude · Clasificar y redactar", "n8n-nodes-base.httpRequest", 4.2,
              [180, 300],
              {"method": "POST", "url": "https://api.anthropic.com/v1/messages",
               # La API key va en una credencial de n8n (Header Auth con
               # x-api-key), nunca en el JSON: este archivo se versiona en git.
               "authentication": "genericCredentialType",
               "genericAuthType": "httpHeaderAuth",
               "sendHeaders": True,
               "headerParameters": {"parameters": [
                   {"name": "anthropic-version", "value": "2023-06-01"},
                   {"name": "content-type", "value": "application/json"}]},
               "sendBody": True, "specifyBody": "json",
               "jsonBody": "={{ JSON.stringify({ model: 'claude-sonnet-5', "
                           "max_tokens: 700, messages: [{ role: 'user', content: "
                           "'Clasifica este correo del Club STEM y redacta un "
                           "borrador de respuesta. Devuelve SOLO JSON con las claves "
                           "categoria, prioridad, urgente, requiere_humano, borrador.\\n\\n' "
                           "+ 'Asunto: ' + $json.correo.asunto + '\\n' + $json.correo.cuerpo }] }) }}",
               "options": {}},
              {"credentials": {"httpHeaderAuth": {"name": "Anthropic API key"}},
               "onError": "continueRegularOutput",
               "notes": "Si la IA falla, el siguiente nodo clasifica por reglas"}),
        _node("clasif", "Clasificar (con respaldo por reglas)", "n8n-nodes-base.code", 2,
              [420, 300], {"jsCode": js},
              {"notes": "Aplica la regla dura: quejas y alianzas siempre requieren persona"}),
        _node("hoja", "Bandeja · Guardar en hoja", "n8n-nodes-base.googleSheets", 4.5,
              [660, 300],
              {"operation": "append",
               "documentId": {"__rl": True, "value": HOJA, "mode": "id"},
               "sheetName": {"__rl": True, "value": "Bandeja", "mode": "name"},
               "columns": {"mappingMode": "autoMapInputData", "value": {}},
               "options": {}}),
        _node("if-urg", "¿Requiere persona?", "n8n-nodes-base.if", 2,
              [880, 300],
              {"conditions": {
                  "options": {"caseSensitive": False, "leftValue": "",
                              "typeValidation": "loose", "version": 2},
                  "conditions": [{"id": "u1", "leftValue": "={{ $json.requiere_humano }}",
                                  "rightValue": "true",
                                  "operator": {"type": "boolean", "operation": "true",
                                               "singleValue": True}}],
                  "combinator": "and"},
               "options": {}}),
        _node("aviso", "Avisar al equipo", "n8n-nodes-base.telegram", 1.2,
              [1120, 220],
              {"chatId": "REEMPLAZAR_CHAT_ID",
               "text": "= Correo que necesita respuesta humana "
                       "[{{ $json.categoria }} · {{ $json.prioridad }}]\n"
                       "De: {{ $json.remitente }}\nAsunto: {{ $json.asunto }}",
               "additionalFields": {}}),
        _node("espera", "Queda en cola para revisión", "n8n-nodes-base.noOp", 1,
              [1120, 400], {},
              {"notes": "El borrador espera aprobación; nunca se envía solo"}),
    ]
    connections = {
        "Correo entrante": {"main": [[{"node": "Preparar correo", "type": "main", "index": 0}]]},
        "Preparar correo": {"main": [[{"node": "Claude · Clasificar y redactar", "type": "main", "index": 0}]]},
        "Claude · Clasificar y redactar": {"main": [[{"node": "Clasificar (con respaldo por reglas)", "type": "main", "index": 0}]]},
        "Clasificar (con respaldo por reglas)": {"main": [[{"node": "Bandeja · Guardar en hoja", "type": "main", "index": 0}]]},
        "Bandeja · Guardar en hoja": {"main": [[{"node": "¿Requiere persona?", "type": "main", "index": 0}]]},
        "¿Requiere persona?": {"main": [
            [{"node": "Avisar al equipo", "type": "main", "index": 0}],
            [{"node": "Queda en cola para revisión", "type": "main", "index": 0}]]},
    }
    return {"id": "clubstembandeja",
            "name": "Club STEM · Bandeja de entrada con IA",
            "nodes": nodes, "connections": connections,
            "settings": {"executionOrder": "v1"}, "pinData": {},
            "tags": [{"name": "club-stem"}, {"name": "ia"}]}


def build_reporte() -> dict:
    nodes = [
        _node("cron", "Cada lunes 08:00", "n8n-nodes-base.scheduleTrigger", 1.2,
              [-260, 300],
              {"rule": {"interval": [{"field": "cronExpression",
                                      "expression": "0 8 * * 1"}]}}),
        _node("kpis", "Leer KPIs del dashboard", "n8n-nodes-base.httpRequest", 4.2,
              [-40, 300],
              {"url": "https://REEMPLAZAR_URL_VERCEL/datos.json",
               "options": {}},
              {"notes": "El dashboard del proyecto 03 publica este JSON"}),
        _node("redact", "Armar el resumen", "n8n-nodes-base.code", 2,
              [180, 300],
              {"jsCode": (
                  "// Ordena los KPIs por magnitud del cambio y separa mejoras de caidas\n"
                  "const RELEVANTE = 5, FUERTE = 15;\n"
                  "const kpis = $input.first().json.kpis || [];\n"
                  "const esBueno = (k) => k.mejor === 'abajo' ? k.variacion < 0 : k.variacion > 0;\n"
                  "const mejoras = [], caidas = [], revisar = [];\n"
                  "for (const k of kpis) {\n"
                  "  const v = Math.abs(k.variacion || 0);\n"
                  "  if (v < RELEVANTE) continue;\n"
                  "  if (esBueno(k)) mejoras.push(k); else {\n"
                  "    caidas.push(k);\n"
                  "    if (v >= FUERTE) revisar.push(k);\n"
                  "  }\n"
                  "}\n"
                  "const linea = (k) => `- ${k.etiqueta}: ${k.valor}${k.unidad} "
                  "(${k.variacion > 0 ? '+' : ''}${k.variacion} %)`;\n"
                  "const texto = [\n"
                  "  'Reporte semanal · Club STEM', '',\n"
                  "  'Lo que mejoró:', ...mejoras.map(linea), '',\n"
                  "  'Lo que bajó:', ...caidas.map(linea), '',\n"
                  "  'Qué revisar esta semana:',\n"
                  "  ...(revisar.length ? revisar.map(linea)\n"
                  "      : ['Sin caídas relevantes: buen momento para probar algo nuevo.']),\n"
                  "].join('\\n');\n"
                  "return [{ json: { texto, mejoras: mejoras.length, "
                  "caidas: caidas.length, revisar: revisar.length } }];\n")}),
        _node("mail", "Enviar al equipo", "n8n-nodes-base.gmail", 2.1,
              [420, 300],
              {"sendTo": "REEMPLAZAR_CORREO_EQUIPO",
               "subject": "=Reporte semanal Club STEM",
               "message": "={{ $json.texto }}",
               "options": {}},
              {"onError": "continueErrorOutput"}),
        _node("err", "Avisar si no se pudo enviar", "n8n-nodes-base.telegram", 1.2,
              [660, 420],
              {"chatId": "REEMPLAZAR_CHAT_ID",
               "text": " No se pudo enviar el reporte semanal por correo.",
               "additionalFields": {}}),
    ]
    connections = {
        "Cada lunes 08:00": {"main": [[{"node": "Leer KPIs del dashboard", "type": "main", "index": 0}]]},
        "Leer KPIs del dashboard": {"main": [[{"node": "Armar el resumen", "type": "main", "index": 0}]]},
        "Armar el resumen": {"main": [[{"node": "Enviar al equipo", "type": "main", "index": 0}]]},
        "Enviar al equipo": {"main": [[], [{"node": "Avisar si no se pudo enviar", "type": "main", "index": 0}]]},
    }
    return {"id": "clubstemreporte",
            "name": "Club STEM · Reporte semanal automático",
            "nodes": nodes, "connections": connections,
            "settings": {"executionOrder": "v1"}, "pinData": {},
            "tags": [{"name": "club-stem"}, {"name": "reportes"}]}


def main():
    js = (SRC / "clasificar_correo.js").read_text(encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    for nombre, wf in (("workflow_bandeja.json", build_bandeja(js)),
                       ("workflow_reporte_semanal.json", build_reporte())):
        p = OUT / nombre
        p.write_text(json.dumps(wf, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ {p.relative_to(ROOT)} — {len(wf['nodes'])} nodos")


if __name__ == "__main__":
    main()
