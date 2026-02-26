"""
Clasifica cada producto en momentos del día: desayuno, comida, merienda, cena.
Usa keywords del nombre del producto + tipo de categoría.
"""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/mercadona_db"

# =============================================================================
# REGLAS POR KEYWORD (nombre del producto)
# Si el nombre contiene alguna keyword → asignar SOLO esos momentos
# =============================================================================
KEYWORD_RULES = [
    # --- SOLO DESAYUNO ---
    (['cereales crunchy', 'corn flakes', 'copos de avena', 'avena molida',
      'muesli', 'cereales rellenos', 'mini cereales'], ['desayuno']),

    # --- DESAYUNO + MERIENDA ---
    (['galleta', 'tostada', 'pan tostado', 'biscote', 'pan de molde',
      'pan brioche', 'pan de leche', 'mermelada', 'margarina', 'mantequilla',
      'crackers', 'tortitas de arroz', 'tortitas de maíz', 'tortitas de legumbres',
      'barrita', 'grissini'], ['desayuno', 'merienda']),

    # --- DESAYUNO ---
    (['leche desnatada', 'leche entera', 'leche semidesnatada', 'leche fresca',
      'leche sin lactosa', 'leche calcio', 'leche +proteínas',
      'leche evaporada', 'leche condensada'], ['desayuno']),

    # --- DESAYUNO + MERIENDA ---
    (['yogur', 'bífidus', 'kéfir', 'petit',
      'cuajada', 'batido de', 'batido sabor'], ['desayuno', 'merienda']),

    # --- SOLO COMIDA + CENA (pasta/arroz/guarniciones) ---
    (['spaghetti', 'macarrón', 'fideo', 'fideuá', 'lasaña', 'tallarín',
      'hélices', 'pajaritas', 'pasta fusilli', 'pasta penne', 'pasta tiburón',
      'pasta tortiglioni', 'pasta trottole', 'pasta maravilla', 'pasta estrellas',
      'pasta fresca', 'gnocchi', 'tortellini', 'cous cous', 'sémola',
      'arroz basmati', 'arroz bomba', 'arroz integral', 'arroz largo',
      'arroz redondo', 'arroz vaporizado', 'arroz negro',
      'quinoa', 'puré de patata',
      'masa fresca', 'masa hojaldre', 'masa pizza', 'masa empanada',
      'mazorquita', 'maíz dulce'], ['comida', 'cena']),

    # --- COMIDA + CENA (patatas como guarnición) ---
    (['patatas cocida', 'patatas guarnición', 'patatas prefritas',
      'patatas para microondas'], ['comida', 'cena']),

    # --- MERIENDA (snacks de patata/maíz) ---
    (['patatas fritas clásicas', 'patatas fritas corte', 'patatas fritas extra',
      'patatas fritas paja', 'patatas fritas sabor', 'patatas light',
      'sticks de patata', 'nachos', 'aros de maíz', 'maíz frito',
      'tiras de maíz', 'palomitas', 'trigo snack',
      'cuquitos', 'garfitos', 'pelotazos', 'pandilla', 'cheetos',
      'pipas girasol'], ['merienda']),

    # --- COMIDA + CENA (quesos para cocinar) ---
    (['queso rallado', 'mozzarella', 'burrata', 'mascarpone',
      'nata para', 'queso provolone', 'pizza'], ['comida', 'cena']),

    # --- DESAYUNO + MERIENDA + CENA (quesos de tabla/picar) ---
    (['queso curado', 'queso semicurado', 'queso tierno', 'queso viejo',
      'queso azul', 'queso roquefort', 'queso camembert', 'queso emmental',
      'queso gouda', 'queso manchego', 'queso añejo', 'queso cabra',
      'queso en porciones', 'queso untar', 'queso fresco',
      'queso lonchas', 'queso grana', 'requesón',
      'tabla de quesos', 'crema de queso'], ['desayuno', 'merienda', 'cena']),

    # --- MERIENDA (dulces/postres) ---
    (['helado', 'tarta de queso', 'flan de queso', 'dulce de leche',
      'arroz con leche', 'bizcocho', 'barquillo',
      'horchata', 'pastas de aceite', 'obleas', 'surtido de pastas'], ['merienda']),

    # --- PAN (desayuno + comida + cena) ---
    (['baguette', 'barra de pan', 'hogaza', 'panecillo', 'picos',
      'rosquilletas', 'regañá', 'bocadillo', 'chapata',
      'pan viena', 'pan 5 semillas', 'pan campeón', 'pan fibra',
      'pan integral', 'pan redondo', 'pan hot dog',
      'wraps', 'semillas de chía', 'semillas lino', 'semillas sésamo',
      'tahini', 'pastel de aceite'], ['desayuno', 'comida', 'cena']),
]

# =============================================================================
# REGLAS POR DEFECTO (tipo de categoría, cuando ningún keyword coincide)
# =============================================================================
DEFAULT_BY_TIPO = {
    'carne':    ['comida', 'cena'],
    'pescado':  ['comida', 'cena'],
    'verdura':  ['comida', 'cena'],
    'legumbre': ['comida', 'cena'],
    'conserva': ['comida', 'cena'],
    'huevo':    ['desayuno', 'comida', 'cena'],
    'fruta':    ['desayuno', 'merienda'],
    'capricho': ['merienda'],
    'cereal':   ['desayuno', 'comida', 'merienda', 'cena'],  # fallback
    'lacteo':   ['desayuno', 'merienda'],                     # fallback
}


def clasificar_producto(nombre, tipo):
    """Devuelve lista de momentos para un producto."""
    nombre_lower = nombre.lower()

    # Intentar match por keywords (primera regla que coincida)
    for keywords, momentos in KEYWORD_RULES:
        for kw in keywords:
            if kw in nombre_lower:
                return momentos

    # Fallback: usar tipo de categoría
    return DEFAULT_BY_TIPO.get(tipo, ['comida', 'cena'])


def main():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT p.id, p.nombre, c.tipo
            FROM productos_v2 p
            JOIN categorias c ON p.categoria_id = c.id
        """)).fetchall()

        stats = {'desayuno': 0, 'comida': 0, 'merienda': 0, 'cena': 0}
        total = 0

        for pid, nombre, tipo in rows:
            momentos = clasificar_producto(nombre, tipo)
            conn.execute(
                text("UPDATE productos_v2 SET momentos = :m WHERE id = :id"),
                {"m": momentos, "id": pid}
            )
            for m in momentos:
                stats[m] = stats.get(m, 0) + 1
            total += 1

        conn.commit()

    print(f"\n[CLASIFICACION] {total} productos clasificados:")
    for k, v in sorted(stats.items()):
        print(f"  {k:12s} -> {v} productos pueden ir ahí")

    # Mostrar ejemplos
    with engine.connect() as conn:
        for momento in ['desayuno', 'comida', 'merienda', 'cena']:
            rows = conn.execute(text(f"""
                SELECT p.nombre, c.tipo, p.momentos
                FROM productos_v2 p
                JOIN categorias c ON p.categoria_id = c.id
                WHERE :m = ANY(p.momentos)
                ORDER BY RANDOM()
                LIMIT 5
            """), {"m": momento}).fetchall()
            print(f"\n  Ejemplo {momento.upper()}:")
            for r in rows:
                print(f"    {r[0][:50]:52s} ({r[1]:8s}) -> {r[2]}")


if __name__ == "__main__":
    main()
