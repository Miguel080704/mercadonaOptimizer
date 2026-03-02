"""
Modelos Pydantic (requests/responses) y perfiles de dieta.
"""
from pydantic import BaseModel
from typing import Optional

# =====================================================================
# PERFILES DE DIETA PREDEFINIDOS
# =====================================================================
PERFILES_DIETA = {
    "estandar": {
        "nombre": "⚡ Estándar",
        "proteinas": 150,
        "calorias": 2400,
        "carbohidratos": None,
        "grasas": None,
        "excluir_tipos": [],
    },
    "deportista": {
        "nombre": "🏋️ Deportista",
        "proteinas": 180,
        "calorias": 2800,
        "carbohidratos": 350,
        "grasas": 90,
        "excluir_tipos": [],
    },
    "deficit": {
        "nombre": "🥗 Dieta / Déficit",
        "proteinas": 150,
        "calorias": 1800,
        "carbohidratos": 180,
        "grasas": 60,
        "excluir_tipos": ["capricho"],
    },
    "vegano": {
        "nombre": "🌱 Vegano",
        "proteinas": 120,
        "calorias": 2200,
        "carbohidratos": 300,
        "grasas": 70,
        "excluir_tipos": ["carne", "pescado", "lacteo", "huevo"],
    },
    "vegetariano": {
        "nombre": "🥚 Vegetariano",
        "proteinas": 130,
        "calorias": 2200,
        "carbohidratos": 280,
        "grasas": 70,
        "excluir_tipos": ["carne", "pescado"],
    },
    "personalizado": {
        "nombre": "🔧 Personalizado",
        "proteinas": 150,
        "calorias": 2400,
        "carbohidratos": None,
        "grasas": None,
        "excluir_tipos": [],
    },
}

# =====================================================================
# REQUEST MODELS
# =====================================================================
class RegisterRequest(BaseModel):
    email: str
    password: str
    nombre: str
    apellidos: Optional[str] = None
    perfil_dieta: Optional[str] = "estandar"

class LoginRequest(BaseModel):
    email: str
    password: str

class PerfilUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    perfil_dieta: Optional[str] = None
    presupuesto_default: Optional[float] = None
    proteinas_default: Optional[float] = None
    calorias_default: Optional[float] = None
    carbohidratos_default: Optional[float] = None
    grasas_default: Optional[float] = None
    foto_url: Optional[str] = None

class DietaRequest(BaseModel):
    presupuesto: float
    proteinas: float
    calorias: float
    carbohidratos: Optional[float] = None
    grasas: Optional[float] = None
    excluir_tipos: Optional[list[str]] = None
    secciones_fijas: Optional[dict] = None
    solo_version: Optional[str] = None

class PedidoRequest(BaseModel):
    precio_total: float
    version_label: str
    macros_json: dict
    secciones_json: dict
