# 💡 Ideas — Mercadona AI Optimizer

## 🔥 Alto impacto, factibles

### 1. 📅 Menú semanal generado
No solo qué comprar, sino QUÉ COCINAR cada día. El solver asigna productos a platos concretos: "Lunes comida: pollo + arroz + verdura". Esto le da sentido real a la cesta.

### 2. 🔄 Actualización automática de precios
Re-ejecutar el ETL periódicamente (scraping/API) para mantener precios y productos actualizados. Los datos actuales son estáticos.

### 3. ⚖️ Perfiles de usuario
"Estoy a dieta", "Soy deportista", "Vegano/vegetariano". Cada perfil auto-configura macros y excluye categorías (ej: vegano excluye carne/pescado/lácteo/huevo).

### 4. 📊 Dashboard nutricional
Gráficos visuales: distribución de macros por comida, reparto calórico, diversidad de categorías. Con Chart.js o similar.

---

## 💡 Impacto medio, interesantes

### 5. 🛒 Lista de la compra exportable
Botón "Copiar lista" o "Descargar PDF" con productos agrupados por pasillo de supermercado (lácteos, carnes, frutería...).

### 6. ❤️ Favoritos y blacklist
El usuario marca productos que le gustan (forzar inclusión) o que odia (excluir). Se guardan en localStorage o BBDD.

### 7. 🔀 Botón "Regenerar" por sección
Si no te gusta la cena de la Versión A pero el resto está bien, regenerar solo esa sección manteniendo el resto fijo.

### 8. 📱 PWA (Progressive Web App)
Funciona offline y se instala como app en el móvil. Ideal para consultar la lista en el supermercado.

---

## 🚀 Ambiciosas (más curro pero WOW)

### 9. 🤖 Integración con IA generativa
Usar un LLM para generar recetas a partir de los productos seleccionados. "Tienes pollo, arroz y pimiento → Arroz con pollo al estilo asiático".

### 10. 📈 Histórico de compras
Guardar las cestas generadas, comparar semanas, ver tendencias de gasto. Login con auth básico.

### 11. 🗺️ Comparador de supermercados
Añadir datos de Lidl, Carrefour, DIA... y comparar la misma cesta entre supermercados.

### 12. 🧪 A/B testing de dietas
Generar 2 planes distintos para 2 semanas y que el usuario puntúe cuál le funcionó mejor.
