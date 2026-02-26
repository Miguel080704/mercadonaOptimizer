"""
Mercadona Optimizer v6 — Compra Semanal por Comidas
- 4 secciones: Desayuno, Comida, Merienda, Cena
- 3 versiones distintas, maximiza variedad
- Permite multi-pack (máx 2 unidades por producto)
- Versiones B/C intentan no repetir de A/B pero pueden si es necesario
"""
import pulp
from sqlalchemy import create_engine, text
import pandas as pd
import random

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/mercadona_db"

# COMIDA_MAPPING is now in the BBDD (columna 'momentos' en productos_v2)
# See Database/clasificar_momentos.py for classification rules

SECCIONES = ['desayuno', 'comida', 'merienda', 'cena']

# =====================================================================
# MÍNIMOS POR SECCIÓN para cubrir 7 días
# =====================================================================
# Escalado dinámico según presupuesto (se calcula en resolver_version)

# Límites de tipo GLOBAL (cuántos de cada tipo en toda la cesta)
LIMITES_TIPO_BASE = {
    'carne':    (2, 5),
    'pescado':  (1, 3),
    'verdura':  (3, 6),
    'fruta':    (2, 4),
    'lacteo':   (2, 5),
    'legumbre': (1, 3),
    'cereal':   (3, 6),
    'huevo':    (1, 2),
    'capricho': (1, 3),
    'conserva': (0, 3),
}

# Productos "básicos" que tiene sentido comprar x2
TIPOS_MULTIPACK = {'carne', 'pescado', 'cereal', 'fruta', 'verdura', 'huevo', 'legumbre', 'lacteo'}


def cargar_productos():
    engine = create_engine(DATABASE_URL)
    query = """
        SELECT DISTINCT ON (p.nombre)
            p.id, p.nombre, p.precio, p.peso_gramos, p.imagen_url,
            c.tipo, c.emoji, p.momentos,
            n.proteinas_100g, n.carbohidratos_100g, n.grasas_100g, n.calorias_100g
        FROM productos_v2 p
        JOIN categorias c ON p.categoria_id = c.id
        JOIN nutricion n ON n.producto_id = p.id
        WHERE p.precio > 0
          AND c.tipo NOT IN ('condimento', 'aceite', 'bebida', 'otros')
        ORDER BY p.nombre, p.precio ASC
    """
    df = pd.read_sql(query, engine)
    productos = df.to_dict('records')

    for i, p in enumerate(productos):
        p['safe_id'] = i
        peso = max(float(p.get('peso_gramos', 100) or 100), 1)
        factor = peso / 100.0
        p['prot_pack'] = (p.get('proteinas_100g') or 0) * factor
        p['kcal_pack'] = (p.get('calorias_100g') or 0) * factor
        p['gras_pack'] = (p.get('grasas_100g') or 0) * factor
        p['carb_pack'] = (p.get('carbohidratos_100g') or 0) * factor
        p['precio'] = float(p['precio'])
        p['comidas'] = p.get('momentos') or ['comida', 'cena']

    print(f"[LOAD] {len(productos)} productos")
    return productos


