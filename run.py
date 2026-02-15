import uvicorn
import sys
import os

# Esto asegura que la raíz del proyecto esté en el radar de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Lanzamos uvicorn programáticamente
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
    