import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import { ApiLogProvider } from './context/ApiLogContext.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      {/* ApiLog wraps Auth: the log must exist before the first auth call fires. */}
      <ApiLogProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ApiLogProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
