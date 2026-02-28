import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, LogOut, Sparkles, ChevronDown, X, Flame, Beef, Wheat, Droplets, Plus, Search, Trash2, ArrowRightLeft, FileDown, Copy } from 'lucide-react';
import { jsPDF } from 'jspdf';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { apiPost, apiPut, apiUpload, apiGet, avatarUrl } from '../api';
import s from './DashboardPage.module.css';

const PROFILE_ICONS = {
    estandar: '⚡', deportista: '🏋️', deficit: '🥗',
    vegano: '🌱', vegetariano: '🥚', personalizado: '🔧',
};

const MEAL_CONFIG = {
    desayuno: { icon: '🌅', label: 'Desayuno' },
    comida: { icon: '🍽️', label: 'Comida' },
    merienda: { icon: '🍪', label: 'Merienda' },
    cena: { icon: '🌙', label: 'Cena' },
};

const VERSION_CONFIG = [
    { key: 'version_a', label: 'Versión A', headerClass: 'headerA' },
    { key: 'version_b', label: 'Versión B', headerClass: 'headerB' },
    { key: 'version_c', label: 'Versión C', headerClass: 'headerC' },
];

const PASILLO_MAP = {
    carne: { name: 'Carnes', emoji: '🥩', order: 1 },
    pescado: { name: 'Pescado', emoji: '🐟', order: 2 },
    verdura: { name: 'Verduras y Frutas', emoji: '🥬', order: 3 },
    fruta: { name: 'Frutas', emoji: '🍎', order: 4 },
    lacteo: { name: 'Lácteos', emoji: '🥛', order: 5 },
    huevo: { name: 'Huevos', emoji: '🥚', order: 6 },
    cereal: { name: 'Cereales y Pan', emoji: '🍞', order: 7 },
    legumbre: { name: 'Legumbres', emoji: '🫘', order: 8 },
    conserva: { name: 'Conservas', emoji: '🥫', order: 9 },
    capricho: { name: 'Snacks y Dulces', emoji: '🍪', order: 10 },
};

function recalcMacros(secciones) {
    let prot = 0, kcal = 0, carb = 0, gras = 0, precio = 0, count = 0;
    for (const items of Object.values(secciones)) {
        for (const p of items) {
            precio += p.precio;
            prot += p.prot_pack || 0;
            kcal += p.kcal_pack || 0;
            carb += p.carb_pack || 0;
            gras += p.gras_pack || 0;
            count++;
        }
    }
    return {
        precio_total: Math.round(precio * 100) / 100,
        total_productos: count,
        macros: {
            prot: Math.round(prot * 10) / 10,
            kcal: Math.round(kcal),
            carb: Math.round(carb * 10) / 10,
            gras: Math.round(gras * 10) / 10,
        },
    };
}

