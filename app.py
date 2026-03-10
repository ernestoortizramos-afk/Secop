from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests
import html
import ast
from collections import Counter, defaultdict

app = FastAPI(title="Veeduría SECOP")

BASE = "https://www.datos.gov.co/resource"
DATASET_PROCESOS = "p6dx-8zbt"
DATASET_CONTRATOS = "jbjy-vk9h"


def esc(texto):
    if texto is None:
        return ""
    return html.escape(str(texto))


def limpiar(texto):
    return str(texto).replace("\\", "\\\\").replace("'", "''").strip()


def obtener_url(valor):
    if not valor:
        return ""

    if isinstance(valor, dict):
        return valor.get("url", "")

    texto = str(valor).strip()

    if texto.startswith("http://") or texto.startswith("https://"):
        return texto

    if texto.startswith("{") and "url" in texto:
        try:
            data = ast.literal_eval(texto)
            if isinstance(data, dict):
                return data.get("url", "")
        except Exception:
            return ""

    return ""


def to_float(valor):
    try:
        if valor in (None, ""):
            return 0.0
        return float(str(valor).replace(",", "").strip())
    except Exception:
        return 0.0


def consultar(dataset, params):
    url = f"{BASE}/{dataset}.json"
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def opcion_seleccionada(valor_actual, valor_opcion):
    return "selected" if str(valor_actual) == str(valor_opcion) else ""


