import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiGet } from '../api';
import { Clock, ArrowRightLeft, ArrowLeft, Flame, Beef } from 'lucide-react';
import toast from 'react-hot-toast';
import s from './OrdersPage.module.css';

const MEAL_CONFIG = {
    desayuno: { label: 'Desayuno', icon: '☕' },
    comida: { label: 'Comida', icon: '🍲' },
    merienda: { label: 'Merienda', icon: '🍎' },
    cena: { label: 'Cena', icon: '🥗' }
};

export default function OrdersPage() {
    const navigate = useNavigate();
    const [orders, setOrders] = useState([]);
    const [loadingOrders, setLoadingOrders] = useState(true);
    const [expandedOrder, setExpandedOrder] = useState(null);

    useEffect(() => {
        fetchOrders();
    }, []);

    const fetchOrders = async () => {
        setLoadingOrders(true);
        try {
            const data = await apiGet('/pedidos');
            if (data.error) throw new Error(data.error);
            setOrders(data);
        } catch (e) {
            toast.error(e.message || 'Error al cargar pedidos');
        } finally {
            setLoadingOrders(false);
        }
    };

    const loadOrder = (order) => {
        // Save to session storage to pass back to Dashboard
        sessionStorage.setItem('mercadona_load_order', JSON.stringify({
            precio_total: order.precio_total,
            macros: order.macros_json || {},
            secciones: order.secciones_json || {}
        }));
        navigate('/');
    };

    return (
        <div className={s.pageWrapper}>
            <header className={s.topbar}>
                <button className={s.btnBack} onClick={() => navigate('/')}>
                    <ArrowLeft size={16} /> Volver al Optimizador
                </button>
                <span className={s.pageTitle}><Clock size={16} /> Mis Pedidos</span>
            </header>

            <main className={s.mainContent}>
                <div className={s.ordersContainer}>
                    {loadingOrders ? (
                        <div className={s.emptyState}>Cargando historial de pedidos...</div>
                    ) : orders.length === 0 ? (
                        <div className={s.emptyState}>Aún no has realizado ninguna compra simulada.</div>
                    ) : (
                        <div className={s.orderList}>
                            {orders.map((o) => (
                                <div key={o.id} className={s.orderCard}>
                                    <div className={s.orderHeader}>
                                        <div>
                                            <div className={s.orderDate}>{new Date(o.fecha).toLocaleString('es-ES')}</div>
                                            <div className={s.orderLabel}>Pedido de {o.version_label}</div>
                                        </div>
                                        <div className={s.orderTotal}>{o.precio_total.toFixed(2)}€</div>
                                    </div>

                                    <div className={s.orderMacros}>
                                        <span className={s.macroBadge}><Flame size={14} color="#f97316" /> {o.macros_json.kcal || 0} kcal</span>
                                        <span className={s.macroBadge}><Beef size={14} color="#ef4444" /> {o.macros_json.prot || 0}g prot</span>
                                    </div>

                                    <div className={s.orderActions}>
                                        <button className={s.btnSecondary} onClick={() => setExpandedOrder(expandedOrder === o.id ? null : o.id)}>
                                            {expandedOrder === o.id ? 'Ocultar Detalles' : 'Ver Detalles'}
                                        </button>
                                        <button className={s.btnAccent} onClick={() => loadOrder(o)} title="Cargar como Versión C">
                                            <ArrowRightLeft size={16} /> Cargar Cesta
                                        </button>
                                    </div>

                                    {expandedOrder === o.id && (
                                        <div className={s.orderDetails}>
                                            {Object.entries(o.secciones_json).map(([sec, items]) => (
                                                items.length > 0 && (
                                                    <div key={sec} className={s.orderSection}>
                                                        <div className={s.sectionTitle}>
                                                            {MEAL_CONFIG[sec]?.icon} {MEAL_CONFIG[sec]?.label || sec} <span>({items.length})</span>
                                                        </div>
                                                        <div className={s.orderSectionItems}>
                                                            {items.map((p, idx) => (
                                                                <div key={idx} className={s.productItem}>
                                                                    <span>{p.emoji} {p.nombre}</span>
                                                                    <span className={s.productPrice}>{p.precio.toFixed(2)}€</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
