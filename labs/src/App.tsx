
import Footer from './components/Footer';
import LabsPage from './components/LabsPage';
import UseCasePage from './components/UseCasePage';
import AboutUsPage from './components/AboutUsPage';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

function App() {
  return(
    <Router>
      <>
        <Routes>
          <Route path="/" element={<LabsPage />} />
          <Route path="/use-cases" element={<UseCasePage />} />
          <Route path="/about" element={<AboutUsPage />} />
        </Routes>
        <Footer />
      </>
    </Router>
  );
}

export default App
