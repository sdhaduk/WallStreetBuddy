import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Current from './pages/Current'
import StockDetail from './pages/StockDetail'
import './App.css'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="current" element={<Current />} />
          <Route path="stock/:symbol" element={<StockDetail />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