def pagina(titulo, contenido):
    return f"""
    <html>
    <head>
        <title>{esc(titulo)}</title>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                background: #f4f6f8;
                color: #1f2937;
            }}
            .top {{
                background: #0f172a;
                color: white;
                padding: 20px 30px;
            }}
            .top h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .menu {{
                background: white;
                padding: 15px 30px;
                border-bottom: 1px solid #ddd;
            }}
            .menu a {{
                margin-right: 20px;
                text-decoration: none;
                color: #0f172a;
                font-weight: bold;
            }}
            .wrap {{
                padding: 25px 30px;
            }}
            .card {{
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}
            h2 {{
                margin-top: 0;
            }}
            form {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 15px;
            }}
            label {{
                display: block;
                font-size: 14px;
                margin-bottom: 6px;
                font-weight: bold;
            }}
            input, select {{
                width: 100%;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 8px;
                box-sizing: border-box;
                background: white;
            }}
            button {{
                background: #0f172a;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: bold;
            }}
            button:hover {{
                background: #1e293b;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                background: white;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
                vertical-align: top;
                font-size: 14px;
            }}
            th {{
                background: #e5e7eb;
            }}
            .alerta {{
                background: #fff7ed;
                border-left: 5px solid #ea580c;
                padding: 12px;
                margin-bottom: 10px;
                border-radius: 8px;
            }}
            .ok {{
                background: #ecfdf5;
                border-left: 5px solid #16a34a;
                padding: 12px;
                border-radius: 8px;
            }}
            .grid4 {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 15px;
            }}
            .mini {{
                background: white;
                border-radius: 12px;
                padding: 18px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}
            .mini h3 {{
                margin-top: 0;
            }}
            .small {{
                color: #475569;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="top">
            <h1>Panel de Veeduría SECOP</h1>
        </div>
        <div class="menu">
            <a href="/">Inicio</a>
            <a href="/contratos">Buscar contratos</a>
            <a href="/procesos">Buscar procesos</a>
            <a href="/persona">Buscar persona</a>
            <a href="/alertas">Alertas</a>
        </div>
        <div class="wrap">
            {contenido}
        </div>
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def inicio():
    contenido = """
    <div class="card">
        <h2>Bienvenido</h2>
        <p>Este bot te permite hacer una veeduría básica sobre contratación pública en SECOP II usando datos públicos.</p>
        <p>Ahora cada módulo tiene filtros y opciones de ordenamiento por orden alfabético, valor y fecha según corresponda.</p>
    </div>

    <div class="grid4">
        <div class="mini">
            <h3>Buscar contratos</h3>
            <p class="small">Consulta por entidad, proveedor, documento, representante legal, estado, fecha y valor.</p>
            <a href="/contratos"><button>Entrar</button></a>
        </div>
        <div class="mini">
            <h3>Buscar procesos</h3>
            <p class="small">Consulta procesos por entidad, referencia, modalidad, estado y fecha de adjudicación.</p>
            <a href="/procesos"><button>Entrar</button></a>
        </div>
        <div class="mini">
            <h3>Buscar persona</h3>
            <p class="small">Revisa si una persona aparece como proveedor o representante legal en contratos.</p>
            <a href="/persona"><button>Entrar</button></a>
        </div>
        <div class="mini">
            <h3>Alertas</h3>
            <p class="small">Obtén señales básicas de concentración, valores altos y enlaces faltantes.</p>
            <a href="/alertas"><button>Entrar</button></a>
        </div>
    </div>
    """
    return pagina("Inicio", contenido)


@app.get("/contratos", response_class=HTMLResponse)
def contratos(
    entidad: str = "",
    proveedor: str = "",
    documento: str = "",
    representante: str = "",
    estado: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    valor_min: str = "",
    valor_max: str = "",
    ordenar_por: str = "fecha",
    direccion: str = "desc",
    limite: int = 20
):
    mapa_orden = {
        "entidad": "nombre_entidad",
        "proveedor": "proveedor_adjudicado",
        "documento": "documento_proveedor",
        "representante": "nombre_representante_legal",
        "estado": "estado_contrato",
        "valor": "valor_del_contrato",
        "fecha": "fecha_de_firma",
    }

    campo_orden = mapa_orden.get(ordenar_por, "fecha_de_firma")
    sentido = "ASC" if str(direccion).lower() == "asc" else "DESC"

    form = f"""
    <div class="card">
        <h2>Buscar contratos</h2>
        <form method="get">
            <div><label>Entidad</label><input name="entidad" value="{esc(entidad)}"></div>
            <div><label>Proveedor</label><input name="proveedor" value="{esc(proveedor)}"></div>
            <div><label>Documento del proveedor</label><input name="documento" value="{esc(documento)}"></div>
            <div><label>Representante legal</label><input name="representante" value="{esc(representante)}"></div>
            <div><label>Estado del contrato</label><input name="estado" value="{esc(estado)}"></div>
            <div><label>Fecha desde</label><input type="date" name="fecha_desde" value="{esc(fecha_desde)}"></div>
            <div><label>Fecha hasta</label><input type="date" name="fecha_hasta" value="{esc(fecha_hasta)}"></div>
            <div><label>Valor mínimo</label><input name="valor_min" value="{esc(valor_min)}"></div>
            <div><label>Valor máximo</label><input name="valor_max" value="{esc(valor_max)}"></div>

            <div>
                <label>Ordenar por</label>
                <select name="ordenar_por">
                    <option value="fecha" {opcion_seleccionada(ordenar_por, "fecha")}>Fecha de firma</option>
                    <option value="valor" {opcion_seleccionada(ordenar_por, "valor")}>Valor</option>
                    <option value="entidad" {opcion_seleccionada(ordenar_por, "entidad")}>Entidad</option>
                    <option value="proveedor" {opcion_seleccionada(ordenar_por, "proveedor")}>Proveedor</option>
                    <option value="documento" {opcion_seleccionada(ordenar_por, "documento")}>Documento</option>
                    <option value="representante" {opcion_seleccionada(ordenar_por, "representante")}>Representante legal</option>
                    <option value="estado" {opcion_seleccionada(ordenar_por, "estado")}>Estado</option>
                </select>
            </div>

            <div>
                <label>Dirección</label>
                <select name="direccion">
                    <option value="asc" {opcion_seleccionada(direccion, "asc")}>Menor a mayor / A-Z</option>
                    <option value="desc" {opcion_seleccionada(direccion, "desc")}>Mayor a menor / Z-A</option>
                </select>
            </div>

            <div><label>Límite</label><input name="limite" value="{esc(limite)}"></div>
            <div style="align-self:end;"><button type="submit">Buscar</button></div>
        </form>
    </div>
    """

    if not any([entidad, proveedor, documento, representante, estado, fecha_desde, fecha_hasta, valor_min, valor_max]):
        return pagina("Buscar contratos", form)

    clausulas = []

    if entidad.strip():
        clausulas.append(f"upper(nombre_entidad) like upper('%{limpiar(entidad)}%')")
    if proveedor.strip():
        clausulas.append(f"upper(proveedor_adjudicado) like upper('%{limpiar(proveedor)}%')")
    if documento.strip():
        clausulas.append(f"upper(documento_proveedor) like upper('%{limpiar(documento)}%')")
    if representante.strip():
        clausulas.append(f"upper(nombre_representante_legal) like upper('%{limpiar(representante)}%')")
    if estado.strip():
        clausulas.append(f"upper(estado_contrato) like upper('%{limpiar(estado)}%')")
    if fecha_desde.strip():
        clausulas.append(f"fecha_de_firma >= '{fecha_desde}T00:00:00'")
    if fecha_hasta.strip():
        clausulas.append(f"fecha_de_firma <= '{fecha_hasta}T23:59:59'")
    if valor_min.strip():
        clausulas.append(f"valor_del_contrato >= {valor_min}")
    if valor_max.strip():
        clausulas.append(f"valor_del_contrato <= {valor_max}")

    params = {
        "$limit": min(limite, 100),
        "$order": f"{campo_orden} {sentido}"
    }
    if clausulas:
        params["$where"] = " AND ".join(clausulas)

    try:
        datos = consultar(DATASET_CONTRATOS, params)
    except Exception as e:
        return pagina("Buscar contratos", form + f'<div class="alerta">Ocurrió un error al consultar: {esc(e)}</div>')

    if not datos:
        return pagina("Buscar contratos", form + '<div class="alerta">No encontré contratos con esos filtros.</div>')

    filas = ""
    for item in datos:
        url = obtener_url(item.get("urlproceso"))
        ver = f'<a href="{esc(url)}" target="_blank">Abrir proceso</a>' if url else "Sin enlace"
        filas += f"""
        <tr>
            <td>{esc(item.get("nombre_entidad"))}</td>
            <td>{esc(item.get("proveedor_adjudicado"))}</td>
            <td>{esc(item.get("documento_proveedor"))}</td>
            <td>{esc(item.get("nombre_representante_legal"))}</td>
            <td>{esc(item.get("estado_contrato"))}</td>
            <td>{esc(item.get("valor_del_contrato"))}</td>
            <td>{esc(item.get("fecha_de_firma"))}</td>
            <td>{ver}</td>
        </tr>
        """

    tabla = f"""
    <div class="card">
        <h2>Resultados</h2>
        <p>Se encontraron {len(datos)} contratos.</p>
        <p><b>Orden aplicado:</b> {esc(ordenar_por)} - {esc(sentido)}</p>
        <table>
            <tr>
                <th>Entidad</th>
                <th>Proveedor</th>
                <th>Documento</th>
                <th>Representante legal</th>
                <th>Estado</th>
                <th>Valor</th>
                <th>Fecha de firma</th>
                <th>Proceso</th>
            </tr>
            {filas}
        </table>
    </div>
    """

    return pagina("Buscar contratos", form + tabla)


@app.get("/procesos", response_class=HTMLResponse)
def procesos(
    entidad: str = "",
    referencia: str = "",
    modalidad: str = "",
    estado: str = "",
    adjudicado: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    ordenar_por: str = "fecha",
    direccion: str = "desc",
    limite: int = 20
):
    mapa_orden = {
        "entidad": "entidad",
        "referencia": "referencia_del_proceso",
        "modalidad": "modalidad_de_contratacion",
        "estado": "estado_del_procedimiento",
        "adjudicado": "adjudicado",
        "fecha": "fecha_adjudicacion",
    }

    campo_orden = mapa_orden.get(ordenar_por, "fecha_adjudicacion")
    sentido = "ASC" if str(direccion).lower() == "asc" else "DESC"

    form = f"""
    <div class="card">
        <h2>Buscar procesos</h2>
        <form method="get">
            <div><label>Entidad</label><input name="entidad" value="{esc(entidad)}"></div>
            <div><label>Referencia del proceso</label><input name="referencia" value="{esc(referencia)}"></div>
            <div><label>Modalidad</label><input name="modalidad" value="{esc(modalidad)}"></div>
            <div><label>Estado</label><input name="estado" value="{esc(estado)}"></div>
            <div><label>Adjudicado</label><input name="adjudicado" value="{esc(adjudicado)}"></div>
            <div><label>Fecha adjudicación desde</label><input type="date" name="fecha_desde" value="{esc(fecha_desde)}"></div>
            <div><label>Fecha adjudicación hasta</label><input type="date" name="fecha_hasta" value="{esc(fecha_hasta)}"></div>

            <div>
                <label>Ordenar por</label>
                <select name="ordenar_por">
                    <option value="fecha" {opcion_seleccionada(ordenar_por, "fecha")}>Fecha adjudicación</option>
                    <option value="entidad" {opcion_seleccionada(ordenar_por, "entidad")}>Entidad</option>
                    <option value="referencia" {opcion_seleccionada(ordenar_por, "referencia")}>Referencia</option>
                    <option value="modalidad" {opcion_seleccionada(ordenar_por, "modalidad")}>Modalidad</option>
                    <option value="estado" {opcion_seleccionada(ordenar_por, "estado")}>Estado</option>
                    <option value="adjudicado" {opcion_seleccionada(ordenar_por, "adjudicado")}>Adjudicado</option>
                </select>
            </div>

            <div>
                <label>Dirección</label>
                <select name="direccion">
                    <option value="asc" {opcion_seleccionada(direccion, "asc")}>Menor a mayor / A-Z</option>
                    <option value="desc" {opcion_seleccionada(direccion, "desc")}>Mayor a menor / Z-A</option>
                </select>
            </div>

            <div><label>Límite</label><input name="limite" value="{esc(limite)}"></div>
            <div style="align-self:end;"><button type="submit">Consultar</button></div>
        </form>
    </div>
    """

    if not any([entidad, referencia, modalidad, estado, adjudicado, fecha_desde, fecha_hasta]):
        return pagina("Buscar procesos", form)

    clausulas = []

    if entidad.strip():
        clausulas.append(f"upper(entidad) like upper('%{limpiar(entidad)}%')")
    if referencia.strip():
        clausulas.append(f"upper(referencia_del_proceso) like upper('%{limpiar(referencia)}%')")
    if modalidad.strip():
        clausulas.append(f"upper(modalidad_de_contratacion) like upper('%{limpiar(modalidad)}%')")
    if estado.strip():
        clausulas.append(f"upper(estado_del_procedimiento) like upper('%{limpiar(estado)}%')")
    if adjudicado.strip():
        clausulas.append(f"upper(adjudicado) like upper('%{limpiar(adjudicado)}%')")
    if fecha_desde.strip():
        clausulas.append(f"fecha_adjudicacion >= '{fecha_desde}T00:00:00'")
    if fecha_hasta.strip():
        clausulas.append(f"fecha_adjudicacion <= '{fecha_hasta}T23:59:59'")

    params = {
        "$limit": min(limite, 100),
        "$order": f"{campo_orden} {sentido}"
    }
    if clausulas:
        params["$where"] = " AND ".join(clausulas)

    try:
        datos = consultar(DATASET_PROCESOS, params)
    except Exception as e:
        return pagina("Buscar procesos", form + f'<div class="alerta">Ocurrió un error al consultar: {esc(e)}</div>')

    if not datos:
        return pagina("Buscar procesos", form + '<div class="alerta">No encontré procesos con esos filtros.</div>')

    filas = ""
    for item in datos:
        url = obtener_url(item.get("urlproceso"))
        ver = f'<a href="{esc(url)}" target="_blank">Abrir expediente</a>' if url else "Sin enlace"
        filas += f"""
        <tr>
            <td>{esc(item.get("entidad"))}</td>
            <td>{esc(item.get("referencia_del_proceso"))}</td>
            <td>{esc(item.get("modalidad_de_contratacion"))}</td>
            <td>{esc(item.get("estado_del_procedimiento"))}</td>
            <td>{esc(item.get("adjudicado"))}</td>
            <td>{esc(item.get("fecha_adjudicacion"))}</td>
            <td>{ver}</td>
        </tr>
        """

    tabla = f"""
    <div class="card">
        <h2>Resultados</h2>
        <p>Se encontraron {len(datos)} procesos.</p>
        <p><b>Orden aplicado:</b> {esc(ordenar_por)} - {esc(sentido)}</p>
        <table>
            <tr>
                <th>Entidad</th>
                <th>Referencia</th>
                <th>Modalidad</th>
                <th>Estado</th>
                <th>Adjudicado</th>
                <th>Fecha adjudicación</th>
                <th>Expediente</th>
            </tr>
            {filas}
        </table>
    </div>
    """

    return pagina("Buscar procesos", form + tabla)


@app.get("/persona", response_class=HTMLResponse)
def persona(
    nombre: str = "",
    documento: str = "",
    ordenar_por: str = "fecha",
    direccion: str = "desc",
    limite: int = 20
):
    mapa_orden = {
        "entidad": "nombre_entidad",
        "proveedor": "proveedor_adjudicado",
        "documento": "documento_proveedor",
        "representante": "nombre_representante_legal",
        "valor": "valor_del_contrato",
        "fecha": "fecha_de_firma",
    }

    campo_orden = mapa_orden.get(ordenar_por, "fecha_de_firma")
    sentido = "ASC" if str(direccion).lower() == "asc" else "DESC"

    form = f"""
    <div class="card">
        <h2>Buscar persona</h2>
        <p>Esta pantalla busca coincidencias en proveedor adjudicado, documento del proveedor y representante legal.</p>
        <form method="get">
            <div><label>Nombre</label><input name="nombre" value="{esc(nombre)}"></div>
            <div><label>Documento</label><input name="documento" value="{esc(documento)}"></div>

            <div>
                <label>Ordenar por</label>
                <select name="ordenar_por">
                    <option value="fecha" {opcion_seleccionada(ordenar_por, "fecha")}>Fecha de firma</option>
                    <option value="valor" {opcion_seleccionada(ordenar_por, "valor")}>Valor</option>
                    <option value="entidad" {opcion_seleccionada(ordenar_por, "entidad")}>Entidad</option>
                    <option value="proveedor" {opcion_seleccionada(ordenar_por, "proveedor")}>Proveedor</option>
                    <option value="documento" {opcion_seleccionada(ordenar_por, "documento")}>Documento</option>
                    <option value="representante" {opcion_seleccionada(ordenar_por, "representante")}>Representante legal</option>
                </select>
            </div>

            <div>
                <label>Dirección</label>
                <select name="direccion">
                    <option value="asc" {opcion_seleccionada(direccion, "asc")}>Menor a mayor / A-Z</option>
                    <option value="desc" {opcion_seleccionada(direccion, "desc")}>Mayor a menor / Z-A</option>
                </select>
            </div>

            <div><label>Límite</label><input name="limite" value="{esc(limite)}"></div>
            <div style="align-self:end;"><button type="submit">Buscar coincidencias</button></div>
        </form>
    </div>
    """

    if not any([nombre, documento]):
        return pagina("Buscar persona", form)

    partes = []

    if nombre.strip():
        partes.append(
            "("
            f"upper(proveedor_adjudicado) like upper('%{limpiar(nombre)}%') "
            f"OR upper(nombre_representante_legal) like upper('%{limpiar(nombre)}%')"
            ")"
        )

    if documento.strip():
        partes.append(f"upper(documento_proveedor) like upper('%{limpiar(documento)}%')")

    params = {
        "$limit": min(limite, 100),
        "$order": f"{campo_orden} {sentido}",
        "$where": " AND ".join(partes)
    }

    try:
        datos = consultar(DATASET_CONTRATOS, params)
    except Exception as e:
        return pagina("Buscar persona", form + f'<div class="alerta">Ocurrió un error al consultar: {esc(e)}</div>')

    advertencia = """
    <div class="alerta">
        Esta búsqueda muestra coincidencias en datos públicos. No prueba por sí sola la firma material del PDF del contrato.
        Para confirmar la firma debes abrir el proceso y revisar el documento contractual.
    </div>
    """

    if not datos:
        return pagina("Buscar persona", form + advertencia + '<div class="alerta">No encontré coincidencias para esa persona.</div>')

    filas = ""
    for item in datos:
        url = obtener_url(item.get("urlproceso"))
        ver = f'<a href="{esc(url)}" target="_blank">Abrir proceso</a>' if url else "Sin enlace"
        filas += f"""
        <tr>
            <td>{esc(item.get("nombre_entidad"))}</td>
            <td>{esc(item.get("proveedor_adjudicado"))}</td>
            <td>{esc(item.get("documento_proveedor"))}</td>
            <td>{esc(item.get("nombre_representante_legal"))}</td>
            <td>{esc(item.get("referencia_del_contrato"))}</td>
            <td>{esc(item.get("valor_del_contrato"))}</td>
            <td>{esc(item.get("fecha_de_firma"))}</td>
            <td>{ver}</td>
        </tr>
        """

    tabla = f"""
    <div class="card">
        <h2>Coincidencias encontradas</h2>
        <p>Se encontraron {len(datos)} registros.</p>
        <p><b>Orden aplicado:</b> {esc(ordenar_por)} - {esc(sentido)}</p>
        <table>
            <tr>
                <th>Entidad</th>
                <th>Proveedor</th>
                <th>Documento</th>
                <th>Representante legal</th>
                <th>Referencia contrato</th>
                <th>Valor</th>
                <th>Fecha firma</th>
                <th>Proceso</th>
            </tr>
            {filas}
        </table>
    </div>
    """

    return pagina("Buscar persona", form + advertencia + tabla)


@app.get("/alertas", response_class=HTMLResponse)
def alertas(
    entidad: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
    umbral: float = 500000000,
    limite: int = 200
):
    form = f"""
    <div class="card">
        <h2>Alertas de veeduría</h2>
        <form method="get">
            <div><label>Entidad</label><input name="entidad" value="{esc(entidad)}"></div>
            <div><label>Fecha desde</label><input type="date" name="fecha_desde" value="{esc(fecha_desde)}"></div>
            <div><label>Fecha hasta</label><input type="date" name="fecha_hasta" value="{esc(fecha_hasta)}"></div>
            <div><label>Umbral de valor alto</label><input name="umbral" value="{esc(umbral)}"></div>
            <div><label>Límite</label><input name="limite" value="{esc(limite)}"></div>
            <div style="align-self:end;"><button type="submit">Generar alertas</button></div>
        </form>
    </div>
    """

    if not entidad.strip():
        return pagina("Alertas", form)

    clausulas = [f"upper(nombre_entidad) like upper('%{limpiar(entidad)}%')"]

    if fecha_desde.strip():
        clausulas.append(f"fecha_de_firma >= '{fecha_desde}T00:00:00'")
    if fecha_hasta.strip():
        clausulas.append(f"fecha_de_firma <= '{fecha_hasta}T23:59:59'")

    params = {
        "$limit": min(limite, 500),
        "$where": " AND ".join(clausulas)
    }

    try:
        datos = consultar(DATASET_CONTRATOS, params)
    except Exception as e:
        return pagina("Alertas", form + f'<div class="alerta">Ocurrió un error al consultar: {esc(e)}</div>')

    if not datos:
        return pagina("Alertas", form + '<div class="alerta">No encontré contratos para esa entidad.</div>')

    total = 0.0
    sin_enlace = 0
    conteo_proveedor = Counter()
    valor_proveedor = defaultdict(float)
    contratos_altos = []

    for item in datos:
        proveedor = item.get("proveedor_adjudicado") or "SIN DATO"
        valor = to_float(item.get("valor_del_contrato"))
        url = obtener_url(item.get("urlproceso"))

        total += valor
        conteo_proveedor[proveedor] += 1
        valor_proveedor[proveedor] += valor

        if valor >= umbral:
            contratos_altos.append(item)

        if not url:
            sin_enlace += 1

    alertas_lista = ""

    top = conteo_proveedor.most_common(1)
    if top and top[0][1] / len(datos) >= 0.35:
        alertas_lista += f'<div class="alerta">Posible concentración: el proveedor <b>{esc(top[0][0])}</b> aparece en {top[0][1]} de {len(datos)} contratos revisados.</div>'

    if contratos_altos:
        alertas_lista += f'<div class="alerta">Se encontraron {len(contratos_altos)} contratos con valor igual o superior a {esc(umbral)}.</div>'

    if sin_enlace > 0:
        alertas_lista += f'<div class="alerta">Hay {sin_enlace} registros sin enlace al proceso. Conviene verificarlos manualmente.</div>'

    if not alertas_lista:
        alertas_lista = '<div class="ok">No encontré alertas simples con las reglas actuales.</div>'

    top_filas = ""
    for proveedor, cantidad in conteo_proveedor.most_common(5):
        top_filas += f"""
        <tr>
            <td>{esc(proveedor)}</td>
            <td>{cantidad}</td>
            <td>{esc(valor_proveedor[proveedor])}</td>
        </tr>
        """

    tabla = f"""
    <div class="card">
        <h2>Resumen</h2>
        <p><b>Contratos revisados:</b> {len(datos)}</p>
        <p><b>Valor total revisado:</b> {total}</p>
        {alertas_lista}
    </div>

    <div class="card">
        <h2>Top 5 proveedores por cantidad de contratos</h2>
        <table>
            <tr>
                <th>Proveedor</th>
                <th>Cantidad</th>
                <th>Valor acumulado</th>
            </tr>
            {top_filas}
        </table>
    </div>
    """

    return pagina("Alertas", form + tabla)