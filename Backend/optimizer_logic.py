"""
Mercadona Optimizer v5 — Compra Semanal por Comidas
- 4 secciones: Desayuno, Comida, Merienda, Cena
- 3 versiones distintas, todas cerca del presupuesto
- Cada producto se asigna a una SOLA sección por el solver
"""
import pulp
from sqlalchemy import create_engine, text
import pandas as pd
import random

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/mercadona_db"

# =====================================================================
# MAPEO: qué tipo de producto puede ir en qué comida
# =====================================================================
COMIDA_MAPPING = {
    'cereal':   ['desayuno', 'comida', 'merienda', 'cena'],
    'lacteo':   ['desayuno', 'merienda'],
    'huevo':    ['desayuno', 'cena'],
    'fruta':    ['desayuno', 'merienda'],
    'carne':    ['comida', 'cena'],
    'pescado':  ['comida', 'cena'],
    'legumbre': ['comida', 'cena'],
    'verdura':  ['comida', 'cena'],
    'conserva': ['comida', 'cena'],
    'capricho': ['merienda'],
}

SECCIONES = ['desayuno', 'comida', 'merienda', 'cena']

# =====================================================================
# MÍNIMOS POR SECCIÓN para cubrir 7 días
# =====================================================================
MINIMOS_SECCION = {
    'desayuno': 4,
    'comida':   7,
    'merienda': 3,
    'cena':     5,
}

# Límites de tipo GLOBAL (cuántos de cada tipo en toda la cesta)
LIMITES_TIPO = {
    'carne':    (2, 5),
    'pescado':  (1, 3),
    'verdura':  (3, 6),
    'fruta':    (2, 4),
    'lacteo':   (2, 4),
    'legumbre': (1, 3),
    'cereal':   (3, 5),
    'huevo':    (1, 2),
    'capricho': (1, 3),
    'conserva': (0, 3),
}


