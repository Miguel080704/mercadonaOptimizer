from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

# Este pequeño "hack" ayuda a que Python encuentre siempre la carpeta backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimizer_logic import resolver_dieta

app = FastAPI(
    title="Mercadona Optimizer API",
    description="API para calcular la cesta de la compra óptima basada en macros y presupuesto",
    version="1.0.0"
)

# Definimos el esquema de lo que esperamos recibir (El "Contrato" de la API)
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
def read_root():
    return {"status": "online", "mensaje": "Servidor de Mercadona Optimizer funcionando correctamente 🚀"}

@app.post("/optimizar")
def post_optimizar(request: DietaRequest):
    """
    Recibe las preferencias del usuario y devuelve la lista de la compra optimizada.
    """
    # Llamamos a tu lógica (que ahora imprime en terminal Y devuelve un diccionario)
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
    
    # Si el optimizador devolvió None (Infeasible), lanzamos error 400
    if resultado is None:
        raise HTTPException(
            status_code=400, 
            detail="No se ha podido encontrar una combinación de productos que cumpla todos tus requisitos. Prueba a subir el presupuesto o bajar las proteínas."
        )
    
    # Si todo va bien, FastAPI convierte el diccionario automáticamente a JSON
    return resultado

if __name__ == "__main__":
    import uvicorn
    # Por si quieres ejecutarlo haciendo 'python backend/main.py'
    uvicorn.run(app, host="127.0.0.1", port=8000)