# 🚀 Cómo Ejecutar Mercadona Optimizer

Para arrancar el proyecto completo por tu cuenta, siempre tienes que levantar **dos cosas**: el Backend (servidor de Python/Base de datos) y el Frontend (interfaz de React).

Sigue estos dos pasos sencillos:

---

## 🟩 PASO 1: Iniciar el Backend (Python)
Esto arranca la API, la base de datos y la inteligencia del optimizador.

1. Abre una terminal nueva en Visual Studio Code.
2. Escribe o pega este comando y dale a Enter:
```bash
cd Backend
python main.py
```
*Deberías ver un mensaje que dice `INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)`.*

---

## 🟦 PASO 2: Iniciar el Frontend (React / Vite)
Esto arranca la interfaz visual para que puedas verla en tu navegador (Chrome, Safari...).

1. **Abre otra terminal nueva** (es importante que sea una ventana nueva, pulsando el `+` en la zona de terminales de VSCode, para no cerrar el Backend).
2. Escribe o pega este comando y dale a Enter:
```bash
cd Frontend
npm run dev
```
*Te saldrá un mensaje verde diciendo algo como `➜  Local:   http://localhost:5173/`.*

---

## 💻 PASO 3: Abrir la aplicación
Una vez que ambas terminales estén corriendo (una con Python y otra con Vite), abre tu navegador favorito y ve a esta dirección:

👉 **http://localhost:5173**

¡Y listo! Ya puedes usar la aplicación.

---

### ⚠️ Notas Comunes:
- **Port In Use (10048)**: Si al intentar arrancar el backend te sale un error de puerto ocupado, significa que ya hay otro backend abierto en segundo plano. Mata la terminal o usa este comando para cerrarlo a la fuerza: `Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force` (en Windows/PowerShell).
- Para **apagar** los servidores, pulsa `Ctrl + C` en cada una de sus pestañas de la terminal.
