import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from './Pages/auth/AuthPage';
import Dashboard from './pages/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';
import api from './services/api';
import './App.css';

function App() {
    useEffect(() => {
        const getCsrfToken = async () => {
            try {
                await api.get('/users/csrf/');
            } catch (error) {
                console.error('Failed to fetch CSRF token:', error);
            }
        };
        getCsrfToken();
    }, []);

    return (
        <div className="App">
            <header className="App-header">
                <h1>File Manager</h1>
            </header>
            <main>
                <Routes>
                    <Route path="/login" element={<AuthPage />} />
                    <Route path="/register" element={<AuthPage />} />
                    <Route path="/dashboard" element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    } />
                    <Route path="*" element={<Navigate to="/login" />} />
                </Routes>
            </main>
        </div>
    );
}

export default App;
