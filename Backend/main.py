from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
import sys, os, base64, uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizer_logic import generar_propuestas_api
from database import get_db
from auth import hash_password, verify_password, create_access_token, require_auth, get_current_user_id
from models import (
    RegisterRequest, LoginRequest, PerfilUpdate,
    DietaRequest, PERFILES_DIETA, PedidoRequest
)

# Crear carpeta para fotos de perfil
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Mercadona Optimizer API", version="6.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos estáticos (fotos de perfil)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# =====================================================================
# AUTH ENDPOINTS
# =====================================================================

@app.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    exists = db.execute(
        text("SELECT id FROM usuarios WHERE email = :e"), {"e": req.email}
    ).fetchone()
    if exists:
        raise HTTPException(status_code=400, detail="Este email ya está registrado")

    hashed = hash_password(req.password)

    # Get default macros from profile
    perfil = PERFILES_DIETA.get(req.perfil_dieta or "estandar", PERFILES_DIETA["estandar"])

    result = db.execute(
        text("""
            INSERT INTO usuarios (email, password_hash, nombre, apellidos, perfil_dieta,
                                  proteinas_default, calorias_default, carbohidratos_default, grasas_default)
            VALUES (:email, :hash, :nombre, :apellidos, :perfil,
                    :prot, :kcal, :carb, :gras)
            RETURNING id
        """),
        {
            "email": req.email, "hash": hashed,
            "nombre": req.nombre, "apellidos": req.apellidos,
            "perfil": req.perfil_dieta or "estandar",
            "prot": perfil["proteinas"], "kcal": perfil["calorias"],
            "carb": perfil.get("carbohidratos"), "gras": perfil.get("grasas"),
        }
    )
    db.commit()
    user_id = result.fetchone()[0]
    token = create_access_token({"user_id": user_id})
    return {"token": token, "user_id": user_id, "message": "Registro exitoso"}


@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id, password_hash, nombre FROM usuarios WHERE email = :e"),
        {"e": req.email}
    ).fetchone()
    if not row or not verify_password(req.password, row[1]):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    token = create_access_token({"user_id": row[0]})
    return {"token": token, "user_id": row[0], "nombre": row[2]}


@app.get("/me")
def get_me(user_id: int = Depends(require_auth), db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            SELECT id, email, nombre, apellidos, perfil_dieta,
                   presupuesto_default, proteinas_default, calorias_default,
                   carbohidratos_default, grasas_default, foto_url
            FROM usuarios WHERE id = :id
        """),
        {"id": user_id}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "id": row[0], "email": row[1], "nombre": row[2], "apellidos": row[3],
        "perfil_dieta": row[4],
        "presupuesto_default": row[5], "proteinas_default": row[6],
        "calorias_default": row[7], "carbohidratos_default": row[8],
        "grasas_default": row[9], "foto_url": row[10],
    }


@app.put("/perfil")
def update_perfil(req: PerfilUpdate, user_id: int = Depends(require_auth),
                  db: Session = Depends(get_db)):
    updates = []
    params = {"id": user_id}

    field_map = {
        "nombre": "nombre", "apellidos": "apellidos",
        "perfil_dieta": "perfil", "presupuesto_default": "pres",
        "proteinas_default": "prot", "calorias_default": "kcal",
        "carbohidratos_default": "carb", "grasas_default": "gras",
        "foto_url": "foto",
    }
    for field, param in field_map.items():
        val = getattr(req, field, None)
        if val is not None:
            updates.append(f"{field} = :{param}")
            params[param] = val

    if not updates:
        raise HTTPException(status_code=400, detail="Nada que actualizar")

    query = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = :id"
    db.execute(text(query), params)
    db.commit()
    return {"message": "Perfil actualizado"}


@app.post("/upload-foto")
async def upload_foto(file: UploadFile = File(...),
                      user_id: int = Depends(require_auth),
                      db: Session = Depends(get_db)):
    """Sube foto de perfil y guarda la URL."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo se permiten imágenes")

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    foto_url = f"/uploads/{filename}"
    db.execute(
        text("UPDATE usuarios SET foto_url = :url WHERE id = :id"),
        {"url": foto_url, "id": user_id}
    )
    db.commit()
    return {"foto_url": foto_url}


@app.get("/perfiles")
def get_perfiles():
    return PERFILES_DIETA


