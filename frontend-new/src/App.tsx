import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import ZoneDetails from "./pages/ZoneDetails";

export default function App() {
  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black text-white">
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
