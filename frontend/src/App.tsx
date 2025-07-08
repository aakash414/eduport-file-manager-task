import { Routes, Route } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';
import PublicRoute from './components/PublicRoute';
import Layout from './components/layout/Layout';
import { ToastProvider } from './context/ToastContext';
import './App.css';
import NotFound from './pages/NotFound';

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