def resolver_version(productos, presupuesto, prot_sem, kcal_sem,
                     carb_sem=None, gras_sem=None,
                     penalizar_ids=None, version_name="A"):
    """
    Genera una versión de cesta semanal.
    penalizar_ids: IDs de productos usados en versiones anteriores.
        Se penalizan en la función objetivo pero NO se excluyen.
    """
    prods = productos  # ya no excluimos nada

    if len(prods) < 15:
        return {"version": version_name, "error": "No hay suficientes productos"}

    penalizar = penalizar_ids or set()

    # --- ESCALADO DINÁMICO según presupuesto ---
    factor = max(0.4, min(presupuesto / 50.0, 1.5))  # 30€→0.6, 50€→1.0, 80€→1.5
    min_total = max(10, int(20 * factor))
    max_total = max(15, int(35 * factor))
    minimos_seccion = {
        'desayuno': max(2, int(4 * factor)),
        'comida':   max(3, int(7 * factor)),
        'merienda': max(1, int(3 * factor)),
        'cena':     max(2, int(5 * factor)),
    }

    prob = pulp.LpProblem(f"Cesta_{version_name}", pulp.LpMaximize)

    # --- VARIABLES ---
    # se_compra[i] = cuántos packs se compran (0, 1 o 2)
    se_compra = {}
    for p in prods:
        sid = p['safe_id']
        max_packs = 2 if p['tipo'] in TIPOS_MULTIPACK else 1
        se_compra[sid] = pulp.LpVariable(f"b_{sid}", lowBound=0, upBound=max_packs, cat='Integer')

    # activo[i] = 1 si se compra al menos 1 (binary flag para asignar a sección)
    activo = {}
    for p in prods:
        sid = p['safe_id']
        activo[sid] = pulp.LpVariable(f"act_{sid}", cat='Binary')

    # Enlace: activo[i] <= se_compra[i] <= 2 * activo[i]
    for p in prods:
        sid = p['safe_id']
        prob += activo[sid] <= se_compra[sid], f"ActLo_{sid}"
        prob += se_compra[sid] <= 2 * activo[sid], f"ActHi_{sid}"

    # assign[i][s] = 1 si producto i se asigna a sección s
    assign = {}
    for p in prods:
        sid = p['safe_id']
        assign[sid] = {}
        for s in SECCIONES:
            if s in p['comidas']:
                assign[sid][s] = pulp.LpVariable(f"a_{sid}_{s}", cat='Binary')

    # Enlace: activo = sum(assign) — cada producto activo va a exactamente 1 sección
    for p in prods:
        sid = p['safe_id']
        secciones_posibles = [assign[sid][s] for s in SECCIONES if s in assign[sid]]
        if secciones_posibles:
            prob += activo[sid] == pulp.lpSum(secciones_posibles), f"Link_{sid}"
        else:
            prob += activo[sid] == 0, f"NoSec_{sid}"

    # --- SUMAS (ahora usan se_compra que puede ser 1 o 2) ---
    coste = pulp.lpSum([p['precio'] * se_compra[p['safe_id']] for p in prods])
    prot = pulp.lpSum([p['prot_pack'] * se_compra[p['safe_id']] for p in prods])
    kcal = pulp.lpSum([p['kcal_pack'] * se_compra[p['safe_id']] for p in prods])
    gras = pulp.lpSum([p['gras_pack'] * se_compra[p['safe_id']] for p in prods])
    carb = pulp.lpSum([p['carb_pack'] * se_compra[p['safe_id']] for p in prods])
    total_prods = pulp.lpSum([activo[p['safe_id']] for p in prods])

    # --- OBJETIVO: maximizar variedad, penalizar repetición de versiones anteriores ---
    penalizacion = pulp.lpSum([
        0.3 * activo[p['safe_id']]
        for p in prods if p['safe_id'] in penalizar
    ])
    prob += total_prods - penalizacion

    # --- RESTRICCIONES DE NUTRICIÓN (escaladas) ---
    prob += prot >= prot_sem * 0.7, "Min_Prot"  # al menos 70% del objetivo
    prob += kcal <= kcal_sem, "Max_Kcal"
    prob += kcal >= kcal_sem * 0.80, "Min_Kcal"

    # --- PRESUPUESTO: gastar entre 60%-100% ---
    prob += coste <= presupuesto, "Max_Budget"
    prob += coste >= presupuesto * 0.60, "Min_Budget"

    # --- Carbos/grasas opcionales ---
    if carb_sem is not None:
        prob += carb >= carb_sem * 0.85, "Min_Carb"
        prob += carb <= carb_sem * 1.15, "Max_Carb"
    if gras_sem is not None:
        prob += gras >= gras_sem * 0.85, "Min_Gras"
        prob += gras <= gras_sem * 1.15, "Max_Gras"

    # --- MÍNIMOS POR SECCIÓN (dinámico) ---
    for s, minimo in minimos_seccion.items():
        items_en_seccion = []
        for p in prods:
            sid = p['safe_id']
            if s in assign[sid]:
                items_en_seccion.append(assign[sid][s])
        if items_en_seccion:
            prob += pulp.lpSum(items_en_seccion) >= minimo, f"MinSec_{s}"

    # --- LÍMITES POR TIPO (escalados con presupuesto) ---
    for tipo, (min_base, max_base) in LIMITES_TIPO_BASE.items():
        min_t = max(0, int(min_base * factor))
        max_t = max(min_t + 1, int(max_base * factor))
        items = [activo[p['safe_id']] for p in prods if p['tipo'] == tipo]
        if items:
            if min_t > 0:
                prob += pulp.lpSum(items) >= min_t, f"MinT_{tipo}"
            prob += pulp.lpSum(items) <= max_t, f"MaxT_{tipo}"

    # --- TOTAL PRODUCTOS DISTINTOS (dinámico) ---
    prob += total_prods >= min_total, "Min_Total"
    prob += total_prods <= max_total, "Max_Total"

    # --- ANTI-MONOPOLIO: ningún producto > 25% de kcal ---
    for p in prods:
        if p['kcal_pack'] > kcal_sem * 0.25:
            prob += se_compra[p['safe_id']] == 0, f"AntiMono_{p['safe_id']}"

    # --- PRECIO MÁXIMO POR PRODUCTO: evitar almejas de 10€ ---
    max_precio_unit = presupuesto * 0.15
    for p in prods:
        if p['precio'] > max_precio_unit:
            prob += se_compra[p['safe_id']] == 0, f"MaxPrice_{p['safe_id']}"

    # === RESOLVER ===
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if pulp.LpStatus[prob.status] != 'Optimal':
        return {"version": version_name, "error": f"No viable ({pulp.LpStatus[prob.status]})"}

    # === CONSTRUIR RESULTADO ===
    secciones = {s: [] for s in SECCIONES}
    t_precio, t_prot, t_kcal, t_gras, t_carb = 0, 0, 0, 0, 0
    ids_usados = set()

    for p in prods:
        sid = p['safe_id']
        qty = int(round(se_compra[sid].varValue or 0))
        if qty > 0:
            ids_usados.add(sid)
            # Determinar la sección asignada
            seccion_asignada = 'comida'
            for s in SECCIONES:
                if s in assign[sid]:
                    if assign[sid][s].varValue and assign[sid][s].varValue > 0.5:
                        seccion_asignada = s
                        break

            nombre = p['nombre']
            if qty > 1:
                nombre = f"{p['nombre']} (x{qty})"

            item = {
                "nombre": nombre,
                "precio": round(p['precio'] * qty, 2),
                "tipo": p['tipo'],
                "emoji": p.get('emoji', ''),
                "imagen_url": p.get('imagen_url', ''),
            }
            secciones[seccion_asignada].append(item)
            t_precio += p['precio'] * qty
            t_prot += p['prot_pack'] * qty
            t_kcal += p['kcal_pack'] * qty
            t_gras += p['gras_pack'] * qty
            t_carb += p['carb_pack'] * qty

    for s in secciones.values():
        s.sort(key=lambda x: x['nombre'])

    total_n = sum(len(s) for s in secciones.values())

    return {
        "version": version_name,
        "precio_total": round(t_precio, 2),
        "total_productos": total_n,
        "macros": {
            "prot": round(t_prot / 7, 1),
            "kcal": round(t_kcal / 7, 0),
            "gras": round(t_gras / 7, 1),
            "carb": round(t_carb / 7, 1)
        },
        "secciones": secciones,
        "_ids_usados": list(ids_usados),  # para penalizar en versiones siguientes
    }


