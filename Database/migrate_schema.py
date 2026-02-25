"""
Database Migration Script - Mercadona Optimizer
Migra la tabla plana 'productos' a un esquema normalizado de 5 tablas.
USO: python Database/migrate_schema.py
"""
from sqlalchemy import create_engine, text
import re
import json

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/mercadona_db"

# =====================================================================
# CLASIFICADOR MEJORADO (v2) - Más preciso que el runtime original
# =====================================================================
CLASIFICACION = {
    'pescado': {
        'keywords': [
            'pescado', 'atun', 'atún', 'merluza', 'salmon', 'salmón',
            'bacalao', 'sardina', 'pez gallo', 'lubina', 'gamba',
            'langostino', 'calamar', 'sepia', 'mejillon', 'mejillón',
            'pulpo', 'trucha', 'bonito', 'anchoa', 'boqueron', 'boquerón',
            'zamburiña', 'berberecho', 'navaja', 'caballa', 'pez espada',
            'rape', 'lenguado', 'rodaballo', 'palito de cangrejo',
            'surimi', 'caviar', 'ahumado de', 'salmón ahumado',
            # v4: reclasificar "Otros"
            'almeja', 'chirla', 'gambón', 'gambon', 'panga', 'nécora',
            'necora', 'concha fina', 'rabas', 'salpicón de marisco',
            'salpicon de marisco', 'anillas de pota', 'almejón', 'almejon',
            'filetes de panga',
        ],
        'emoji': '🐟'
    },
    'carne': {
        'keywords': [
            'carne', 'pollo', 'pavo', 'cerdo', 'ternera', 'vacuno',
            'buey', 'hamburguesa', 'longaniza', 'salchicha', 'jamon',
            'jamón', 'lomo', 'solomillo', 'conejo', 'albondiga',
            'albóndiga', 'picada', 'costilla', 'chuleton', 'chuletón',
            'entrecot', 'fuet', 'chorizo', 'morcilla', 'butifarra',
            'secreto', 'magro', 'pechuga', 'muslo', 'contramuslo',
            'fiambre', 'mortadela', 'salami', 'sobrasada', 'cecina',
            'carpaccio', 'steak', 'nugget', 'escalope', 'cordero',
            # v4: reclasificar "Otros"
            'bacón', 'bacon', 'chistorra', 'codorniz', 'codornices',
            'embutido', 'lacón', 'lacon', 'magret', 'maxi york', 'york',
            'panceta', 'salchichón', 'salchichon', 'compango',
            'croqueta', 'burger',
        ],
        'emoji': '🥩'
    },
    'verdura': {
        'keywords': [
            'verdura', 'ensalada', 'brocoli', 'brócoli', 'espinaca',
            'acelga', 'pimiento', 'tomate', 'calabacin', 'calabacín',
            'berenjena', 'pepino', 'lechuga', 'canonigos', 'canónigos',
            'setas', 'champiñon', 'champiñón', 'cebolla', 'zanahoria',
            'judia verde', 'judía verde', 'coliflor', 'repollo',
            'perejil', 'alcachofa', 'esparrago', 'espárrago', 'guisante',
            'maiz dulce', 'remolacha', 'nabo', 'puerro', 'col',
            'menestra', 'gazpacho', 'salmorejo', 'crema de verdura',
            # v4: reclasificar "Otros"
            'endibia', 'escarola', 'habas', 'rúcula', 'rucula',
            'fritada', 'pisto', 'ensaladilla', 'guacamole', 'rabanito',
            'batata', 'yuca', 'cebollita', 'palmito', 'chucrut',
            'tabulé', 'tabule', 'sticks vegetales',
            'crema de calabaza', 'garrofón', 'garrofon',
        ],
        'emoji': '🥦'
    },
    'fruta': {
        'keywords': [
            'fruta', 'platano', 'plátano', 'manzana', 'pera', 'naranja',
            'mandarina', 'kiwi', 'uva', 'melon', 'melón', 'sandia',
            'sandía', 'piña', 'aguacate', 'limon', 'limón', 'fresa',
            'cereza', 'banana', 'ciruela', 'melocoton', 'melocotón',
            'nectarina', 'mango', 'papaya', 'coco', 'granada',
            'frambuesa', 'arandano', 'arándano', 'mora', 'higo',
            # v4: reclasificar "Otros"
            'albaricoque', 'dátil', 'datil', 'pomelo', 'orejones',
            'pasas', 'frutos rojos', 'castaña', 'castañas',
        ],
        'emoji': '🍎'
    },
    'lacteo': {
        'keywords': [
            'leche', 'yogur', 'queso', 'kefir', 'kéfir', 'cuajada',
            'mantequilla', 'nata', 'requesón', 'mozzarella', 'brie',
            'camembert', 'cheddar', 'parmesano', 'gouda', 'emmental',
            'feta', 'mascarpone', 'burrata', 'crema de queso',
            'batido de', 'leche de',
            # v4: reclasificar "Otros"
            'bífidus', 'bifidus', 'petit', 'margarina',
            'batido sabor', 'horchata',
        ],
        'emoji': '🥛'
    },
    'legumbre': {
        'keywords': [
            'lenteja', 'garbanzo', 'alubia', 'judia', 'judía', 'hummus',
            'soja', 'edamame', 'guisante seco', 'frijol',
            # v4: reclasificar "Otros"
            'fabada', 'cocido', 'altramuz', 'altramuces',
        ],
        'emoji': '🫘'
    },
    'cereal': {
        'keywords': [
            'arroz', 'pasta', 'macarron', 'macarrón', 'espagueti',
            'spaghetti', 'fideo', 'pan ', 'patata', 'avena', 'cereal',
            'harina', 'trigo', 'maiz', 'maíz', 'cous', 'gnocchi',
            'lasaña', 'tagliatelle', 'penne', 'fusilli', 'tortellini',
            'canelón', 'canelon', 'quinoa', 'bulgur',
            # v4: reclasificar "Otros"
            'panecillo', 'baguette', 'hogaza', 'picos', 'crackers',
            'bocadillo', 'chapata', 'centeno', 'tostada', 'wrap',
            'hélices', 'helices', 'tallarines', 'pajaritas', 'fideuá',
            'fideua', 'muesli', 'semillas de chía', 'semillas lino',
            'semillas sésamo', 'semillas sesamo', 'masa de hojaldre',
            'masa fresca', 'obleas', 'barra de pan', 'rosquilleta',
            'piquitos', 'regañá', 'nacho',
        ],
        'emoji': '🌾'
    },
    'huevo': {
        'keywords': ['huevo', 'tortilla'],
        'emoji': '🥚'
    },
    'capricho': {
        'keywords': [
            'pizza', 'helado', 'chocolate', 'galleta', 'bombones',
            'turron', 'turrón', 'pastel', 'tarta', 'bizcocho', 'chips',
            'snack', 'gominola', 'caramelo', 'natillas', 'copa de',
            'mousse', 'croissant', 'donut', 'churro', 'palmera',
            'magdalena', 'brownie', 'cookie', 'barrita de',
            # v4: reclasificar "Otros"
            'ensaimada', 'berlina', 'gofre', 'porra', 'farton',
            'mantecada', 'sobao', 'golosina', 'xuxe', 'cuqui',
            'barquillo', 'hojaldre cabello', 'valenciana',
            'tiramisú', 'tiramisu', 'crema catalana',
            'almendra', 'nuez', 'anacardo', 'pistacho', 'cacahuete',
            'avellana', 'pipas', 'cocktail', 'coquito',
            'palitos con frutos', 'frutos secos',
            'regaliz', 'tubito', 'torta de aceite',
            'crepe', 'empanadilla',
        ],
        'emoji': '🍫'
    },
    'conserva': {
        'keywords': [
            'conserva', 'lata de', 'en aceite', 'en escabeche',
            'tomate frito', 'tomate triturado', 'aceitunas',
            # v4: reclasificar "Otros"
            'al natural hacendado', 'banderilla', 'pepinillo',
            'encurtido', 'alcaparra', 'piparra', 'guindilla',
        ],
        'emoji': '🥫'
    },
    'bebida': {
        'keywords': [
            'zumo', 'refresco', 'agua', 'cerveza', 'vino', 'cava',
            'bebida', 'cola', 'tonica', 'tónica', 'isotonica',
            # v4: reclasificar "Otros"
            'sangría', 'sangria', 'tinto de verano', 'licor',
            'malta', 'néctar', 'nectar', 'aperol', 'aperitivo',
            'flash popitos',
        ],
        'emoji': '🥤'
    },
    'condimento': {
        'keywords': [
            'sal ', 'pimienta', 'especia', 'oregano', 'orégano',
            'comino', 'pimenton', 'pimentón', 'canela', 'curry',
            'vinagre', 'salsa', 'ketchup', 'mayonesa', 'mostaza',
            'allioli', 'alioli', 'ajo granulado', 'caldo de',
            'sofrito', 'tabasco', 'sriracha',
            # v4: reclasificar "Otros"
            'cilantro', 'cayena', 'cúrcuma', 'curcuma', 'eneldo',
            'hierbabuena', 'hierbas provenzales', 'laurel',
            'jengibre', 'romero', 'sazonador', 'nuez moscada',
            'azafrán', 'azafran', 'aroma de vainilla', 'ñora',
            'miel', 'mermelada', 'sopa de miso',
        ],
        'emoji': '🧂'
    },
    'aceite': {
        'keywords': [
            'aceite de oliva', 'aceite de girasol', 'aceite vegetal',
            'aceite de coco',
        ],
        'emoji': '🫒'
    },
}

