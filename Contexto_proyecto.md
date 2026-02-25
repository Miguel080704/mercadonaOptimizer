# 🛒 MERCADONA OPTIMIZER - Contexto para el Agente IA

## 🎯 Objetivo del Proyecto (TFG)
Aplicación web que genera listas de la compra optimizadas usando productos reales de Mercadona. El usuario introduce su presupuesto, calorías máximas y proteínas mínimas, y el sistema devuelve **3 opciones de dieta (Económica, Equilibrada y Premium)** cumpliendo los macros mediante Programación Lineal.

## 💻 Stack Tecnológico
* **Backend:** Python 3, FastAPI, SQLAlchemy (para BBDD) y PuLP (Solver matemático CBC).
* **Base de Datos:** PostgreSQL (Tabla `productos` con datos de Mercadona).
* **Frontend:** HTML, CSS y JavaScript vainilla (Vanilla JS) en un solo archivo (`index.html`).

## 🧠 Lógica Core (¡IMPORTANTE NO ROMPER ESTO!)
El motor de optimización (`optimizer_logic.py`) usa `pulp` para resolver el problema de la mochila. Hemos iterado mucho la lógica para evitar que la IA tome decisiones matemáticamente perfectas pero humanamente estúpidas. 

**Reglas Críticas Actuales:**
1.  **Macros por Paquete:** La BBDD tiene macros por 100g. El algoritmo los convierte a macros *por paquete* (`peso_gramos / 100`) antes de calcular. Nadie compra "medio paquete" de lentejas.
2.  **Candado de Calorías Estricto:** La restricción de calorías máximas es inviolable (`<= kcal_semanal`). Si se da margen, el algoritmo se infla a comprar arroz y pasta para llegar al presupuesto.
3.  **Suelos de Gasto (Estrategia de 3 Niveles):**
    * *ECO:* Busca minimizar el precio puro y duro (Suele salir a ~15€).
    * *MEDIA:* Obligado a gastar el 50% del presupuesto. Exige 2 carnes, 2 verduras y 1 fruta.
    * *PREMIUM:* Obligado a gastar el 75% del presupuesto. Limita la repetición de productos a 1 unidad (máxima variedad) y exige pescado obligatoriamente.
4.  **Clasificador Híbrido:** Como las categorías de la BBDD son malas ("Varios", "Carnes"), el backend incluye una función `clasificar_producto()` que lee el nombre del producto y le asigna un tag real (`carne`, `pescado`, `lacteo`, `legumbre`, etc.) usando palabras clave.

## 🐛 Bugs Históricos Solucionados (Contexto)
* *El Bug de la Sal:* La sal y las especias tenían macros erróneos (ej. 50g de proteína por error de OCR de la API original) y eran baratísimas. El optimizador las usaba como base de la dieta. Se han purgado de la BBDD y el optimizador ignora productos de repostería/condimentos.
* *El Bug del Ternero:* El algoritmo recomendaba 6 litros de leche al día por ser barata. Ahora hay límites de repetición (`max_units = 3 if lacteo else 2`).

## 📍 Estado Actual (Dónde estamos)
1.  El Backend (`main.py` con FastAPI) funciona perfectamente, expone un endpoint POST en `/optimizar` que recibe `{presupuesto, proteinas, calorias}` y devuelve un JSON con las 3 opciones (Eco, Media, Premium) y sus macros calculados.
2.  El Frontend (`index.html`) ha sido actualizado para tener 3 columnas UI que renderizan este JSON de forma visual y atractiva.
3.  **Siguientes pasos:** Refinar la interfaz, hacer testing de casos extremos (presupuestos muy bajos) y añadir la integración con MCP para que puedas leer la BBDD directamente.