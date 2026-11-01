import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AuthProvider } from './context/AuthContext.jsx'
import scanFileLogo from './assets/ScanFile Logo.png'
import './style/global.css'
import App from './App.jsx'

const favicon = document.querySelector('link[rel="icon"]')
if (favicon) {
  favicon.href = scanFileLogo
  favicon.type = 'image/png'
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>,
)