# =====================================================================
# OPTIMIZER ENDPOINT
# =====================================================================

@app.get("/")
def read_root():
    return {"status": "online", "version": "6.1.0"}

@app.post("/optimizar")
def post_optimizar(request: DietaRequest):
    try:
        resultado = generar_propuestas_api(
            presupuesto_max=request.presupuesto,
            proteina_diaria=request.proteinas,
            kcal_diaria=request.calorias,
            carbohidratos_diarios=request.carbohidratos,
            grasas_diarias=request.grasas,
            excluir_tipos=request.excluir_tipos,
            secciones_fijas=request.secciones_fijas,
            solo_version=request.solo_version,
        )
        return resultado
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/buscar-productos")
def buscar_productos(q: str = "", db: Session = Depends(get_db)):
    """Busca productos por nombre. Devuelve hasta 20 resultados con macros."""
    if len(q) < 2:
        return []
    rows = db.execute(
        text("""
            SELECT p.id, p.nombre, p.precio, p.peso_gramos, p.imagen_url,
                   c.tipo, c.emoji, p.momentos,
                   n.proteinas_100g, n.carbohidratos_100g, n.grasas_100g, n.calorias_100g
            FROM productos_v2 p
            JOIN categorias c ON p.categoria_id = c.id
            JOIN nutricion n ON n.producto_id = p.id
            WHERE p.nombre ILIKE :q AND p.precio > 0
            ORDER BY p.nombre ASC
            LIMIT 20
        """),
        {"q": f"%{q}%"}
    ).fetchall()
    result = []
    for r in rows:
        peso = max(float(r[3] or 100), 1)
        factor = peso / 100.0
        result.append({
            "nombre": r[1],
            "precio": round(float(r[2]), 2),
            "tipo": r[5],
            "emoji": r[6] or "",
            "imagen_url": r[4] or "",
            "momentos": r[7] or ["comida", "cena"],
            "prot_pack": round((r[8] or 0) * factor, 1),
            "kcal_pack": round((r[11] or 0) * factor, 0),
            "carb_pack": round((r[9] or 0) * factor, 1),
            "gras_pack": round((r[10] or 0) * factor, 1),
        })
    return result
@app.post("/pedidos")
def crear_pedido(req: PedidoRequest, user_id: int = Depends(require_auth), db: Session = Depends(get_db)):
    """Crea un nuevo pedido guardando la cesta comprada por el usuario."""
    import json
    result = db.execute(
        text("""
            INSERT INTO pedidos (usuario_id, precio_total, version_label, macros_json, secciones_json)
            VALUES (:uid, :precio, :label, :macros, :secciones)
            RETURNING id, fecha
        """),
        {
            "uid": user_id,
            "precio": req.precio_total,
            "label": req.version_label,
            "macros": json.dumps(req.macros_json),
            "secciones": json.dumps(req.secciones_json)
        }
    )
    db.commit()
    row = result.fetchone()
    return {"id": row[0], "fecha": row[1], "message": "Pedido realizado con éxito"}

@app.get("/pedidos")
def listar_pedidos(user_id: int = Depends(require_auth), db: Session = Depends(get_db)):
    """Devuelve el historial de pedidos del usuario, ordenado por fecha desc."""
    rows = db.execute(
        text("""
            SELECT id, fecha, precio_total, version_label, macros_json, secciones_json
            FROM pedidos
            WHERE usuario_id = :uid
            ORDER BY fecha DESC
        """),
        {"uid": user_id}
    ).fetchall()
    
    pedidos = []
    for r in rows:
        pedidos.append({
            "id": r[0],
            "fecha": r[1].isoformat(),
            "precio_total": float(r[2]),
            "version_label": r[3],
            "macros_json": r[4] if isinstance(r[4], dict) else {},
            "secciones_json": r[5] if isinstance(r[5], dict) else {}
        })
    return pedidos

def _init_db():
    engine = get_db().__next__().bind
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pedidos (
                id SERIAL PRIMARY KEY,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                precio_total DECIMAL(10, 2) NOT NULL,
                version_label VARCHAR(50) NOT NULL,
                macros_json JSONB NOT NULL,
                secciones_json JSONB NOT NULL
            );
        """))
        conn.commit()

if __name__ == "__main__":
    _init_db()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)