import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, LogOut, Sparkles, ChevronDown, X, Camera, Flame, Beef, Wheat, Droplets } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { apiPost, apiPut, apiUpload, avatarUrl } from '../api';
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

export default function DashboardPage() {
    const { user, perfiles, logout, refreshUser } = useAuth();

    // Optimizer controls
    const [presupuesto, setPresupuesto] = useState(user?.presupuesto_default || 50);
    const [proteinas, setProteinas] = useState(user?.proteinas_default || 150);
    const [calorias, setCalorias] = useState(user?.calorias_default || 2400);
    const [carbohidratos, setCarbohidratos] = useState(user?.carbohidratos_default || '');
    const [grasas, setGrasas] = useState(user?.grasas_default || '');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);

    // Profile modal
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
            {/* TOPBAR */}
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

            {/* CONTENT */}
            <div className={s.content}>
                {/* CONTROLS */}
                <motion.section
                    className={s.controlsCard}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4 }}
                >
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
                        <div className={s.optionalLabel}>
                            Macros avanzados <span className={s.optionalBadge}>Opcional</span>
                        </div>
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

                {/* LOADER */}
                {loading && (
                    <div className={s.loaderBox}>
                        Generando 3 versiones de cesta semanal
                        <span className={s.loaderDots}>
                            <span /><span /><span />
                        </span>
                    </div>
                )}

                {/* RESULTS */}
                {results && (
                    <motion.div
                        className={s.resultsGrid}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.3 }}
                    >
                        {VERSION_CONFIG.map((vc, idx) => (
                            <VersionCard
                                key={vc.key}
                                data={results[vc.key]}
                                label={vc.label}
                                headerClass={vc.headerClass}
                                delay={idx * 0.1}
                            />
                        ))}
                    </motion.div>
                )}
            </div>

            {/* PROFILE MODAL */}
            <AnimatePresence>
                {showProfile && (
                    <motion.div
                        className={s.modalOverlay}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={(e) => e.target === e.currentTarget && setShowProfile(false)}
                    >
                        <motion.div
                            className={s.profileModal}
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        >
                            <div className={s.pmHeader}>
                                <h2><Settings size={18} /> Personalizar perfil</h2>
                                <button className={s.pmClose} onClick={() => setShowProfile(false)}><X size={18} /></button>
                            </div>
                            <div className={s.pmBody}>
                                {/* Avatar */}
                                <div className={s.avatarUpload}>
                                    <div className={s.avatarPreview} onClick={() => fotoRef.current?.click()}>
                                        {foto ? <img src={foto} alt="" /> : <span>{initial}</span>}
                                    </div>
                                    <span className={s.avatarHint}>Haz clic para cambiar foto</span>
                                    <input type="file" ref={fotoRef} accept="image/*" style={{ display: 'none' }} onChange={uploadFoto} />
                                </div>

                                {/* Datos */}
                                <div className={s.pmGrid}>
                                    <div className={s.pmField}>
                                        <label>Nombre</label>
                                        <input className={s.pmInput} value={pmNombre} onChange={e => setPmNombre(e.target.value)} />
                                    </div>
                                    <div className={s.pmField}>
                                        <label>Apellidos</label>
                                        <input className={s.pmInput} value={pmApellidos} onChange={e => setPmApellidos(e.target.value)} />
                                    </div>
                                </div>

                                {/* Perfil de dieta */}
                                <div className={s.pmSectionTitle}>Perfil de dieta</div>
                                <div className={s.pmProfiles}>
                                    {Object.entries(perfiles).map(([key, p]) => (
                                        <div key={key}
                                            className={`${s.pmProfile} ${pmPerfil === key ? s.pmProfileActive : ''}`}
                                            onClick={() => {
                                                setPmPerfil(key);
                                                if (key !== 'personalizado') {
                                                    setPmProt(p.proteinas);
                                                    setPmKcal(p.calorias);
                                                    if (p.carbohidratos) setPmCarb(p.carbohidratos);
                                                }
                                            }}
                                        >
                                            <span className={s.pmProfileIcon}>{PROFILE_ICONS[key] || '📋'}</span>
                                            {p.nombre.replace(/^[^\s]+\s/, '')}
                                        </div>
                                    ))}
                                </div>

                                {/* Macros */}
                                <div className={s.pmSectionTitle}>Macros por defecto</div>
                                <div className={s.pmGrid}>
                                    <div className={s.pmField}>
                                        <label>Presupuesto (€/sem)</label>
                                        <input className={s.pmInput} type="number" value={pmPres} onChange={e => setPmPres(e.target.value)} />
                                    </div>
                                    <div className={s.pmField}>
                                        <label>Proteínas (g/día)</label>
                                        <input className={s.pmInput} type="number" value={pmProt} onChange={e => setPmProt(e.target.value)} />
                                    </div>
                                    <div className={s.pmField}>
                                        <label>Calorías (kcal/día)</label>
                                        <input className={s.pmInput} type="number" value={pmKcal} onChange={e => setPmKcal(e.target.value)} />
                                    </div>
                                    <div className={s.pmField}>
                                        <label>Carbohidratos (g/día)</label>
                                        <input className={s.pmInput} type="number" value={pmCarb} onChange={e => setPmCarb(e.target.value)} placeholder="Opcional" />
                                    </div>
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
function VersionCard({ data, label, headerClass, delay }) {
    const [openSections, setOpenSections] = useState({ desayuno: true, comida: true, merienda: true, cena: true });
    const [selectedProduct, setSelectedProduct] = useState(null);

    const toggle = (sec) => setOpenSections(prev => ({ ...prev, [sec]: !prev[sec] }));

    if (!data) return null;

    if (data.error) {
        return (
            <motion.article
                className={s.versionCard}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay, duration: 0.4 }}
            >
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
        <motion.article
            className={s.versionCard}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay, duration: 0.4 }}
        >
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
                                    <motion.div
                                        className={s.mealItems}
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.2 }}
                                    >
                                        {items.map((p, i) => (
                                            <div className={s.productRow} key={i}
                                                onClick={() => p.imagen_url && setSelectedProduct(p)}
                                                style={{ cursor: p.imagen_url ? 'pointer' : 'default' }}
                                                title={p.imagen_url ? 'Click para ver imagen' : ''}
                                            >
                                                <span className={s.pEmoji}>{p.emoji || '📦'}</span>
                                                <span className={s.pName}>{p.nombre}</span>
                                                <span className={s.pPrice}>{p.precio.toFixed(2)}€</span>
                                            </div>
                                        ))}
                                        {items.length === 0 && (
                                            <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem', padding: '4px 8px' }}>—</div>
                                        )}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    );
                })}
            </div>
            <div className={s.versionFooter}>{data.total_productos} productos</div>

            {/* PRODUCT IMAGE POPUP */}
            <AnimatePresence>
                {selectedProduct && (
                    <motion.div
                        className={s.imgOverlay}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setSelectedProduct(null)}
                    >
                        <motion.div
                            className={s.imgPopup}
                            initial={{ opacity: 0, scale: 0.8, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.8, y: 20 }}
                            onClick={(e) => e.stopPropagation()}
                        >
                            <button className={s.imgClose} onClick={() => setSelectedProduct(null)}>
                                <X size={18} />
                            </button>
                            <img
                                src={selectedProduct.imagen_url}
                                alt={selectedProduct.nombre}
                                className={s.imgProduct}
                            />
                            <div className={s.imgInfo}>
                                <span className={s.imgName}>{selectedProduct.emoji} {selectedProduct.nombre}</span>
                                <span className={s.imgPrice}>{selectedProduct.precio.toFixed(2)}€</span>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.article>
    );
}
