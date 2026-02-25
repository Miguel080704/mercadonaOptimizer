"""Quick DB audit script - run once, then delete."""
from sqlalchemy import create_engine, text
import pandas as pd

DATABASE_URL = "postgresql://postgres:admin@localhost:5432/mercadona_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # 1. Schema
    print("=== SCHEMA ===")
    rows = conn.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = 'productos' ORDER BY ordinal_position"
    ))
    for r in rows:
        print(f"  {r[0]:25s} {r[1]}")

    # 2. Row count
    cnt = conn.execute(text("SELECT COUNT(*) FROM productos")).scalar()
    print(f"\n=== TOTAL ROWS: {cnt} ===")

    # 3. Sample 10 rows
    print("\n=== SAMPLE (10 rows) ===")
    df = pd.read_sql("SELECT * FROM productos LIMIT 10", conn)
    print(df.to_string())

    # 4. Null / zero audit
    print("\n=== DATA QUALITY ===")
    q = """
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN precio IS NULL OR precio <= 0 THEN 1 ELSE 0 END) AS bad_precio,
        SUM(CASE WHEN peso_gramos IS NULL OR peso_gramos <= 0 THEN 1 ELSE 0 END) AS bad_peso,
        SUM(CASE WHEN proteinas_100g IS NULL THEN 1 ELSE 0 END) AS null_prot,
        SUM(CASE WHEN calorias_100g IS NULL THEN 1 ELSE 0 END) AS null_kcal,
        SUM(CASE WHEN calorias_100g = 0 THEN 1 ELSE 0 END) AS zero_kcal,
        SUM(CASE WHEN proteinas_100g = 0 THEN 1 ELSE 0 END) AS zero_prot,
        SUM(CASE WHEN categoria IS NULL OR categoria = '' THEN 1 ELSE 0 END) AS bad_cat
    FROM productos
    """
    audit = pd.read_sql(q, conn)
    print(audit.to_string())

    # 5. Category distribution
    print("\n=== CATEGORIES ===")
    cats = pd.read_sql("SELECT categoria, COUNT(*) as n FROM productos GROUP BY categoria ORDER BY n DESC", conn)
    print(cats.to_string())

    # 6. Price stats
    print("\n=== PRICE STATS ===")
    stats = pd.read_sql("SELECT MIN(precio) as min_p, AVG(precio) as avg_p, MAX(precio) as max_p, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY precio) as median_p FROM productos WHERE precio > 0", conn)
    print(stats.to_string())

    # 7. Weight stats
    print("\n=== WEIGHT STATS ===")
    wstats = pd.read_sql("SELECT MIN(peso_gramos) as min_w, AVG(peso_gramos) as avg_w, MAX(peso_gramos) as max_w FROM productos WHERE peso_gramos > 0", conn)
    print(wstats.to_string())

    # 8. Suspicious products (very high protein per 100g - possible bad data)
    print("\n=== SUSPICIOUS: Protein > 50g/100g ===")
    susp = pd.read_sql("SELECT nombre, proteinas_100g, calorias_100g, precio, categoria FROM productos WHERE proteinas_100g > 50 ORDER BY proteinas_100g DESC LIMIT 15", conn)
    print(susp.to_string())

    # 9. Suspicious: very high calories
    print("\n=== SUSPICIOUS: Calories > 600 kcal/100g ===")
    susp2 = pd.read_sql("SELECT nombre, calorias_100g, proteinas_100g, precio, categoria FROM productos WHERE calorias_100g > 600 ORDER BY calorias_100g DESC LIMIT 15", conn)
    print(susp2.to_string())

    # 10. Tags distribution (if column exists)
    try:
        print("\n=== TAGS SAMPLE ===")
        tags = pd.read_sql("SELECT tags, COUNT(*) as n FROM productos GROUP BY tags ORDER BY n DESC LIMIT 20", conn)
        print(tags.to_string())
    except:
        print("  (no tags column)")
