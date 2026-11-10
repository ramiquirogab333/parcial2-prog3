"""Registro central de modelos de tabla.

`create_all` solo crea las tablas de los modelos que ya fueron importados.
Cada turno agrega acá el import del `models.py` de su módulo.
"""

from app.modules.autores import models as autores_models  # noqa: F401
from app.modules.clientes import models as clientes_models  # noqa: F401
from app.modules.editoriales import models as editoriales_models  # noqa: F401
from app.modules.generos import models as generos_models  # noqa: F401
