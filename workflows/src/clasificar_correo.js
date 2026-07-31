// Nodo Code de n8n — "Clasificar correo (respaldo por reglas)"
// Espejo de src/clasificador.py. Corre DESPUÉS de Claude: si la IA no devolvió
// una clasificación válida, este nodo la deriva por reglas para que ningún
// correo se quede sin procesar.

const SENALES = {
  queja: ['queja', 'reclamo', 'molest', 'pesim', 'mal servicio', 'denunc', 'inaceptable', 'devolucion', 'reembolso'],
  alianza: ['alianza', 'auspicio', 'sponsor', 'convenio', 'rse', 'responsabilidad social', 'donacion', 'donar', 'empresa'],
  voluntariado: ['voluntari', 'ser mentor', 'quiero ayudar', 'colaborar', 'apoyar como'],
  inscripcion: ['inscri', 'matricul', 'vacante', 'cupo', 'taller', 'horario', 'clase', 'curso', 'costo', 'precio', 'mi hijo', 'mi hija'],
  administrativo: ['factura', 'boleta', 'ruc', 'comprobante', 'pago', 'transferencia', 'cotizacion', 'proveedor'],
  spam: ['posicionamiento web', 'seo garantizado', 'prestamo', 'casino', 'criptomoneda', 'gane dinero', 'haga clic aqui', 'oferta unica'],
};

const URGENTES = ['urgente', 'hoy mismo', 'manana', 'cuanto antes', 'de inmediato',
  'ya paso', 'sigo esperando', 'es la tercera vez', 'nadie responde'];

const sinTildes = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

function clasificarPorReglas(correo) {
  const texto = sinTildes(String(correo.asunto || '') + ' ' + String(correo.cuerpo || ''));

  let categoria = 'otro';
  for (const cat of Object.keys(SENALES)) {
    if (SENALES[cat].some((k) => texto.includes(k))) { categoria = cat; break; }
  }

  const urgente = URGENTES.some((u) => texto.includes(u));

  let prioridad;
  if (categoria === 'spam') prioridad = 'baja';
  else if (categoria === 'queja' || urgente) prioridad = 'alta';
  else if (categoria === 'inscripcion' || categoria === 'alianza') prioridad = 'media';
  else prioridad = 'baja';

  // Regla no negociable: quejas, alianzas y urgencias las contesta una persona.
  const requiereHumano = categoria === 'queja' || categoria === 'alianza' || urgente;

  return { categoria, prioridad, urgente, requiere_humano: requiereHumano };
}

const salida = [];

for (const item of $input.all()) {
  const j = item.json;
  const correo = j.correo || j;

  // ¿Claude devolvió algo utilizable?
  let clasif = null;
  try {
    const bruto = j.content
      ? j.content.filter((b) => b.type === 'text').map((b) => b.text).join('')
      : '';
    const bloque = bruto.match(/\{[\s\S]*\}/);
    if (bloque) clasif = JSON.parse(bloque[0]);
  } catch (e) {
    clasif = null;
  }

  const valido = clasif && typeof clasif.categoria === 'string';
  const base = valido ? clasif : clasificarPorReglas(correo);

  salida.push({
    json: {
      id: correo.id,
      remitente: correo.remitente,
      asunto: correo.asunto,
      categoria: base.categoria,
      prioridad: base.prioridad || 'media',
      urgente: Boolean(base.urgente),
      // La regla dura se aplica SIEMPRE, aunque la IA diga lo contrario:
      requiere_humano: Boolean(base.requiere_humano)
        || base.categoria === 'queja' || base.categoria === 'alianza',
      borrador: valido ? (clasif.borrador || '') : '',
      motor: valido ? 'claude' : 'reglas (respaldo)',
      revisado_por: '',
      estado: 'pendiente',
    },
  });
}

return salida;
