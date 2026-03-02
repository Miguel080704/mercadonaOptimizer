import React from 'react';
import { motion } from 'framer-motion';
import { ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { X, Flame, Beef, Wheat, Droplets } from 'lucide-react';
import s from './NutritionalDashboard.module.css';

// Colores de la paleta para los gráficos
const COLORS = {
    prot: '#ef4444', // Rojo
    carb: '#eab308', // Amarillo
    gras: '#eab308', // Usando un tono más naranja o turquesa para variar
    kcal: '#f97316', // Naranja
    bar: '#4ade80'   // Verde principal
};

export default function NutritionalDashboard({ versionLabel, data, onClose }) {
    if (!data) return null;

    // 1. Datos para Donut de Macros (% de Calorías)
    // 1g Prot = 4 kcal, 1g Carb = 4 kcal, 1g Grasa = 9 kcal
    const macros = data.macros;
    const protKcal = macros.prot * 4;
    const carbKcal = macros.carb * 4;
    const grasKcal = macros.gras * 9;

    // Si hubiese decimales los redondeamos para el chart
    const pieData = [
        { name: 'Proteínas', value: Math.round(protKcal), color: '#ef4444' }, // Rojo
        { name: 'Carbohidratos', value: Math.round(carbKcal), color: '#3b82f6' }, // Azul
        { name: 'Grasas', value: Math.round(grasKcal), color: '#eab308' } // Amarillo
    ].filter(i => i.value > 0);

    // 2. Datos para Barras de Comidas (Distribución Calórica)
    const mealData = Object.entries(data.secciones).map(([mealName, items]) => {
        const kcal = items.reduce((sum, item) => sum + (item.kcal_pack || 0), 0);
        return {
            name: mealName.charAt(0).toUpperCase() + mealName.slice(1),
            Calorias: Math.round(kcal)
        };
    }).filter(m => m.Calorias > 0);

    // 3. Datos de Gasto por Tipo de Producto (Radar/Barras horizontales)
    // Agrupamos el gasto total por tipo/pasillo
    const aisleGasto = {};
    Object.values(data.secciones).forEach(items => {
        items.forEach(item => {
            const t = item.tipo || 'otros';
            if (!aisleGasto[t]) aisleGasto[t] = 0;
            aisleGasto[t] += item.precio;
        });
    });

    const gastoData = Object.entries(aisleGasto)
        .map(([tipo, precio]) => ({
            name: tipo.toUpperCase(),
            Gasto: Number(precio.toFixed(2))
        }))
        .sort((a, b) => b.Gasto - a.Gasto);

    return (
        <motion.div className={s.overlay}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}>

            <motion.div className={s.modal}
                initial={{ scale: 0.95, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.95, opacity: 0, y: 20 }}
                onClick={e => e.stopPropagation()}>

                <header className={s.header}>
                    <div>
                        <h2 className={s.title}>📊 Análisis Nutricional</h2>
                        <p className={s.subtitle}>Estadísticas detalladas de la {versionLabel}</p>
                    </div>
                    <button className={s.closeBtn} onClick={onClose}><X size={20} /></button>
                </header>

                <div className={s.grid}>
                    {/* Caja 1: Donut de Macros */}
                    <div className={s.card}>
                        <h3 className={s.cardTitle}>Fuente de Calorías</h3>
                        <div className={s.chartWrap}>
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value">
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff', borderRadius: '8px' }}
                                        itemStyle={{ color: '#fff' }}
                                        formatter={(value) => `${value} kcal`}
                                    />
                                    <Legend verticalAlign="bottom" height={36} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Caja 2: Barras de Comidas */}
                    <div className={s.card}>
                        <h3 className={s.cardTitle}>Reparto Calórico</h3>
                        <div className={s.chartWrap}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={mealData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                    <XAxis dataKey="name" stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff', borderRadius: '8px' }}
                                        itemStyle={{ color: '#4ade80' }}
                                        cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                    />
                                    <Bar dataKey="Calorias" fill="#f97316" radius={[4, 4, 0, 0]} barSize={40} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Caja 3: Gasto por Pasillo */}
                    <div className={`${s.card} ${s.fullWidth}`}>
                        <h3 className={s.cardTitle}>Distribución del Gasto (€)</h3>
                        <div className={s.chartWrapLarge}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart layout="vertical" data={gastoData} margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
                                    <XAxis type="number" stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} hide />
                                    <YAxis type="category" dataKey="name" stroke="#9ca3af" fontSize={11} tickLine={false} axisLine={false} width={80} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#fff', borderRadius: '8px' }}
                                        itemStyle={{ color: '#4ade80' }}
                                        cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                        formatter={(value) => `${value} €`}
                                    />
                                    <Bar dataKey="Gasto" fill="#4ade80" radius={[0, 4, 4, 0]} barSize={20} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                </div>
            </motion.div>
        </motion.div>
    );
}
