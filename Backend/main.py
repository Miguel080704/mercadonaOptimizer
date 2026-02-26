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
    DietaRequest, PERFILES_DIETA
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
        )
        return resultado
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)