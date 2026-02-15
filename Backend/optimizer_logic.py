import pulp
from sqlalchemy import create_engine
import pandas as pd

# --- CONFIGURACIÓN ---
DATABASE_URL = "postgresql://postgres:admin@localhost:5432/mercadona_db"

def resolver_dieta(presupuesto, proteina_min, calorias_max, 
                   grasas_max=None, carbos_max=None,
                   vetados=[], obligatorios=[], 
                   antojos_tags=[], max_caprichos=None):
    
    # MANTENEMOS TU PRINT ORIGINAL
    print(f"\n🧠 OPTIMIZADOR INTELIGENTE (Basado en Categorías Auto-Detectadas)...")
    
    engine = create_engine(DATABASE_URL)
    try:
        df = pd.read_sql("SELECT * FROM productos WHERE precio > 0", engine)
    except Exception as e:
        print(f"❌ Error conectando a BBDD: {e}")
        return None

    productos = df.to_dict('records')
    
    # 1. PRE-PROCESAMIENTO DE DATOS
    for p in productos:
        factor = p['peso_pack'] / 100.0 
        p['proteina_pack'] = (p.get('proteinas_100g') or 0) * factor
        p['calorias_pack'] = (p.get('calorias_100g') or 0) * factor
        p['grasas_pack']   = (p.get('grasas_100g') or 0) * factor
        p['carbos_pack']   = (p.get('carbohidratos_100g') or 0) * factor
        
        raw_tags = p.get('tags') or ""
        p['lista_tags'] = [t.strip().lower() for t in raw_tags.split(',')]

    # 2. INICIAR PROBLEMA MATEMÁTICO
    prob = pulp.LpProblem("Dieta_Inteligente", pulp.LpMinimize)
    cantidades = pulp.LpVariable.dicts("Cant", [p['id'] for p in productos], lowBound=0, cat='Integer')

    # 3. OBJETIVO: MINIMIZAR DINERO
    prob += pulp.lpSum([p['precio'] * cantidades[p['id']] for p in productos]), "Coste_Total"

    # 4. RESTRICCIONES NUTRICIONALES
    prob += pulp.lpSum([p['proteina_pack'] * cantidades[p['id']] for p in productos]) >= proteina_min, "Min_Proteina"
    prob += pulp.lpSum([p['calorias_pack'] * cantidades[p['id']] for p in productos]) <= calorias_max, "Max_Calorias"
    prob += pulp.lpSum([p['precio'] * cantidades[p['id']] for p in productos]) <= presupuesto, "Max_Presupuesto"

    if grasas_max: 
        prob += pulp.lpSum([p['grasas_pack'] * cantidades[p['id']] for p in productos]) <= grasas_max
    if carbos_max: 
        prob += pulp.lpSum([p['carbos_pack'] * cantidades[p['id']] for p in productos]) <= carbos_max

    # 5. REGLAS DE NEGOCIO Y CATEGORÍAS
    if max_caprichos is not None:
        ids_caprichos = [p['id'] for p in productos if p.get('categoria') == 'Caprichos']
        if ids_caprichos:
            prob += pulp.lpSum([cantidades[i] for i in ids_caprichos]) <= max_caprichos, "Limite_Guarradas"
            print(f"   🥗 Modo Saludable: Máximo {max_caprichos} productos de categoría 'Caprichos'.")

    for p in productos:
        if any(v.lower() in p['nombre'].lower() for v in vetados): 
            prob += cantidades[p['id']] == 0
        if any(o.lower() in p['nombre'].lower() for o in obligatorios): 
            prob += cantidades[p['id']] >= 1
            
        limite = 6 if p.get('categoria') == 'Lacteos' else 2
        prob += cantidades[p['id']] <= limite

    for tag_deseado in antojos_tags:
        tag_clean = tag_deseado.lower()
        ids_validos = [p['id'] for p in productos if tag_clean in p['lista_tags']]
        if ids_validos:
            prob += pulp.lpSum([cantidades[i] for i in ids_validos]) >= 1
            print(f"   🍪 Antojo activo: Buscando algo '{tag_clean}'...")

    # 6. RESOLVER
    prob.solve(pulp.PULP_CBC_CMD(msg=0)) 

    # 7. RESULTADOS (PRINT + RETURN PARA LA API)
    if pulp.LpStatus[prob.status] == 'Optimal':
        print("\n✅ ¡COMPRA GENERADA CON ÉXITO!")
        print("="*60)
        
        cesta_final = []
        t_precio, t_prot, t_cal = 0, 0, 0
        
        for p in productos:
            qty = cantidades[p['id']].varValue
            if qty > 0:
                coste = float(qty * p['precio'])
                prot = float(qty * p['proteina_pack'])
                cal = float(qty * p['calorias_pack'])
                cat = p.get('categoria', 'Varios')
                
                # TU LÓGICA DE ICONOS SIGUE AQUÍ
                icon = "🍗" if cat=='Carnes' else "🐟" if cat=='Pescados' else "🥛" if cat=='Lacteos' else "🍪" if cat=='Caprichos' else "📦"
                
                # SIGUE IMPRIMIENDO EN TERMINAL
                print(f"{icon} {int(qty)}x {p['nombre']}")
                print(f"   └─ {cat} | {coste:.2f}€ | {prot:.1f}g Prot | {cal:.0f} kcal")
                
                # GUARDAMOS PARA LA WEB
                cesta_final.append({
                    "nombre": p['nombre'],
                    "cantidad": int(qty),
                    "precio": coste,
                    "proteina": prot,
                    "calorias": cal,
                    "categoria": cat,
                    "imagen": p.get('imagen_url', '')
                })
                
                t_precio += coste; t_prot += prot; t_cal += cal
        
        # PRINTS DE TOTALES
        print("="*60)
        print(f"💰 TOTAL: {t_precio:.2f}€")
        print(f"📊 MACROS: {t_prot:.1f}g Proteína | {t_cal:.0f} Calorías")

        # ESTO ES LO QUE RECIBE LA API
        return {
            "status": "success",
            "productos": cesta_final,
            "totales": {
                "precio": round(t_precio, 2),
                "proteina": round(t_prot, 1),
                "calorias": round(t_cal, 0)
            }
        }
    else:
        print("\n❌ NO SE ENCONTRÓ SOLUCIÓN.")
        return None

if __name__ == "__main__":
    resolver_dieta(presupuesto=30, proteina_min=160, calorias_max=3000, antojos_tags=["dulce"], max_caprichos=1)