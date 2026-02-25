from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/mercadona_db"
engine = create_engine(DATABASE_URL)

print("🧹 OPERACIÓN 'DIETA REAL': Eliminando huesos y verduras mutantes...")

with engine.connect() as conn:
    # 1. BORRAR DESPERDICIOS CÁRNICOS (Huesos, carcasas, pieles)
    print(" - Eliminando carcasas y huesos...")
    conn.execute(text("""
        DELETE FROM productos 
        WHERE nombre ILIKE '%Carcasa%' 
           OR nombre ILIKE '%Espinazo%'
           OR nombre ILIKE '%Hueso%'
           OR nombre ILIKE '%Cuello%'
           OR nombre ILIKE '%Piel%'
           OR nombre ILIKE '%Callos%'
           OR nombre ILIKE '%Sangre%'
           OR nombre ILIKE '%Recortes%'
           OR nombre ILIKE '%Arreglo%'
           OR nombre ILIKE '%Preparado%'
    """))

    # 2. BORRAR VERDURAS "RADIOACTIVAS" (Errores de proteína)
    # Ninguna verdura (salvo legumbres secas) tiene más de 10g de proteína.
    print(" - Eliminando zanahorias musculadas y similares...")
    conn.execute(text("""
        DELETE FROM productos 
        WHERE (categoria ILIKE '%Verdura%' OR nombre ILIKE '%Zanahoria%' OR nombre ILIKE '%Lechuga%')
          AND proteinas_100g > 10
    """))

    # 3. BORRAR EL PEREJIL RESISTENTE
    conn.execute(text("DELETE FROM productos WHERE nombre ILIKE '%Perejil%'"))

    # 4. CAPA DE SEGURIDAD GENERAL
    # Borrar cualquier cosa que cueste menos de 3€ y diga tener más de 100g de proteína TOTAL por paquete
    # (Salvo legumbres de 1kg, que sí pueden tener 200g)
    # Esto elimina el "Atún falso" y las "Zanahorias falsas" de golpe.
    conn.execute(text("""
        DELETE FROM productos 
        WHERE (proteinas_100g * peso_gramos / 100.0) > 150 
          AND precio < 3.0
          AND nombre NOT ILIKE '%Lenteja%' 
          AND nombre NOT ILIKE '%Garbanzo%' 
          AND nombre NOT ILIKE '%Alubia%'
    """))

    conn.commit()

print("✨ ¡LIMPIEZA TERMINADA! Ahora solo queda COMIDA DE VERDAD.")