export default function DashboardPage() {
    const { user, perfiles, logout, refreshUser } = useAuth();

    const [presupuesto, setPresupuesto] = useState(user?.presupuesto_default || 50);
    const [proteinas, setProteinas] = useState(user?.proteinas_default || 150);
    const [calorias, setCalorias] = useState(user?.calorias_default || 2400);
    const [carbohidratos, setCarbohidratos] = useState(user?.carbohidratos_default || '');
    const [grasas, setGrasas] = useState(user?.grasas_default || '');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);

    const [showProfile, setShowProfile] = useState(false);
    const [pmNombre, setPmNombre] = useState('');
    const [pmApellidos, setPmApellidos] = useState('');
    const [pmPerfil, setPmPerfil] = useState('estandar');
    const [pmPres, setPmPres] = useState(50);
    const [pmProt, setPmProt] = useState(150);
    const [pmKcal, setPmKcal] = useState(2400);
    const [pmCarb, setPmCarb] = useState('');
    const fotoRef = useRef(null);

    const calcular = async () => {
        setLoading(true);
        setResults(null);
        const perfil = perfiles[user?.perfil_dieta || 'estandar'];
        const excluir = perfil?.excluir_tipos?.length ? perfil.excluir_tipos : null;
        try {
            const data = await apiPost('/optimizar', {
                presupuesto: parseFloat(presupuesto),
                proteinas: parseFloat(proteinas),
                calorias: parseFloat(calorias),
                carbohidratos: parseFloat(carbohidratos) || null,
                grasas: parseFloat(grasas) || null,
                excluir_tipos: excluir,
            });
            if (data.error) throw new Error(data.error);
            setResults(data);
            toast.success('¡Compra generada!');
        } catch (e) {
            toast.error(e.message);
        } finally {
            setLoading(false);
        }
    };

    const updateVersion = (versionKey, newSecciones) => {
        setResults(prev => {
            if (!prev) return prev;
            const calc = recalcMacros(newSecciones);
            return {
                ...prev,
                [versionKey]: {
                    ...prev[versionKey],
                    secciones: newSecciones,
                    ...calc,
                },
            };
        });
    };

    const openProfile = () => {
        setPmNombre(user?.nombre || '');
        setPmApellidos(user?.apellidos || '');
        setPmPerfil(user?.perfil_dieta || 'estandar');
        setPmPres(user?.presupuesto_default || 50);
        setPmProt(user?.proteinas_default || 150);
        setPmKcal(user?.calorias_default || 2400);
        setPmCarb(user?.carbohidratos_default || '');
        setShowProfile(true);
    };

    const saveProfile = async () => {
        try {
            await apiPut('/perfil', {
                nombre: pmNombre || null,
                apellidos: pmApellidos || null,
                perfil_dieta: pmPerfil,
                presupuesto_default: parseFloat(pmPres) || null,
                proteinas_default: parseFloat(pmProt) || null,
                calorias_default: parseFloat(pmKcal) || null,
                carbohidratos_default: parseFloat(pmCarb) || null,
            });
            await refreshUser();
            setPresupuesto(pmPres);
            setProteinas(pmProt);
            setCalorias(pmKcal);
            if (pmCarb) setCarbohidratos(pmCarb);
            toast.success('Perfil guardado');
            setShowProfile(false);
        } catch (e) {
            toast.error(e.message);
        }
    };

    const uploadFoto = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        try {
            await apiUpload('/upload-foto', file);
            await refreshUser();
            toast.success('Foto actualizada');
        } catch (err) {
            toast.error(err.message);
        }
    };

    const initial = (user?.nombre || '?')[0].toUpperCase();
    const foto = avatarUrl(user?.foto_url);

    return (
        <div className={s.dashboard}>
            <header className={s.topbar}>
                <span className={s.topbarTitle}>Mercadona AI Optimizer</span>
                <div className={s.topbarActions}>
                    <button className={s.userPill} onClick={openProfile}>
                        <div className={s.avatar}>
                            {foto ? <img src={foto} alt="" /> : initial}
                        </div>
                        <span className={s.userName}>{user?.nombre || 'Usuario'}</span>
                    </button>
                    <button className={s.btnIcon} onClick={openProfile}>
                        <Settings size={14} /> Perfil
                    </button>
                    <button className={`${s.btnIcon} ${s.btnDanger}`} onClick={logout}>
                        <LogOut size={14} /> Salir
                    </button>
                </div>
            </header>

            <div className={s.content}>
                <motion.section className={s.controlsCard}
                    initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
                    <div className={s.controlsGrid}>
                        <div className={s.inputGroup}>
                            <label><Flame size={14} /> Presupuesto <span style={{ opacity: 0.5 }}>(€/sem)</span></label>
                            <input type="number" value={presupuesto} onChange={e => setPresupuesto(e.target.value)} min="15" />
                        </div>
                        <div className={s.inputGroup}>
                            <label><Beef size={14} /> Proteínas <span style={{ opacity: 0.5 }}>(g/día)</span></label>
                            <input type="number" value={proteinas} onChange={e => setProteinas(e.target.value)} />
                        </div>
                        <div className={s.inputGroup}>
                            <label><Flame size={14} /> Calorías <span style={{ opacity: 0.5 }}>(kcal/día)</span></label>
                            <input type="number" value={calorias} onChange={e => setCalorias(e.target.value)} />
                        </div>
                    </div>
                    <div className={s.optionalSection}>
                        <div className={s.optionalLabel}>Macros avanzados <span className={s.optionalBadge}>Opcional</span></div>
                        <div className={s.optionalGrid}>
                            <div className={s.inputGroup}>
                                <label><Wheat size={14} /> Carbohidratos <span style={{ opacity: 0.5 }}>(g/día)</span></label>
                                <input type="number" value={carbohidratos} onChange={e => setCarbohidratos(e.target.value)} placeholder="Ej: 300" />
                            </div>
                            <div className={s.inputGroup}>
                                <label><Droplets size={14} /> Grasas <span style={{ opacity: 0.5 }}>(g/día)</span></label>
                                <input type="number" value={grasas} onChange={e => setGrasas(e.target.value)} placeholder="Ej: 80" />
                            </div>
                        </div>
                    </div>
                    <div className={s.btnRow}>
                        <button className={s.btnGenerate} onClick={calcular} disabled={loading}>
                            {loading ? 'Calculando...' : <>Generar Compra Semanal <Sparkles size={16} /></>}
                        </button>
                    </div>
                </motion.section>

                {loading && (
                    <div className={s.loaderBox}>
                        Generando 3 versiones de cesta semanal
                        <span className={s.loaderDots}><span /><span /><span /></span>
                    </div>
                )}

                {results && (
                    <motion.div className={s.resultsGrid} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
                        {VERSION_CONFIG.map((vc, idx) => (
                            <VersionCard
                                key={vc.key}
                                versionKey={vc.key}
                                data={results[vc.key]}
                                label={vc.label}
                                headerClass={vc.headerClass}
                                delay={idx * 0.1}
                                onUpdate={(newSecs) => updateVersion(vc.key, newSecs)}
                                allResults={results}
                                allVersions={VERSION_CONFIG}
                            />
                        ))}
                    </motion.div>
                )}
            </div>

            {/* PROFILE MODAL */}
            <AnimatePresence>
                {showProfile && (
                    <motion.div className={s.modalOverlay}
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        onClick={(e) => e.target === e.currentTarget && setShowProfile(false)}>
                        <motion.div className={s.profileModal}
                            initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}>
                            <div className={s.pmHeader}>
                                <h2><Settings size={18} /> Personalizar perfil</h2>
                                <button className={s.pmClose} onClick={() => setShowProfile(false)}><X size={18} /></button>
                            </div>
                            <div className={s.pmBody}>
                                <div className={s.avatarUpload}>
                                    <div className={s.avatarPreview} onClick={() => fotoRef.current?.click()}>
                                        {foto ? <img src={foto} alt="" /> : <span>{initial}</span>}
                                    </div>
                                    <span className={s.avatarHint}>Haz clic para cambiar foto</span>
                                    <input type="file" ref={fotoRef} accept="image/*" style={{ display: 'none' }} onChange={uploadFoto} />
                                </div>
                                <div className={s.pmGrid}>
                                    <div className={s.pmField}><label>Nombre</label><input className={s.pmInput} value={pmNombre} onChange={e => setPmNombre(e.target.value)} /></div>
                                    <div className={s.pmField}><label>Apellidos</label><input className={s.pmInput} value={pmApellidos} onChange={e => setPmApellidos(e.target.value)} /></div>
                                </div>
                                <div className={s.pmSectionTitle}>Perfil de dieta</div>
                                <div className={s.pmProfiles}>
                                    {Object.entries(perfiles).map(([key, p]) => (
                                        <div key={key} className={`${s.pmProfile} ${pmPerfil === key ? s.pmProfileActive : ''}`}
                                            onClick={() => { setPmPerfil(key); if (key !== 'personalizado') { setPmProt(p.proteinas); setPmKcal(p.calorias); if (p.carbohidratos) setPmCarb(p.carbohidratos); } }}>
                                            <span className={s.pmProfileIcon}>{PROFILE_ICONS[key] || '📋'}</span>
                                            {p.nombre.replace(/^[^\s]+\s/, '')}
                                        </div>
                                    ))}
                                </div>
                                <div className={s.pmSectionTitle}>Macros por defecto</div>
                                <div className={s.pmGrid}>
                                    <div className={s.pmField}><label>Presupuesto (€/sem)</label><input className={s.pmInput} type="number" value={pmPres} onChange={e => setPmPres(e.target.value)} /></div>
                                    <div className={s.pmField}><label>Proteínas (g/día)</label><input className={s.pmInput} type="number" value={pmProt} onChange={e => setPmProt(e.target.value)} /></div>
                                    <div className={s.pmField}><label>Calorías (kcal/día)</label><input className={s.pmInput} type="number" value={pmKcal} onChange={e => setPmKcal(e.target.value)} /></div>
                                    <div className={s.pmField}><label>Carbohidratos (g/día)</label><input className={s.pmInput} type="number" value={pmCarb} onChange={e => setPmCarb(e.target.value)} placeholder="Opcional" /></div>
                                </div>
                                <button className={s.pmSave} onClick={saveProfile}>Guardar cambios</button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

/* === VERSION CARD COMPONENT === */
function VersionCard({ versionKey, data, label, headerClass, delay, onUpdate, allResults, allVersions }) {
    const [openSections, setOpenSections] = useState({ desayuno: true, comida: true, merienda: true, cena: true });
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [showSearch, setShowSearch] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [searchLoading, setSearchLoading] = useState(false);
    const [pendingDelete, setPendingDelete] = useState(null); // { section, index, product }
    const searchRef = useRef(null);

    const toggle = (sec) => setOpenSections(prev => ({ ...prev, [sec]: !prev[sec] }));

    useEffect(() => {
        if (!searchQuery || searchQuery.length < 2) { setSearchResults([]); return; }
        setSearchLoading(true);
        const timer = setTimeout(async () => {
            try {
                const res = await apiGet(`/buscar-productos?q=${encodeURIComponent(searchQuery)}`);
                setSearchResults(res);
            } catch { setSearchResults([]); }
            setSearchLoading(false);
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    useEffect(() => {
        if (showSearch && searchRef.current) searchRef.current.focus();
    }, [showSearch]);

    const confirmDelete = () => {
        if (!pendingDelete) return;
        const { section, index } = pendingDelete;
        const newSecs = { ...data.secciones };
        newSecs[section] = [...newSecs[section]];
        newSecs[section].splice(index, 1);
        onUpdate(newSecs);
        setPendingDelete(null);
        toast('Producto eliminado', { icon: '🗑️' });
    };

    const swapProduct = (newProduct) => {
        if (!pendingDelete) return;
        const { section, index } = pendingDelete;
        const newSecs = { ...data.secciones };
        newSecs[section] = [...newSecs[section]];
        newSecs[section][index] = newProduct;
        onUpdate(newSecs);
        setPendingDelete(null);
        toast.success(`Cambiado por ${newProduct.emoji} ${newProduct.nombre}`);
    };

    // Get products from other versions in the same section
    const getSwapOptions = () => {
        if (!pendingDelete || !allResults || !allVersions) return [];
        const sec = pendingDelete.section;
        const currentNames = new Set((data.secciones[sec] || []).map(p => p.nombre));
        const options = [];
        for (const vc of allVersions) {
            if (vc.key === versionKey) continue;
            const vData = allResults[vc.key];
            if (!vData || vData.error) continue;
            const items = (vData.secciones[sec] || []).filter(p => !currentNames.has(p.nombre));
            if (items.length > 0) options.push({ label: vc.label, items });
        }
        return options;
    };

    // Group all products across all sections by aisle (tipo)
    const groupByAisle = (secciones) => {
        const allProducts = [];
        for (const items of Object.values(secciones)) {
            for (const p of items) allProducts.push(p);
        }
        const groups = {};
        for (const p of allProducts) {
            const tipo = p.tipo || 'otros';
            if (!groups[tipo]) groups[tipo] = [];
            groups[tipo].push(p);
        }
        return Object.entries(groups)
            .map(([tipo, items]) => ({
                tipo,
                ...(PASILLO_MAP[tipo] || { name: tipo, emoji: '📦', order: 99 }),
                items,
            }))
            .sort((a, b) => a.order - b.order);
    };

    const copyList = (vData, vLabel) => {
        const aisles = groupByAisle(vData.secciones);
        let text = `🛒 LISTA DE LA COMPRA — ${vLabel} (${vData.precio_total}€)\n\n`;
        for (const a of aisles) {
            text += `${a.emoji} ${a.name.toUpperCase()}\n`;
            for (const p of a.items) {
                text += `  □ ${p.nombre} — ${p.precio.toFixed(2)}€\n`;
            }
            text += '\n';
        }
        const m = vData.macros;
        text += `───────────────────\n`;
        text += `Total: ${vData.precio_total}€ | ${vData.total_productos} productos\n`;
        text += `🔥 ${m.kcal}kcal · 💪 ${m.prot}g prot · 🍞 ${m.carb}g carb · 🧈 ${m.gras}g gras\n`;
        navigator.clipboard.writeText(text);
        toast.success('Lista copiada al portapapeles');
    };

    const exportPDF = (vData, vLabel) => {
        const doc = new jsPDF({ unit: 'mm', format: 'a4' });
        const W = doc.internal.pageSize.getWidth();
        const margin = 16;
        let y = 20;

        // Header
        doc.setFillColor(16, 185, 129);
        doc.rect(0, 0, W, 36, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(18);
        doc.setFont('helvetica', 'bold');
        doc.text('Mercadona AI Optimizer', margin, 16);
        doc.setFontSize(11);
        doc.setFont('helvetica', 'normal');
        doc.text(`${vLabel} — ${vData.precio_total}\u20AC | ${vData.total_productos} productos`, margin, 26);
        const m = vData.macros;
        doc.setFontSize(9);
        doc.text(`${m.kcal} kcal/sem | ${m.prot}g prot | ${m.carb}g carb | ${m.gras}g gras`, margin, 32);
        y = 44;

        // Group by aisle
        const aisles = groupByAisle(vData.secciones);

        for (const aisle of aisles) {
            // Check if we need a new page
            if (y + 14 + aisle.items.length * 7 > 280) {
                doc.addPage();
                y = 16;
            }

            // Aisle header
            doc.setFillColor(31, 41, 55);
            doc.rect(margin - 2, y - 4, W - 2 * margin + 4, 8, 'F');
            doc.setTextColor(16, 185, 129);
            doc.setFontSize(10);
            doc.setFont('helvetica', 'bold');
            doc.text(`${aisle.name.toUpperCase()}`, margin + 2, y + 1);
            const aisleTotal = aisle.items.reduce((s, p) => s + p.precio, 0);
            doc.setTextColor(200, 200, 200);
            doc.setFontSize(8);
            doc.text(`${aisleTotal.toFixed(2)}\u20AC`, W - margin - 2, y + 1, { align: 'right' });
            y += 10;

            // Products
            doc.setTextColor(60, 60, 60);
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(9);
            for (const p of aisle.items) {
                doc.setFillColor(y % 2 === 0 ? 248 : 243, y % 2 === 0 ? 249 : 244, y % 2 === 0 ? 250 : 246);
                doc.rect(margin - 2, y - 3.5, W - 2 * margin + 4, 6.5, 'F');
                doc.setTextColor(50, 50, 50);
                doc.text(`\u25A1  ${p.nombre}`, margin + 2, y + 0.5);
                doc.setTextColor(16, 185, 129);
                doc.setFont('helvetica', 'bold');
                doc.text(`${p.precio.toFixed(2)}\u20AC`, W - margin - 2, y + 0.5, { align: 'right' });
                doc.setFont('helvetica', 'normal');
                y += 6.5;

                if (y > 278) { doc.addPage(); y = 16; }
            }
            y += 4;
        }

        // Footer
        if (y > 260) { doc.addPage(); y = 16; }
        doc.setDrawColor(16, 185, 129);
        doc.setLineWidth(0.5);
        doc.line(margin, y, W - margin, y);
        y += 6;
        doc.setTextColor(40, 40, 40);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text(`TOTAL: ${vData.precio_total}\u20AC`, margin, y);
        doc.setFontSize(8);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(120, 120, 120);
        doc.text(`Generado por Mercadona AI Optimizer — ${new Date().toLocaleDateString('es-ES')}`, margin, y + 6);

        doc.save(`lista-compra-${vLabel.replace(/\s/g, '-').toLowerCase()}.pdf`);
        toast.success('PDF descargado');
    };

    const addProduct = (product) => {
        const section = showSearch;
        const newSecs = { ...data.secciones };
        newSecs[section] = [...newSecs[section], product];
        onUpdate(newSecs);
        setShowSearch(null);
        setSearchQuery('');
        setSearchResults([]);
        toast.success(`${product.emoji} ${product.nombre} añadido`);
    };

    if (!data) return null;

    if (data.error) {
        return (
            <motion.article className={s.versionCard}
                initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.4 }}>
                <div className={`${s.versionHeader} ${s[headerClass]}`}>
                    <div className={s.versionHeaderContent}>
                        <div className={s.versionLabel}>{label}</div>
                        <div className={s.versionPrice}>—</div>
                    </div>
                </div>
                <div className={s.errorCard}>⚠️ {data.error}</div>
            </motion.article>
        );
    }

    const m = data.macros;
    return (
        <motion.article className={s.versionCard}
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.4 }}>
            <div className={`${s.versionHeader} ${s[headerClass]}`}>
                <div className={s.versionHeaderContent}>
                    <div className={s.versionLabel}>{label}</div>
                    <div className={s.versionPrice}>{data.precio_total}€</div>
                    <div className={s.versionMeta}>
                        <span className={s.badge}>🔥 {m.kcal} kcal</span>
                        <span className={s.badge}>💪 {m.prot}g</span>
                        <span className={s.badge}>🍞 {m.carb}g</span>
                        <span className={s.badge}>🧈 {m.gras}g</span>
                    </div>
                </div>
            </div>
            <div className={s.versionBody}>
                {Object.entries(MEAL_CONFIG).map(([sec, mcfg]) => {
                    const items = data.secciones[sec] || [];
                    const isOpen = openSections[sec];
                    return (
                        <div className={s.mealSection} key={sec}>
                            <div className={s.mealHeader} onClick={() => toggle(sec)}>
                                <span className={s.mealIcon}>{mcfg.icon}</span>
                                <span className={`${s.mealName} ${s[sec]}`}>{mcfg.label}</span>
                                <span className={s.mealCount}>{items.length}</span>
                                <ChevronDown size={14} className={`${s.mealChevron} ${isOpen ? s.mealChevronOpen : ''}`} />
                            </div>
                            <AnimatePresence>
                                {isOpen && (
                                    <motion.div className={s.mealItems}
                                        initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }}>
                                        {items.map((p, i) => (
                                            <div className={s.productRow} key={i}>
                                                <span className={s.pEmoji}
                                                    onClick={() => p.imagen_url && setSelectedProduct(p)}
                                                    style={{ cursor: p.imagen_url ? 'pointer' : 'default' }}
                                                    title={p.imagen_url ? 'Ver imagen' : ''}
                                                >{p.emoji || '📦'}</span>
                                                <span className={s.pName}
                                                    onClick={() => p.imagen_url && setSelectedProduct(p)}
                                                    style={{ cursor: p.imagen_url ? 'pointer' : 'default' }}
                                                >{p.nombre}</span>
                                                <span className={s.pPrice}>{p.precio.toFixed(2)}€</span>
                                                <button className={s.pDelete} onClick={() => setPendingDelete({ section: sec, index: i, product: p })} title="Eliminar / Cambiar">
                                                    <Trash2 size={12} />
                                                </button>
                                            </div>
                                        ))}
                                        {items.length === 0 && (
                                            <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem', padding: '4px 8px' }}>—</div>
                                        )}
                                        <button className={s.addBtn} onClick={() => { setShowSearch(sec); setSearchQuery(''); setSearchResults([]); }}>
                                            <Plus size={12} /> Añadir producto
                                        </button>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    );
                })}
            </div>
            <div className={s.versionFooter}>
                <span>{data.total_productos} productos · {data.precio_total}€</span>
                <div className={s.footerActions}>
                    <button className={s.footerBtn} onClick={() => copyList(data, label)} title="Copiar lista">
                        <Copy size={13} /> Copiar
                    </button>
                    <button className={`${s.footerBtn} ${s.footerBtnPrimary}`} onClick={() => exportPDF(data, label)} title="Descargar PDF">
                        <FileDown size={13} /> PDF
                    </button>
                </div>
            </div>

            {/* PRODUCT IMAGE POPUP */}
            <AnimatePresence>
                {selectedProduct && (
                    <motion.div className={s.imgOverlay}
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        onClick={() => setSelectedProduct(null)}>
                        <motion.div className={s.imgPopup}
                            initial={{ opacity: 0, scale: 0.8, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.8, y: 20 }}
                            onClick={(e) => e.stopPropagation()}>
                            <button className={s.imgClose} onClick={() => setSelectedProduct(null)}><X size={18} /></button>
                            <img src={selectedProduct.imagen_url} alt={selectedProduct.nombre} className={s.imgProduct} />
                            <div className={s.imgInfo}>
                                <span className={s.imgName}>{selectedProduct.emoji} {selectedProduct.nombre}</span>
                                <span className={s.imgPrice}>{selectedProduct.precio.toFixed(2)}€</span>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* SEARCH PRODUCT MODAL */}
            <AnimatePresence>
                {showSearch && (
                    <motion.div className={s.imgOverlay}
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        onClick={() => setShowSearch(null)}>
                        <motion.div className={s.searchModal}
                            initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            onClick={(e) => e.stopPropagation()}>
                            <div className={s.searchHeader}>
                                <h3><Plus size={16} /> Añadir a {MEAL_CONFIG[showSearch]?.label}</h3>
                                <button className={s.pmClose} onClick={() => setShowSearch(null)}><X size={18} /></button>
                            </div>
                            <div className={s.searchInputWrap}>
                                <Search size={16} className={s.searchIcon} />
                                <input
                                    ref={searchRef}
                                    className={s.searchInput}
                                    type="text"
                                    placeholder="Buscar producto... (ej: pollo, leche, pasta)"
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                />
                            </div>
                            <div className={s.searchResults}>
                                {searchLoading && <div className={s.searchHint}>Buscando...</div>}
                                {!searchLoading && searchQuery.length >= 2 && searchResults.length === 0 && (
                                    <div className={s.searchHint}>No se encontraron productos</div>
                                )}
                                {!searchLoading && searchQuery.length < 2 && (
                                    <div className={s.searchHint}>Escribe al menos 2 letras para buscar</div>
                                )}
                                {searchResults.map((p, i) => (
                                    <div className={s.searchRow} key={i} onClick={() => addProduct(p)}>
                                        <span className={s.pEmoji}>{p.emoji || '📦'}</span>
                                        <div className={s.searchInfo}>
                                            <span className={s.searchName}>{p.nombre}</span>
                                            <span className={s.searchMacros}>
                                                {p.kcal_pack}kcal · {p.prot_pack}g prot · {p.carb_pack}g carb
                                            </span>
                                        </div>
                                        <span className={s.searchPrice}>{p.precio.toFixed(2)}€</span>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* SWAP / DELETE MODAL */}
            <AnimatePresence>
                {pendingDelete && (
                    <motion.div className={s.imgOverlay}
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        onClick={() => setPendingDelete(null)}>
                        <motion.div className={s.swapModal}
                            initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            onClick={(e) => e.stopPropagation()}>
                            <div className={s.searchHeader}>
                                <h3><ArrowRightLeft size={16} /> {pendingDelete.product.emoji} {pendingDelete.product.nombre}</h3>
                                <button className={s.pmClose} onClick={() => setPendingDelete(null)}><X size={18} /></button>
                            </div>
                            <div className={s.swapBody}>
                                <div className={s.swapQuestion}>¿Qué quieres hacer con este producto?</div>

                                {/* Swap options from other versions */}
                                {getSwapOptions().map((group, gi) => (
                                    <div key={gi} className={s.swapGroup}>
                                        <div className={s.swapGroupLabel}>
                                            <ArrowRightLeft size={12} /> Cambiar por producto de {group.label}
                                        </div>
                                        {group.items.map((p, pi) => (
                                            <div className={s.searchRow} key={pi} onClick={() => swapProduct(p)}>
                                                <span className={s.pEmoji}>{p.emoji || '📦'}</span>
                                                <div className={s.searchInfo}>
                                                    <span className={s.searchName}>{p.nombre}</span>
                                                    <span className={s.searchMacros}>
                                                        {p.kcal_pack}kcal · {p.prot_pack}g prot
                                                    </span>
                                                </div>
                                                <span className={s.searchPrice}>{p.precio.toFixed(2)}€</span>
                                            </div>
                                        ))}
                                    </div>
                                ))}

                                {getSwapOptions().length === 0 && (
                                    <div className={s.searchHint}>No hay productos alternativos en otras versiones</div>
                                )}

                                <button className={s.swapDeleteBtn} onClick={confirmDelete}>
                                    <Trash2 size={14} /> Eliminar definitivamente
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.article>
    );
}
