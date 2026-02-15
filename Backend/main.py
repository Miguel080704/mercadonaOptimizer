import sys
import os

# Esto obliga a Python a ver la carpeta actual como base del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from backend.optimizer_logic import resolver_dieta# Importamos tu lógica

app = FastAPI(title="Mercadona Optimizer API")

# Definimos qué datos esperamos recibir de la web (El "Contrato")
class DietaRequest(BaseModel):
    presupuesto: float
    proteina_min: float
    calorias_max: float
    grasas_max: Optional[float] = None
    carbos_max: Optional[float] = None
    vetados: Optional[List[str]] = []
    obligatorios: Optional[List[str]] = []
    antojos_tags: Optional[List[str]] = []
    max_caprichos: Optional[int] = 1

@app.get("/")
def home():
    return {"mensaje": "Servidor de Mercadona Optimizer funcionando 🚀"}

@app.post("/optimizar")
def post_optimizar(request: DietaRequest):
    """
    Este endpoint recibe los datos, llama al optimizador y devuelve la compra
    """
    try:
        # Llamamos a la función que ya teníamos hecha
        resultado = resolver_dieta(
            presupuesto=request.presupuesto,
            proteina_min=request.proteina_min,
            calorias_max=request.calorias_max,
            grasas_max=request.grasas_max,
            carbos_max=request.carbos_max,
            vetados=request.vetados,
            obligatorios=request.obligatorios,
            antojos_tags=request.antojos_tags,
            max_caprichos=request.max_caprichos
        )
        
        # Si el optimizador no encontró solución, devolvemos un error 400
        if not resultado:
            raise HTTPException(status_code=400, detail="No se encontró una solución óptima")
            
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))