def cargar_productos():
    engine = create_engine(DATABASE_URL)
    query = """
        SELECT DISTINCT ON (p.nombre)
            p.id, p.nombre, p.precio, p.peso_gramos, p.imagen_url,
            c.tipo, c.emoji,
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
        p['comidas'] = COMIDA_MAPPING.get(p.get('tipo', 'otros'), [])

    print(f"[LOAD] {len(productos)} productos")
    return productos


def resolver_version(productos, presupuesto, prot_sem, kcal_sem,
                     carb_sem=None, gras_sem=None,
                     excluir_ids=None, version_name="A"):
    """
    Resuelve UNA versión: elige productos Y los asigna a secciones.
    Objetivo: maximizar VARIEDAD (nº de productos) dentro del presupuesto.
    """
    print(f"  [SOLVER] Versión {version_name}...")
    excluir = excluir_ids or set()
    prods = [p for p in productos if p['safe_id'] not in excluir]

    if len(prods) < 15:
        return {"version": version_name, "error": "No hay suficientes productos"}

    prob = pulp.LpProblem(f"Cesta_{version_name}", pulp.LpMaximize)

    # --- VARIABLES ---
    # assign[i][s] = 1 si producto i se asigna a sección s
    assign = {}
    for p in prods:
        sid = p['safe_id']
        assign[sid] = {}
        for s in SECCIONES:
            if s in p['comidas']:
                assign[sid][s] = pulp.LpVariable(f"a_{sid}_{s}", cat='Binary')

    # se_compra[i] = 1 si se compra producto i (en cualquier sección)
    se_compra = {}
    for p in prods:
        sid = p['safe_id']
        se_compra[sid] = pulp.LpVariable(f"b_{sid}", cat='Binary')

    # --- ENLACE: se_compra = sum(assign[s]) para cada producto ---
    for p in prods:
        sid = p['safe_id']
        secciones_posibles = [assign[sid][s] for s in SECCIONES if s in assign[sid]]
        if secciones_posibles:
            prob += se_compra[sid] == pulp.lpSum(secciones_posibles), f"Link_{sid}"
        else:
            prob += se_compra[sid] == 0, f"NoSec_{sid}"

    # --- SUMAS ---
    coste = pulp.lpSum([p['precio'] * se_compra[p['safe_id']] for p in prods])
    prot = pulp.lpSum([p['prot_pack'] * se_compra[p['safe_id']] for p in prods])
    kcal = pulp.lpSum([p['kcal_pack'] * se_compra[p['safe_id']] for p in prods])
    gras = pulp.lpSum([p['gras_pack'] * se_compra[p['safe_id']] for p in prods])
    carb = pulp.lpSum([p['carb_pack'] * se_compra[p['safe_id']] for p in prods])
    total_prods = pulp.lpSum([se_compra[p['safe_id']] for p in prods])

    # --- OBJETIVO: maximizar variedad (nº productos) ---
    prob += total_prods

    # --- RESTRICCIONES DE NUTRICIÓN ---
    prob += prot >= prot_sem, "Min_Prot"
    prob += kcal <= kcal_sem, "Max_Kcal"
    prob += kcal >= kcal_sem * 0.85, "Min_Kcal"

    # --- PRESUPUESTO: gastar entre 75%-100% ---
    prob += coste <= presupuesto, "Max_Budget"
    prob += coste >= presupuesto * 0.75, "Min_Budget"

    # --- Carbos/grasas opcionales ---
    if carb_sem is not None:
        prob += carb >= carb_sem * 0.85, "Min_Carb"
        prob += carb <= carb_sem * 1.15, "Max_Carb"
    if gras_sem is not None:
        prob += gras >= gras_sem * 0.85, "Min_Gras"
        prob += gras <= gras_sem * 1.15, "Max_Gras"

    # --- MÍNIMOS POR SECCIÓN ---
    for s, minimo in MINIMOS_SECCION.items():
        items_en_seccion = []
        for p in prods:
            sid = p['safe_id']
            if s in assign[sid]:
                items_en_seccion.append(assign[sid][s])
        if items_en_seccion:
            prob += pulp.lpSum(items_en_seccion) >= minimo, f"MinSec_{s}"

    # --- LÍMITES POR TIPO ---
    for tipo, (min_t, max_t) in LIMITES_TIPO.items():
        items = [se_compra[p['safe_id']] for p in prods if p['tipo'] == tipo]
        if items:
            prob += pulp.lpSum(items) >= min_t, f"MinT_{tipo}"
            prob += pulp.lpSum(items) <= max_t, f"MaxT_{tipo}"

    # --- TOTAL PRODUCTOS ---
    prob += total_prods >= 20, "Min_Total"
    prob += total_prods <= 30, "Max_Total"

    # --- ANTI-MONOPOLIO: ningún producto > 25% de kcal ---
    for p in prods:
        if p['kcal_pack'] > kcal_sem * 0.25:
            prob += se_compra[p['safe_id']] == 0, f"AntiMono_{p['safe_id']}"

    # --- PRECIO MÁXIMO POR PRODUCTO: evitar almejas de 10€ ---
    max_precio_unit = presupuesto * 0.15  # ningún producto > 15% del presupuesto
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
        if se_compra[sid].varValue and se_compra[sid].varValue > 0.5:
            ids_usados.add(sid)
            # Determinar la sección asignada
            seccion_asignada = 'comida'
            for s in SECCIONES:
                if s in assign[sid]:
                    if assign[sid][s].varValue and assign[sid][s].varValue > 0.5:
                        seccion_asignada = s
                        break

            item = {
                "nombre": p['nombre'],
                "precio": round(p['precio'], 2),
                "tipo": p['tipo'],
                "emoji": p.get('emoji', ''),
            }
            secciones[seccion_asignada].append(item)
            t_precio += p['precio']
            t_prot += p['prot_pack']
            t_kcal += p['kcal_pack']
            t_gras += p['gras_pack']
            t_carb += p['carb_pack']

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
        "secciones": secciones
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
        # Re-indexar safe_id
        for i, p in enumerate(productos):
            p['safe_id'] = i
        print(f"  [FILTER] Excluidos tipos {excluir_tipos} -> {len(productos)} prods")

    prot_sem = proteina_diaria * 7
    kcal_sem = kcal_diaria * 7
    carb_sem = carbohidratos_diarios * 7 if carbohidratos_diarios else None
    gras_sem = grasas_diarias * 7 if grasas_diarias else None

    # Versión A
    va = resolver_version(productos, presupuesto_max, prot_sem, kcal_sem,
                          carb_sem, gras_sem, excluir_ids=set(), version_name="A")

    # Versión B: excluir prods de A
    ids_a = set()
    if 'secciones' in va:
        nombres_a = set()
        for sec in va['secciones'].values():
            for item in sec:
                nombres_a.add(item['nombre'])
        for p in productos:
            if p['nombre'] in nombres_a:
                ids_a.add(p['safe_id'])

    vb = resolver_version(productos, presupuesto_max, prot_sem, kcal_sem,
                          carb_sem, gras_sem, excluir_ids=ids_a, version_name="B")

    # Versión C: excluir prods de A+B
    ids_ab = set(ids_a)
    if 'secciones' in vb:
        nombres_b = set()
        for sec in vb['secciones'].values():
            for item in sec:
                nombres_b.add(item['nombre'])
        for p in productos:
            if p['nombre'] in nombres_b:
                ids_ab.add(p['safe_id'])

    vc = resolver_version(productos, presupuesto_max, prot_sem, kcal_sem,
                          carb_sem, gras_sem, excluir_ids=ids_ab, version_name="C")

    return {"version_a": va, "version_b": vb, "version_c": vc}


if __name__ == "__main__":
    result = generar_propuestas_api(presupuesto_max=50, proteina_diaria=150, kcal_diaria=2400)
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