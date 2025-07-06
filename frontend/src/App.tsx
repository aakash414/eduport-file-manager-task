import { Routes, Route } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';
import PublicRoute from './components/PublicRoute';
import Layout from './components/layout/Layout';
import NotFound from './pages/NotFound';
import { ToastProvider } from './context/ToastContext';
import './App.css';

function App() {
    return (
        <ToastProvider>
            <Routes>
                <Route path="/login" element={<PublicRoute><AuthPage /></PublicRoute>} />
                <Route path="/register" element={<PublicRoute><AuthPage /></PublicRoute>} />
                <Route
                    path="/dashboard/*"
                    element={
                        <ProtectedRoute>
                            <Layout>
                                <Routes>
                                    <Route path="/" element={<Dashboard />} />
                                </Routes>
                            </Layout>
                        </ProtectedRoute>
                    }
                />
                <Route path="*" element={<NotFound />} />
            </Routes>
        </ToastProvider>
    );
}

export default App;