# Prioridad: pescado antes que carne (para anchoas, boquerones, etc.)
PRIORIDAD_CATEGORIAS = [
    'aceite', 'condimento', 'bebida', 'conserva',
    'pescado', 'huevo', 'carne', 'legumbre',
    'verdura', 'fruta', 'lacteo', 'cereal', 'capricho',
]

def clasificar_producto_v2(nombre):
    """Clasificador mejorado con prioridad de categorías."""
    n = nombre.lower()
    for cat in PRIORIDAD_CATEGORIAS:
        info = CLASIFICACION[cat]
        if any(kw in n for kw in info['keywords']):
            return cat
    return 'otros'


# =====================================================================
# REGLAS DE EXCLUSIÓN (datos corruptos o inútiles para el solver)
# =====================================================================
EXCLUSION_RULES = [
    ("calorias_100g > 750", "Calorías sospechosamente altas (probable error OCR)"),
    ("proteinas_100g > 55", "Proteínas sospechosamente altas (probable error OCR)"),
    ("proteinas_100g = 0 AND calorias_100g < 5", "Producto zombie (sin macros útiles)"),
]


def run_migration():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # =========================================================
        # PASO 1: Crear nuevas tablas
        # =========================================================
        print("[SCHEMA] Creando nuevas tablas...")

        # Drop old migration tables if they exist (for re-runs)
        for tbl in ['producto_tags', 'nutricion', 'exclusiones', 'productos_v2', 'tags', 'categorias']:
            conn.execute(text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))
        conn.commit()

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS categorias (
                id SERIAL PRIMARY KEY,
                nombre TEXT UNIQUE NOT NULL,
                tipo TEXT NOT NULL,     -- La key del dict (pescado, carne, etc.)
                emoji TEXT DEFAULT '📦'
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS productos_v2 (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                precio DOUBLE PRECISION NOT NULL DEFAULT 0,
                peso_gramos DOUBLE PRECISION NOT NULL DEFAULT 100,
                codigo_barras TEXT,
                categoria_id INTEGER REFERENCES categorias(id),
                imagen_url TEXT
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS nutricion (
                id SERIAL PRIMARY KEY,
                producto_id INTEGER UNIQUE REFERENCES productos_v2(id) ON DELETE CASCADE,
                proteinas_100g DOUBLE PRECISION DEFAULT 0,
                carbohidratos_100g DOUBLE PRECISION DEFAULT 0,
                grasas_100g DOUBLE PRECISION DEFAULT 0,
                calorias_100g DOUBLE PRECISION DEFAULT 0,
                fibra_100g DOUBLE PRECISION DEFAULT 0,
                azucar_100g DOUBLE PRECISION DEFAULT 0
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tags (
                id SERIAL PRIMARY KEY,
                nombre TEXT UNIQUE NOT NULL
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS producto_tags (
                producto_id INTEGER REFERENCES productos_v2(id) ON DELETE CASCADE,
                tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                PRIMARY KEY (producto_id, tag_id)
            );
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS exclusiones (
                id SERIAL PRIMARY KEY,
                producto_nombre TEXT NOT NULL,
                motivo TEXT NOT NULL,
                datos_originales JSONB
            );
        """))
        conn.commit()
        print("   ✅ Tablas creadas.")

        # =========================================================
        # PASO 2: Insertar categorías
        # =========================================================
        print("📂 Insertando categorías...")
        for tipo, info in CLASIFICACION.items():
            conn.execute(text(
                "INSERT INTO categorias (nombre, tipo, emoji) VALUES (:nom, :tipo, :emoji) "
                "ON CONFLICT (nombre) DO NOTHING"
            ), {"nom": tipo.capitalize(), "tipo": tipo, "emoji": info['emoji']})

        # Añadir 'Otros' para los no clasificados
        conn.execute(text(
            "INSERT INTO categorias (nombre, tipo, emoji) VALUES ('Otros', 'otros', '📦') "
            "ON CONFLICT (nombre) DO NOTHING"
        ))
        conn.commit()
        print("   ✅ Categorías listas.")

        # =========================================================
        # PASO 3: Cargar categorías en memoria (para FK lookup)
        # =========================================================
        cat_rows = conn.execute(text("SELECT id, tipo FROM categorias")).fetchall()
        cat_map = {r[1]: r[0] for r in cat_rows}  # {'pescado': 1, 'carne': 2, ...}

        # =========================================================
        # PASO 4: Migrar productos
        # =========================================================
        print("🔄 Migrando productos...")

        old_products = conn.execute(text("SELECT * FROM productos")).fetchall()
        col_names = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'productos' ORDER BY ordinal_position"
        )).fetchall()
        col_names = [c[0] for c in col_names]

        migrated = 0
        excluded = 0
        reclassified = 0

        for row in old_products:
            p = dict(zip(col_names, row))
            nombre = p.get('nombre', '')
            precio = p.get('precio', 0) or 0
            peso = p.get('peso_gramos', 100) or 100
            prot = p.get('proteinas_100g', 0) or 0
            kcal = p.get('calorias_100g', 0) or 0
            gras = p.get('grasas_100g', 0) or 0
            carb = p.get('carbohidratos_100g', 0) or 0

            # --- CHECK EXCLUSIONES ---
            should_exclude = False
            motivo = ""
            if kcal > 750:
                should_exclude = True
                motivo = f"Calorías sospechosas: {kcal} kcal/100g"
            elif prot > 55:
                should_exclude = True
                motivo = f"Proteínas sospechosas: {prot}g/100g"
            elif prot <= 0.1 and kcal < 5:
                should_exclude = True
                motivo = "Producto zombie (sin macros útiles)"
            elif precio <= 0:
                should_exclude = True
                motivo = "Precio inválido"

            if should_exclude:
                datos_json = json.dumps({
                    "precio": precio, "kcal": kcal,
                    "prot": prot, "peso": peso
                })
                conn.execute(text(
                    "INSERT INTO exclusiones (producto_nombre, motivo, datos_originales) "
                    "VALUES (:nombre, :motivo, CAST(:datos AS jsonb))"
                ), {
                    "nombre": nombre,
                    "motivo": motivo,
                    "datos": datos_json
                })
                excluded += 1
                continue

            # --- CLASIFICAR ---
            tipo = clasificar_producto_v2(nombre)
            cat_id = cat_map.get(tipo, cat_map['otros'])

            old_cat = p.get('categoria', 'Varios')
            if old_cat == 'Varios' and tipo != 'otros':
                reclassified += 1

            # --- INSERTAR PRODUCTO ---
            result = conn.execute(text(
                "INSERT INTO productos_v2 (nombre, precio, peso_gramos, codigo_barras, categoria_id, imagen_url) "
                "VALUES (:n, :p, :w, :cb, :cid, :img) RETURNING id"
            ), {
                "n": nombre, "p": precio, "w": peso,
                "cb": p.get('codigo_barras', ''),
                "cid": cat_id,
                "img": p.get('imagen_url', '')
            })
            new_id = result.fetchone()[0]

            # --- INSERTAR NUTRICIÓN ---
            conn.execute(text(
                "INSERT INTO nutricion (producto_id, proteinas_100g, carbohidratos_100g, grasas_100g, calorias_100g) "
                "VALUES (:pid, :prot, :carb, :gras, :kcal)"
            ), {"pid": new_id, "prot": prot, "carb": carb, "gras": gras, "kcal": kcal})

            # --- INSERTAR TAGS ---
            old_tags = p.get('tags', '') or ''
            for tag_name in old_tags.split(','):
                tag_name = tag_name.strip()
                if not tag_name:
                    continue
                # Upsert tag
                conn.execute(text(
                    "INSERT INTO tags (nombre) VALUES (:t) ON CONFLICT (nombre) DO NOTHING"
                ), {"t": tag_name})
                tag_row = conn.execute(text(
                    "SELECT id FROM tags WHERE nombre = :t"
                ), {"t": tag_name}).fetchone()
                if tag_row:
                    conn.execute(text(
                        "INSERT INTO producto_tags (producto_id, tag_id) VALUES (:pid, :tid) "
                        "ON CONFLICT DO NOTHING"
                    ), {"pid": new_id, "tid": tag_row[0]})

            migrated += 1

        conn.commit()

        # =========================================================
        # PASO 5: Resumen
        # =========================================================
        print(f"\n{'='*60}")
        print(f"📊 MIGRACIÓN COMPLETADA")
        print(f"{'='*60}")
        print(f"   ✅ Productos migrados:    {migrated}")
        print(f"   🔄 Reclasificados (Varios → tipo real): {reclassified}")
        print(f"   ⛔ Excluidos (datos corruptos):         {excluded}")
        print(f"{'='*60}")

        # Verificación rápida
        print("\n📂 Distribución por categoría (NUEVA):")
        dist = conn.execute(text(
            "SELECT c.tipo, c.emoji, COUNT(p.id) as n "
            "FROM categorias c LEFT JOIN productos_v2 p ON p.categoria_id = c.id "
            "GROUP BY c.tipo, c.emoji ORDER BY n DESC"
        )).fetchall()
        for r in dist:
            print(f"   {r[1]} {r[0]:15s} → {r[2]} productos")

        print("\n⛔ Exclusiones:")
        excl = conn.execute(text(
            "SELECT motivo, COUNT(*) as n FROM exclusiones GROUP BY motivo ORDER BY n DESC"
        )).fetchall()
        for r in excl:
            print(f"   {r[0]:50s} → {r[1]}")


if __name__ == "__main__":
    run_migration()