def generar_propuestas_api(presupuesto_max, proteina_diaria, kcal_diaria,
                           carbohidratos_diarios=None, grasas_diarias=None,
                           excluir_tipos=None):
    productos = cargar_productos()
    if not productos:
        return {"error": "No se pudieron cargar productos"}

    # Filtrar tipos excluidos (perfil vegano/vegetariano)
    if excluir_tipos:
        productos = [p for p in productos if p['tipo'] not in excluir_tipos]
        for i, p in enumerate(productos):
            p['safe_id'] = i
        print(f"  [FILTER] Excluidos tipos {excluir_tipos} -> {len(productos)} prods")

    prot_sem = proteina_diaria * 7
    kcal_sem = kcal_diaria * 7
    carb_sem = carbohidratos_diarios * 7 if carbohidratos_diarios else None
    gras_sem = grasas_diarias * 7 if grasas_diarias else None

    # Versión A: sin penalización
    va = resolver_version(productos, presupuesto_max, prot_sem, kcal_sem,
                          carb_sem, gras_sem, penalizar_ids=set(), version_name="A")

    # Versión B: penaliza (pero no excluye) productos de A
    ids_a = set(va.get('_ids_usados', []))
    vb = resolver_version(productos, presupuesto_max, prot_sem, kcal_sem,
                          carb_sem, gras_sem, penalizar_ids=ids_a, version_name="B")

    # Versión C: penaliza productos de A + B
    ids_ab = ids_a | set(vb.get('_ids_usados', []))
    vc = resolver_version(productos, presupuesto_max, prot_sem, kcal_sem,
                          carb_sem, gras_sem, penalizar_ids=ids_ab, version_name="C")

    # Limpiar campo interno antes de devolver
    for v in [va, vb, vc]:
        v.pop('_ids_usados', None)

    return {"version_a": va, "version_b": vb, "version_c": vc}


if __name__ == "__main__":
    result = generar_propuestas_api(presupuesto_max=80, proteina_diaria=150, kcal_diaria=2400)
    for key in ['version_a', 'version_b', 'version_c']:
        data = result[key]
        if 'error' in data:
            print(f"\n[{data['version']}] ERROR: {data['error']}")
            continue

        print(f"\n{'='*60}")
        print(f"VERSION {data['version']} | {data['precio_total']}E | "
              f"{data['total_productos']} prods | "
              f"{data['macros']['kcal']} kcal/dia | "
              f"{data['macros']['prot']}g prot")
        print(f"{'='*60}")

        for seccion_name, items in data['secciones'].items():
            icon = {'desayuno': '🌅', 'comida': '🍽️', 'merienda': '🍪', 'cena': '🌙'}
            print(f"\n  {icon.get(seccion_name, '')} {seccion_name.upper()} ({len(items)})")
            for p in items:
                e = p.get('emoji', '')
                print(f"    {e} {p['nombre'][:45]:47s} {p['precio']:5.2f}E  ({p['tipo']})")