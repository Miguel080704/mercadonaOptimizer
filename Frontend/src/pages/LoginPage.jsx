import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShoppingCart } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import s from './LoginPage.module.css';

const PROFILE_ICONS = {
    estandar: '⚡', deportista: '🏋️', deficit: '🥗',
    vegano: '🌱', vegetariano: '🥚', personalizado: '🔧',
};

export default function LoginPage() {
    const { login, register, perfiles } = useAuth();
    const [mode, setMode] = useState('login');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    // Login fields
    const [loginEmail, setLoginEmail] = useState('');
    const [loginPass, setLoginPass] = useState('');

    // Register fields
    const [regNombre, setRegNombre] = useState('');
    const [regApellidos, setRegApellidos] = useState('');
    const [regEmail, setRegEmail] = useState('');
    const [regPass, setRegPass] = useState('');
    const [regPerfil, setRegPerfil] = useState('estandar');

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        if (!loginEmail || !loginPass) { setError('Rellena todos los campos'); return; }
        setLoading(true);
        try {
            await login(loginEmail, loginPass);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setError('');
        if (!regNombre || !regEmail || !regPass) { setError('Rellena los campos obligatorios'); return; }
        if (regPass.length < 6) { setError('Contraseña debe tener al menos 6 caracteres'); return; }
        setLoading(true);
        try {
            await register({
                email: regEmail,
                password: regPass,
                nombre: regNombre,
                apellidos: regApellidos || null,
                perfil_dieta: regPerfil,
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={s.authPage}>
            <motion.div
                className={s.authCard}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
            >
                <div className={s.authBrand}>
                    <h1><ShoppingCart size={22} style={{ verticalAlign: 'middle', marginRight: 6 }} />Mercadona AI</h1>
                    <p>Tu compra semanal inteligente</p>
                </div>

                <div className={s.tabs}>
                    <button
                        className={`${s.tab} ${mode === 'login' ? s.tabActive : ''}`}
                        onClick={() => { setMode('login'); setError(''); }}
                    >Iniciar sesión</button>
                    <button
                        className={`${s.tab} ${mode === 'register' ? s.tabActive : ''}`}
                        onClick={() => { setMode('register'); setError(''); }}
                    >Registrarse</button>
                </div>

                <div className={s.formBody}>
                    <AnimatePresence mode="wait">
                        {error && (
                            <motion.div
                                className={s.errorMsg}
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                exit={{ opacity: 0, height: 0 }}
                            >{error}</motion.div>
                        )}
                    </AnimatePresence>

                    {mode === 'login' ? (
                        <motion.form key="login" onSubmit={handleLogin}
                            initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.25 }}
                        >
                            <div className={s.field}>
                                <label>Email</label>
                                <input className={s.input} type="email" placeholder="tu@email.com"
                                    value={loginEmail} onChange={e => setLoginEmail(e.target.value)} />
                            </div>
                            <div className={s.field}>
                                <label>Contraseña</label>
                                <input className={s.input} type="password" placeholder="••••••••"
                                    value={loginPass} onChange={e => setLoginPass(e.target.value)} />
                            </div>
                            <button className={s.submitBtn} disabled={loading}>
                                {loading ? 'Entrando...' : 'Entrar'}
                            </button>
                        </motion.form>
                    ) : (
                        <motion.form key="register" onSubmit={handleRegister}
                            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.25 }}
                        >
                            <div className={s.fieldRow}>
                                <div className={s.field}>
                                    <label>Nombre *</label>
                                    <input className={s.input} type="text" placeholder="Miguel"
                                        value={regNombre} onChange={e => setRegNombre(e.target.value)} />
                                </div>
                                <div className={s.field}>
                                    <label>Apellidos</label>
                                    <input className={s.input} type="text" placeholder="García"
                                        value={regApellidos} onChange={e => setRegApellidos(e.target.value)} />
                                </div>
                            </div>
                            <div className={s.field}>
                                <label>Email *</label>
                                <input className={s.input} type="email" placeholder="tu@email.com"
                                    value={regEmail} onChange={e => setRegEmail(e.target.value)} />
                            </div>
                            <div className={s.field}>
                                <label>Contraseña *</label>
                                <input className={s.input} type="password" placeholder="Mínimo 6 caracteres"
                                    value={regPass} onChange={e => setRegPass(e.target.value)} />
                            </div>
                            <div className={s.field}>
                                <label>Perfil de dieta</label>
                                <div className={s.profilePicker}>
                                    {Object.entries(perfiles).map(([key, p]) => (
                                        <div key={key}
                                            className={`${s.profileOption} ${regPerfil === key ? s.profileOptionActive : ''}`}
                                            onClick={() => setRegPerfil(key)}
                                        >
                                            <span className={s.profileIcon}>{PROFILE_ICONS[key] || '📋'}</span>
                                            {p.nombre.replace(/^[^\s]+\s/, '')}
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <button className={s.submitBtn} disabled={loading}>
                                {loading ? 'Creando cuenta...' : 'Crear cuenta'}
                            </button>
                        </motion.form>
                    )}
                </div>
            </motion.div>
        </div>
    );
}
