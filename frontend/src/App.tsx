import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import PlayerList from './pages/PlayerList'
import PlayerDetail from './pages/PlayerDetail'
import './App.css'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<PlayerList />} />
          <Route path="/players/:id" element={<PlayerDetail />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
