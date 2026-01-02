// src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { ThemeProvider } from './theme/ThemeProvider'
import { AppRoutes } from './routes/AppRoutes'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider defaultMode="dark">
      <AppRoutes />
    </ThemeProvider>
  </StrictMode>,
)