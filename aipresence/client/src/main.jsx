import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/theme.css';
import './styles/global.css';
import App from './App';
import { ToastProvider } from './components/ToastContext';
import ToastContainer from './components/Toast';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ToastProvider>
      <App />
      <ToastContainer />
    </ToastProvider>
  </React.StrictMode>
);
