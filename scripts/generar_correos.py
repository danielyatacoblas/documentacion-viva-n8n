#!/usr/bin/env python3
"""Genera una bandeja de entrada ficticia (30 correos) para probar el clasificador.

    python scripts/generar_correos.py     # data/correos.json

Incluye a propósito los casos difíciles: quejas urgentes, spam disfrazado,
consultas ambiguas y una alianza empresarial (que siempre debe ir a una persona).
"""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "correos.json"

random.seed(5)

CORREOS = [
    ("Consulta sobre talleres de robótica",
     "Buenos días, quisiera inscribir a mi hija de 10 años en el taller de "
     "robótica. ¿Cuáles son los horarios y el costo?", "maria.quispe@correo.com"),
    ("Quiero ser voluntario",
     "Hola, soy estudiante de ingeniería y me gustaría apoyar como mentor los "
     "sábados. ¿Cómo puedo postular?", "jorge.huaman@correo.com"),
    ("Propuesta de alianza corporativa",
     "Estimados, represento el área de responsabilidad social de una empresa "
     "y nos interesa auspiciar sus programas. Quisiéramos coordinar una reunión.",
     "alianzas@empresa.com.pe"),
    ("RECLAMO - nadie responde",
     "Es la tercera vez que escribo y nadie responde. Inscribí a mi hijo y "
     "hasta ahora no me confirman el cupo. Esto es inaceptable.",
     "roberto.silva@correo.com"),
    ("Factura del taller de julio",
     "Buenas tardes, necesito la factura del pago realizado el 15 de julio. "
     "Mi RUC es 20xxxxxxxxx.", "contabilidad@colegio.edu.pe"),
    ("Posicionamiento web GARANTIZADO",
     "Aumente sus ventas 300%. Ofrecemos SEO garantizado y posicionamiento web "
     "en Google. Haga clic aquí para una oferta única.", "ventas@seopro.biz"),
    ("¿Hay vacantes para agosto?",
     "Hola, consulto si quedan cupos para el taller de programación de agosto. "
     "Gracias.", "lucia.fernandez@correo.com"),
    ("Necesito respuesta urgente hoy mismo",
     "Buenos días, mañana es la inscripción de mi hija y necesito saber "
     "urgente si hay vacante disponible.", "ana.paredes@correo.com"),
    ("Información general",
     "Buenas, vi su publicación en Facebook y quisiera más información sobre "
     "lo que hacen.", "pedro.castillo@correo.com"),
    ("Donación de equipos",
     "Buenas tardes, mi empresa quiere donar diez computadoras para sus "
     "talleres. ¿A quién puedo contactar?", "gerencia@tecnocorp.pe"),
    ("Molesto por el cambio de horario",
     "Cambiaron el horario del taller sin avisar y mi hijo perdió la clase. "
     "Muy mal servicio, quiero una solución.", "carmen.flores@correo.com"),
    ("Solicitud de cotización",
     "Estimados, somos proveedores de material didáctico. Adjunto nuestra "
     "cotización para su evaluación.", "ventas@didacticos.pe"),
    ("Mi hijo quiere aprender a programar",
     "Hola, mi hijo de 12 años está muy interesado en aprender programación. "
     "¿Tienen algún curso para su edad?", "miguel.salas@correo.com"),
    ("Apoyo como mentora",
     "Buenas, soy profesora de matemática y quiero colaborar enseñando en sus "
     "programas de fin de semana.", "sofia.herrera@correo.com"),
    ("Préstamos rápidos sin aval",
     "Obtenga un préstamo de hasta S/50,000 sin aval. Gane dinero fácil "
     "invirtiendo en criptomonedas.", "info@prestamosya.net"),
]

VARIANTES = [
    ("Consulta de inscripción", "Quisiera matricular a mi hija en el taller de "
     "ciencias. ¿Cuándo empiezan las clases?"),
    ("Sobre el taller de Scratch", "¿El curso de Scratch tiene algún costo? "
     "¿Y qué días son las clases?"),
    ("Voluntariado corporativo", "Nuestra empresa quiere que sus colaboradores "
     "apoyen como voluntarios en sus talleres."),
    ("Consulta", "Buenas tardes, ¿dónde están ubicados exactamente?"),
    ("Comprobante de pago", "Adjunto la transferencia realizada. ¿Me confirman "
     "la inscripción?"),
]


def main():
    base = datetime(2026, 7, 27, 8, 30)
    correos = []
    for i, (asunto, cuerpo, remitente) in enumerate(CORREOS):
        correos.append({
            "id": f"M{i+1:03d}", "remitente": remitente, "asunto": asunto,
            "cuerpo": cuerpo,
            "fecha": (base + timedelta(hours=i * 3.5)).isoformat(timespec="minutes"),
            "nombre": remitente.split("@")[0].split(".")[0].title(),
        })
    for j, (asunto, cuerpo) in enumerate(VARIANTES * 3):
        i = len(CORREOS) + j
        remitente = f"persona{j+1}@correo.com"
        correos.append({
            "id": f"M{i+1:03d}", "remitente": remitente, "asunto": asunto,
            "cuerpo": cuerpo,
            "fecha": (base + timedelta(hours=i * 3.5)).isoformat(timespec="minutes"),
            "nombre": f"Persona{j+1}",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(correos, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"✓ {OUT.relative_to(ROOT)} — {len(correos)} correos ficticios")
    print("  incluye: quejas urgentes, spam, alianzas y consultas ambiguas")


if __name__ == "__main__":
    main()
