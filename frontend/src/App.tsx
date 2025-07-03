import { Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from './Pages/auth/AuthPage';
import HomePage from './Pages/Home/page';
import ProtectedRoute from './components/ProtectedRoute';
import './App.css';

function App() {
    return (
        <div className="App">
            <header className="App-header">
                <h1>File Manager</h1>
            </header>
            <main>
                <Routes>
                    <Route path="/login" element={<AuthPage />} />
                    <Route path="/register" element={<AuthPage />} />
                    <Route path="/home" element={
                        <ProtectedRoute>
                            <HomePage />
                        </ProtectedRoute>
                    } />
                    <Route path="*" element={<Navigate to="/login" />} />
                </Routes>
            </main>
        </div>
    );
}

export default App;
