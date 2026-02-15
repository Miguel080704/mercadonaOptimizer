import pandas as pd
import requests
import urllib.parse
from difflib import SequenceMatcher
from sqlalchemy import create_engine, text

# --- CONFIGURACIÓN ---
DATABASE_URL = "postgresql://postgres:admin@localhost:5432/mercadona_db"
CSV_PATH = "etl/productos_semilla.csv"

# --- LÓGICA DE TRADUCCIÓN API -> TU SISTEMA ---
def detect_category_and_tags(api_data):
    """
    Traduce las categorías raras de la API (PNNS Groups) a tus categorías simples.
    También genera los TAGS automáticamente (dulce, salado, capricho...).
    """
    # Obtenemos los grupos oficiales de nutrición de la API
    g1 = api_data.get('pnns_groups_1', '').lower() # Ej: 'sugary snacks'
    g2 = api_data.get('pnns_groups_2', '').lower() # Ej: 'biscuits and cakes'
    
    categoria = 'Varios'
    tags = set() # Usamos un set para no repetir etiquetas
    
    # 1. MAPEO DE CATEGORÍAS (De API a Tu BBDD)
    if 'meat' in g1 or 'meat' in g2:
        categoria = 'Carnes'
        tags.add('salado'); tags.add('proteina'); tags.add('comida')
    elif 'fish' in g1 or 'fish' in g2 or 'seafood' in g2:
        categoria = 'Conservas' if 'canned' in g2 else 'Pescados'
        tags.add('salado'); tags.add('proteina'); tags.add('comida')
    elif 'egg' in g1 or 'egg' in g2:
        categoria = 'Huevos'
        tags.add('salado'); tags.add('proteina'); tags.add('desayuno')
    elif 'milk' in g1 or 'cheese' in g2 or 'dairy' in g1:
        categoria = 'Lacteos'
        tags.add('proteina')
        if 'milk' in g2: tags.add('liquido'); tags.add('desayuno')
        if 'cheese' in g2: tags.add('salado')
        if 'yogurt' in g2: tags.add('postre')
    elif 'cereals' in g1 or 'potatoes' in g1:
        categoria = 'Cereales'
        tags.add('neutro')
        if 'breakfast' in g2 or 'cereal' in g2: tags.add('desayuno')
        if 'rice' in g2: categoria = 'Arroces'; tags.add('comida')
    elif 'sugary snacks' in g1 or 'sweets' in g2 or 'chocolate' in g2 or 'ice cream' in g2:
        categoria = 'Caprichos'
        tags.add('dulce'); tags.add('capricho'); tags.add('snack')
    elif 'salty snacks' in g1 or 'appetizers' in g2:
        categoria = 'Caprichos'
        tags.add('salado'); tags.add('capricho')
    elif 'composite foods' in g1 or 'pizza' in g2 or 'sandwich' in g2:
        categoria = 'Caprichos' # O 'Precocinados'
        tags.add('salado'); tags.add('capricho'); tags.add('comida')
    
    # 2. GENERACIÓN EXTRA DE TAGS (Basado en nombre y nutrientes)
    nutriments = api_data.get('nutriments', {})
    azucar = nutriments.get('sugars_100g', 0)
    proteina = nutriments.get('proteins_100g', 0)
    
    if azucar > 20: tags.add('dulce')
    if proteina > 15: tags.add('proteina')
    if 'hacendado' in api_data.get('product_name', '').lower(): tags.add('marca_propia')

    # Convertimos el set de tags a string (ej: "dulce,capricho")
    tags_str = ",".join(list(tags)) if tags else "basico"
    
    return categoria, tags_str

