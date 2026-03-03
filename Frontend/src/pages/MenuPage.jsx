import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Sparkles, ArrowLeft, AlertTriangle, Coffee, Utensils, UtensilsCrossed, Calendar } from 'lucide-react';
import s from './MenuPage.module.css';

function MenuPage() {
    const location = useLocation();
    const navigate = useNavigate();
    const basketData = location.state?.basketData;
    const versionLabel = location.state?.versionLabel;

    const [menuData, setMenuData] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');

    // Para evitar doble ejecución en StrictMode
    const hasRequested = useRef(false);

    useEffect(() => {
        if (!basketData) {
            navigate('/');
            return;
        }

        if (!hasRequested.current) {
            hasRequested.current = true;
            generateMenuJSON();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const generateMenuJSON = async () => {
        setIsLoading(true);
        setError('');

        const apiKey = localStorage.getItem('groq_api_key');
        if (!apiKey) {
            setError('No has configurado tu API Key de Groq. Vuelve al Dashboard, entra en tu Perfil y añádela.');
            setIsLoading(false);
            return;
        }

        try {
            let ingredientsText = '';
            let totalKcal = 0;
            let totalProt = 0;
            let totalCarb = 0;
            let totalFat = 0;

            if (basketData.secciones) {
                for (const [secName, items] of Object.entries(basketData.secciones)) {
                    ingredientsText += `${secName.toUpperCase()}:\n`;
                    items.forEach(p => {
                        ingredientsText += `- ${p.nombre} (${p.peso_pack}) [${p.kcal_pack}kcal, ${p.prot_pack}g prot]\n`;
                    });
                }
            }

            if (basketData.macros) {
                totalKcal = Math.round(basketData.macros.kcal);
                totalProt = Math.round(basketData.macros.prot);
                totalCarb = Math.round(basketData.macros.carb);
                totalFat = Math.round(basketData.macros.gras);
            }

            const prompt = `
Eres un nutricionista experto. Tu tarea es generar un MENÚ SEMANAL ESTRICTO y REALISTA (Lunes a Viernes) utilizando ÚNICAMENTE los ingredientes proporcionados.

**Restricciones Absolutas:**
1. NO inventes ingredientes. Usa SOLO los de la Cesta de la Compra.
2. Si falta algo típico (ej. aceite, sal, agua), puedes asumirlo para cocinar, pero la base del plato DEBE ser estricta de la lista.
3. El formato de salida DEBE ser un objeto JSON válido y minificado, sin texto introductorio, sin formato markdown (\`\`\`json). Solo el JSON puro.

**Cesta de la Compra:**
${ingredientsText}

**Macros Totales Diarios Objetivo (Aprox):**
${totalKcal} kcal | ${totalProt}g Proteínas | ${totalCarb}g Carbohidratos | ${totalFat}g Grasas

**Estructura del JSON esperada:**
{
  "lunes": {
    "desayuno": "Descripción breve",
    "comida": "Descripción breve",
    "merienda": "Descripción breve o null",
    "cena": "Descripción breve"
  },
  "martes": { ... },
  "miercoles": { ... },
  "jueves": { ... },
  "viernes": { ... }
}

Genera el JSON ahora:`;

            const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: 'llama-3.3-70b-versatile',
                    messages: [{ role: 'user', content: prompt }],
                    temperature: 0.3,
                    max_tokens: 3000,
                    response_format: { type: "json_object" }
                })
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error?.message || 'Error en la petición a Groq');
            }

            const data = await response.json();
            const jsonText = data.choices[0].message.content;

            try {
                const parsed = JSON.parse(jsonText);
                setMenuData(parsed);
            } catch (e) {
                console.error("JSON parse error:", jsonText);
                throw new Error("La IA no devolvió un JSON válido. Inténtalo de nuevo.");
            }

        } catch (err) {
            console.error('Groq API Error:', err);
            if (err.message && err.message.includes('API key')) {
                setError('La API Key proporcionada no es válida.');
            } else {
                setError(err.message);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const getMealIcon = (type) => {
        switch (type) {
            case 'desayuno': return <Coffee size={16} />;
            case 'comida': return <Utensils size={16} />;
            case 'merienda': return <Coffee size={16} />;
            case 'cena': return <UtensilsCrossed size={16} />;
            default: return <Utensils size={16} />;
        }
    };

    const diasOrden = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes'];

    return (
        <div className={s.menuPageContainer}>

            <div className={s.header}>
                <div className={s.titleSection}>
                    <button className={s.btnBack} onClick={() => navigate('/')}>
                        <ArrowLeft size={18} /> Volver
                    </button>
                    <h1><Sparkles size={24} className={s.iconGlow} /> Menú Semanal Inteligente</h1>
                </div>
            </div>

            {isLoading && (
                <div className={s.loadingState}>
                    <Sparkles size={64} className={s.chefGlow} />
                    <div className={s.loadingText}>
                        <h3>Diseñando tu plan nutricional...</h3>
                        <p>El Chef de IA está combinando los ingredientes exactos de tu cesta {versionLabel}</p>
                    </div>
                    <div className={s.dots}><span>.</span><span>.</span><span>.</span></div>
                </div>
            )}

            {error && !isLoading && (
                <div className={s.errorState}>
                    <AlertTriangle size={48} />
                    <h2>Algo ha fallado</h2>
                    <p>{error}</p>
                    <button className={s.btnBack} style={{ background: '#ef4444', color: 'white' }} onClick={() => {
                        hasRequested.current = false;
                        generateMenuJSON();
                    }}>
                        Reintentar Generación
                    </button>
                </div>
            )}

            {menuData && !isLoading && !error && (
                <div className={s.gridContainer}>
                    {diasOrden.map((dia) => (
                        menuData[dia] && Object.keys(menuData[dia]).length > 0 && (
                            <div key={dia} className={s.dayCard}>
                                <div className={s.dayHeader}>
                                    <h2><Calendar size={20} /> {dia}</h2>
                                </div>
                                <div className={s.mealsGrid}>
                                    {Object.entries(menuData[dia]).map(([mealType, description]) => (
                                        description && description !== 'null' && description !== '' && (
                                            <div key={mealType} className={s.mealSlot}>
                                                <div className={`${s.mealType} ${s[mealType] || ''}`}>
                                                    {getMealIcon(mealType)} {mealType}
                                                </div>
                                                <div className={s.mealContent}>
                                                    {description}
                                                </div>
                                            </div>
                                        )
                                    ))}
                                </div>
                            </div>
                        )
                    ))}
                </div>
            )}

        </div>
    );
}

export default MenuPage;
