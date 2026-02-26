import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiGet, apiPost } from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [perfiles, setPerfiles] = useState({});

    const loadPerfiles = useCallback(async () => {
        try {
            const data = await apiGet('/perfiles');
            setPerfiles(data);
        } catch (e) {
            console.error('Error loading perfiles:', e);
        }
    }, []);

    const loadUser = useCallback(async () => {
        const token = localStorage.getItem('token');
        if (!token) { setLoading(false); return false; }
        try {
            const data = await apiGet('/me');
            setUser(data);
            setLoading(false);
            return true;
        } catch {
            localStorage.removeItem('token');
            setUser(null);
            setLoading(false);
            return false;
        }
    }, []);

    useEffect(() => {
        loadPerfiles();
        loadUser();
    }, [loadPerfiles, loadUser]);

    const login = async (email, password) => {
        const data = await apiPost('/login', { email, password });
        localStorage.setItem('token', data.token);
        await loadUser();
    };

    const register = async (payload) => {
        const data = await apiPost('/register', payload);
        localStorage.setItem('token', data.token);
        await loadUser();
    };

    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    const refreshUser = async () => {
        await loadUser();
    };

    return (
        <AuthContext.Provider value={{
            user, loading, perfiles,
            login, register, logout, refreshUser
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be inside AuthProvider');
    return ctx;
}
