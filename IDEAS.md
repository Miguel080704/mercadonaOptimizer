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

### 13. 🎯 Objetivos semanales con seguimiento
El usuario define su objetivo ("perder peso", "ganar músculo", "comer más sano") y el sistema adapta automáticamente los macros, el reparto calórico y las restricciones. Al final de la semana, puede marcar si lo cumplió.

### 14. 💰 Modo "Ahorro extremo"
Un botón que minimiza precio por encima de todo: solo marca blanca, prioriza ofertas, menos variedad pero máximo ahorro. Ideal para estudiantes/fin de mes.

### 15. 🧮 Calculadora de precio por gramo de proteína
Ranking en tiempo real de los productos más eficientes en €/g de proteína (o kcal/€). Para los que entrenan y quieren optimizar al máximo.

### 16. 🔔 Alertas de ofertas
Detectar cuando un producto que el usuario compra habitualmente baja de precio. Notificación push (PWA) o email: "¡Las pechugas de pollo están a 4.99€ esta semana!"

### 17. 👨‍👩‍👧‍👦 Modo familia / número de personas
Configurar para cuántas personas es la compra (1, 2, 4...). El solver multiplica cantidades y ajusta el presupuesto proporcionalmente.

---

## 💡 Impacto medio, interesantes

### 5. 🛒 Lista de la compra exportable ✅
Botón "Copiar lista" o "Descargar PDF" con productos agrupados por pasillo de supermercado (lácteos, carnes, frutería...).

### 6. ❤️ Favoritos y blacklist
El usuario marca productos que le gustan (forzar inclusión) o que odia (excluir). Se guardan en localStorage o BBDD.

### 7. 🔀 Botón "Regenerar" por sección
Si no te gusta la cena de la Versión A pero el resto está bien, regenerar solo esa sección manteniendo el resto fijo.

### 8. 📱 PWA (Progressive Web App)
Funciona offline y se instala como app en el móvil. Ideal para consultar la lista en el supermercado.

### 18. 🏷️ Etiquetas de alérgenos
Marcar alérgenos (gluten, lactosa, frutos secos...) y el solver excluye automáticamente productos que los contengan. Datos extraíbles de OpenFoodFacts.

### 19. 📤 Compartir cesta con amigos
Botón "Compartir" que genera un link único. Tu compañero de piso abre el link y ve la misma cesta — puede copiarla o editarla.

### 20. 🕐 Estimación de tiempo de preparación
Cada comida del menú muestra un tiempo estimado: "🟢 15min", "🟡 30min", "🔴 1h". Filtrar por "solo platos rápidos" para semanas ocupadas.

### 21. 📦 Agrupador de packs inteligente
Si compras 2 unidades del mismo producto, sugerir el pack ahorro si existe (ej: 2 pechugas sueltas vs 1 bandeja familiar más barata).

### 22. 🌡️ Modo temporada
Priorizar productos de temporada (frutas/verduras). Más baratos, más frescos, más sostenibles. Mapa de estacionalidad español.

### 23. 🎨 Temas y personalización UI
Modo claro/oscuro, temas de color personalizables, font size ajustable. Que el usuario haga suya la app.

### 24. 📊 Desglose calórico visual por comida
Gráfico de barras apiladas: cuántas kcal aporta cada comida del día. "Tu cena aporta el 40% — ¿seguro que quieres eso?"

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

### 25. 🗣️ Asistente de voz / chatbot
"Hazme una compra para 2 personas, 40€, alta en proteína y sin gluten" → la IA interpreta y configura el solver. Interfaz conversacional.

### 26. 📸 Escáner de ticket
Subes una foto del ticket de Mercadona → OCR extrae los productos → compara con lo que el optimizador sugirió. ¿Cuánto hubieras ahorrado?

### 27. 🧠 Machine Learning para predicción de gustos
Cuantas más cestas genere el usuario, más aprende el sistema qué le gusta. ML (collaborative filtering) para sugerir productos personalizados.

### 28. 🌍 Multi-idioma + internacionalización
Español, Catalán, Valenciano, Inglés, Portugués. Abrir la app a más público. i18n con react-intl o similar.

### 29. 📱 App nativa (React Native / Expo)
Portar la web a una app nativa de iOS/Android. Notificaciones push, acceso offline, escáner de código de barras integrado.

### 30. 🤝 Modo compartido en tiempo real
Dos personas editando la misma cesta a la vez (WebSockets). Ideal para parejas que deciden la compra juntos desde sitios distintos.

