import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import App from './App.jsx'

function Page({ title }) {
  return (
    <>
      <h1>{title}</h1>
      <p>Module wires to its API endpoint in its build task (14.6+). SYNTHETIC data only.</p>
    </>
  )
}

const TITLES = {
  '/': 'Executive overview',
  '/inventory': 'Inventory',
  '/suppliers': 'Suppliers',
  '/logistics': 'Logistics',
  '/forecasts': 'Forecasts',
  '/risks': 'Risk center',
  '/recommendations': 'Recommendations',
  '/sources': 'Data sources',
  '/etl': 'ETL monitoring',
  '/quality': 'Data quality',
  '/alerts': 'Alerts',
  '/admin': 'Administration',
}

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Routes>
      <Route element={<App />}>
        {Object.entries(TITLES).map(([path, title]) => (
          <Route key={path} path={path} element={<Page title={title} />} />
        ))}
      </Route>
    </Routes>
  </BrowserRouter>,
)
