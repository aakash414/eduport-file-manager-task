import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './index.css';
import App from './App.tsx';
import { AuthProvider } from './contexts/AuthContext';
import { FileProvider } from './contexts/FileContext';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <FileProvider>
          <App />
        </FileProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
