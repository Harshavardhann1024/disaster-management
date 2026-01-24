import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import ZoneDetails from "./pages/ZoneDetails";

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black text-white">
      <Navbar />
      <main className="px-6 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/zone/:id" element={<ZoneDetails />} />
        </Routes>
      </main>
    </div>
  );
}
