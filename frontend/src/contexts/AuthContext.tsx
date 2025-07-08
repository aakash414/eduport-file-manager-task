import React, { createContext, useState, useContext, useEffect, useCallback, type ReactNode } from 'react';
import apiClient from '../api/axios';

interface User {
    username: string;
    email: string;
}

interface AuthContextType {
    user: User | null;
    login: (userData: User) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const checkUserLoggedIn = useCallback(async () => {
        setIsLoading(true);
        try {
            const { data } = await apiClient.get('/users/user/');
            setUser(data);
        } catch (error) {
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        checkUserLoggedIn();
    }, [checkUserLoggedIn]);

    const login = (userData: User) => {
        return new Promise<void>((resolve) => {
            setUser(userData);
            resolve();
        });
    };

    const logout = async () => {
        try {
            await apiClient.post('/users/logout/');
            setUser(null);
        } catch (error) {
            console.error('Logout failed', error);
        }
    };

    const value = { user, login, logout, isAuthenticated: !!user, isLoading };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};