def get_nutrients_from_product_data(product):
    nutrients = product.get('nutriments', {})
    
    # DETECCIÓN AUTOMÁTICA AQUÍ
    cat_detectada, tags_detectados = detect_category_and_tags(product)
    
    return {
        'proteinas_100g': nutrients.get('proteins_100g', 0),
        'carbohidratos_100g': nutrients.get('carbohydrates_100g', 0),
        'grasas_100g': nutrients.get('fat_100g', 0),
        'calorias_100g': nutrients.get('energy-kcal_100g', 0),
        'imagen_url': product.get('image_url', ''),
        'nombre_encontrado': product.get('product_name', 'Desconocido'),
        'categoria_detectada': cat_detectada, # <--- NUEVO CAMPO
        'tags_detectados': tags_detectados    # <--- NUEVO CAMPO
    }

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def search_product_by_barcode(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get('status') == 1:
            info = get_nutrients_from_product_data(data['product'])
            # Filtro anti-zombis (si todo es 0, lo descartamos)
            if info['proteinas_100g'] <= 0.1 and info['calorias_100g'] <= 1:
                return None
            return info
    except:
        pass
    return None

def search_product_waterfall(name):
    clean_name = name.replace("Hacendado", "").replace("Mercadona", "").strip()
    intentos = [f"{clean_name} Mercadona", f"{clean_name} Hacendado", clean_name]
    
    for intento in intentos:
        print(f"\n      🔎 Buscando: '{intento}'...", end="")
        encoded_name = urllib.parse.quote(intento)
        url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={encoded_name}&search_simple=1&action=process&json=1"
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
            products = data.get('products', [])
            
            best_match = None
            best_score = 0
            
            for p in products[:5]:
                score = similar(clean_name, p.get('product_name', ''))
                # Validar que tenga datos
                n = p.get('nutriments', {})
                tiene_datos = n.get('proteins_100g', 0) > 0 or n.get('energy-kcal_100g', 0) > 0
                
                if score > best_score and score > 0.4 and tiene_datos:
                    best_score = score
                    best_match = p
            
            if best_match:
                print(f" ✅", end="")
                return get_nutrients_from_product_data(best_match)
        except:
            pass
        print(" ❌", end="")
    return None

def main():
    print("🚀 Iniciando ETL 7.0 (Auto-Categorización con IA de OpenFoodFacts)...")
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        print("❌ Error: No encuentro el CSV.")
        return

    datos_enriquecidos = []

    for index, row in df.iterrows():
        nombre = row['nombre']
        barcode = str(row['codigo_barras'])
        peso = row['peso_gramos']
        
        print(f"\n📦 {nombre}...", end="")
        
        # BUSCAR INFORMACIÓN
        info = search_product_by_barcode(barcode)
        if not info:
            print(" -> Plan B...", end="")
            info = search_product_waterfall(nombre)

        if info:
            # MAGIA: Usamos la categoría detectada por la API en vez de la del CSV
            # (Si el CSV tiene una manual, la ignoramos o la usamos como fallback, aquí priorizo la API)
            categoria_final = info['categoria_detectada']
            tags_finales = info['tags_detectados']
            
            print(f"\n    🏷️ Detectado: [{categoria_final}] Tags: ({tags_finales})", end="")

            datos_enriquecidos.append({
                'nombre': nombre,
                'precio': row['precio'],
                'peso_pack': peso,
                'codigo_barras': barcode,
                'categoria': categoria_final, # <--- AUTO
                'tags': tags_finales,         # <--- AUTO
                **info
            })
        else:
            print("\n ❌ ERROR: Producto no encontrado.")

    # GUARDAR
    if datos_enriquecidos:
        df_final = pd.DataFrame(datos_enriquecidos)
        # Limpiamos columnas auxiliares
        cols_borrar = ['nombre_encontrado', 'categoria_detectada', 'tags_detectados']
        df_final = df_final.drop(columns=[c for c in cols_borrar if c in df_final.columns])
            
        engine = create_engine(DATABASE_URL)
        df_final.to_sql('productos', engine, if_exists='replace', index=False)
        
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE productos ADD COLUMN IF NOT EXISTS id SERIAL PRIMARY KEY;"))
            conn.commit()
        print(f"\n\n🎉 ¡EXITAZO! BBDD actualizada con Categorías Automáticas.")
    else:
        print("\n⚠️ Nada guardado.")

if __name__ == "__main__":
    main()