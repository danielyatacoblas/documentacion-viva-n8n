# docs

Material de apoyo del repositorio.

- `ficha_leads.png` — captura de una ficha generada, la del flujo de leads.

Se regenera con `python scripts/capturar_ficha.py`, que renderiza el Markdown
de la ficha y lo captura con Chrome en modo headless. Se hace así, y no con una
captura de pantalla a mano, para que salga siempre con el mismo ancho, sin la
barra de tareas ni los marcadores del navegador, y para poder rehacerla cuando
la ficha cambie.
