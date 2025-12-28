import React, { useEffect, useState } from 'react';
import axios from 'axios';

interface Zone {
  id: number;
  name: string;
  risk_level: string;
  detected_people: number;
  available_beds: number;
  allocated_volunteers?: number;
}

function App() {
  const [data, setData] = useState<{ total_people: number; available_beds: number; critical_zones: number; zones: Zone[] } | null>(null);
  const [selectedZone, setSelectedZone] = useState<Zone | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get('http://localhost:8000/dashboard');
        setData(res.data);
      } catch (e) {
        console.error('Fetch error:', e);
      }
    };
    fetchData();
    const intervalId = setInterval(fetchData, 5000);  // Every 5 seconds
    return () => clearInterval(intervalId);
  }, []);

  const openZone = (zone: Zone) => {
    setSelectedZone(zone);
  };

  const getRiskStyle = (level: string) => {
    switch (level) {
      case 'Severe':
        return { bg: 'rgb(20, 0, 0)', border: 'rgb(220, 38, 38)', badgeBg: 'rgb(220, 38, 38)', text: 'rgb(248, 113, 113)' };
      case 'Elevated':
        return { bg: 'rgb(20, 10, 0)', border: 'rgb(249, 115, 22)', badgeBg: 'rgb(249, 115, 22)', text: 'rgb(251, 146, 60)' };
      case 'Caution':
        return { bg: 'rgb(20, 20, 0)', border: 'rgb(250, 204, 21)', badgeBg: 'rgb(250, 204, 21)', text: 'rgb(253, 224, 71)' };
      default:
        return { bg: 'rgb(0, 20, 0)', border: 'rgb(16, 185, 129)', badgeBg: 'rgb(16, 185, 129)', text: 'rgb(52, 211, 153)' };
    }
  };

  if (!data) {
    return (
      <div style={{ height: '100vh', background: '#000', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem', fontWeight: 'bold' }}>
        EcoRescue Loading...
      </div>
    );
  }

  if (selectedZone) {
    return (
      <div style={{ background: '#000', minHeight: '100vh', color: '#fff', padding: '2rem' }}>
        <button
          onClick={() => setSelectedZone(null)}
          style={{ marginBottom: '2rem', padding: '0.5rem 1rem', background: '#1a1a1a', color: '#fff', border: '1px solid #333', borderRadius: '0.5rem', cursor: 'pointer' }}
        >
          ← Back to Dashboard
        </button>
        <h1 style={{ fontSize: '3rem', marginBottom: '1rem' }}>{selectedZone.name}</h1>
        <div style={{ padding: '1rem', background: getRiskStyle(selectedZone.risk_level).bg, border: `2px solid ${getRiskStyle(selectedZone.risk_level).border}`, borderRadius: '0.5rem', marginBottom: '2rem' }}>
          Risk Level: {selectedZone.risk_level} | Detected: {selectedZone.detected_people} | Available Beds: {selectedZone.available_beds} | Allocated Volunteers: {selectedZone.allocated_volunteers || 0}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
          {/* Shelters Table */}
          <div>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Shelters</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse', background: '#1a1a1a', borderRadius: '0.5rem', overflow: 'hidden' }}>
              <thead>
                <tr style={{ background: '#333' }}>
                  <th style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Name</th>
                  <th style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Available Beds</th>
                  <th style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Total Beds</th>
                  <th style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Location</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Ananda Nilaya</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444', color: '#44ff44' }}>{data.zones[0].available_beds || 139}</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>192</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>100 Feet Road</td>
                </tr>
                <tr>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Vishwa Manava Hall</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444', color: '#44ff44' }}>{data.zones[0].available_beds || 70}</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>96</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>CMH Road, Metro Station</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Volunteers Table */}
          <div>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Volunteers</h2>
            <table style={{ width: '100%', borderCollapse: 'collapse', background: '#1a1a1a', borderRadius: '0.5rem', overflow: 'hidden' }}>
              <thead>
                <tr style={{ background: '#333' }}>
                  <th style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Name</th>
                  <th style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Status</th>
                  <th style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Location</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Anika Shah</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444', color: '#44ff44' }}>Available</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Indira Nagar - Ibbalur</td>
                </tr>
                <tr>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Rohan Verma</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444', color: '#ff4444' }}>Assigned</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Indira Nagar - Ecospace</td>
                </tr>
                <tr>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Vihaan Kumar</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444', color: '#ff4444' }}>Assigned</td>
                  <td style={{ padding: '1rem', borderBottom: '1px solid #444' }}>Indira Nagar - Phase 1</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ background: '#000', minHeight: '100vh', color: '#fff' }}>
      {/* Header */}
      <header style={{ background: '#111', padding: '2rem', textAlign: 'center', borderBottom: '1px solid #333' }}>
        <h1 style={{ fontSize: '3rem', color: '#0ff' }}>EcoRescue</h1>
        <p style={{ color: '#ccc', marginTop: '0.5rem' }}>AI-Powered Disaster Response System</p>
        <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
          <div style={{ width: '12px', height: '12px', background: '#0f0', borderRadius: '50%', animation: 'pulse 2s infinite' }}></div>
          <span style={{ color: '#0f0', fontWeight: 'bold' }}>System Active</span>
        </div>
      </header>

      {/* Stats */}
      <section style={{ padding: '3rem 2rem', background: '#111' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
          {[
            { label: "Total People Detected", value: data.total_people, color: '#0ff' },
            { label: "Available Shelter Beds", value: data.available_beds, color: '#0f0' },
            { label: "Active Volunteers", value: "50+", color: '#f0f' },
            { label: "Critical Zones", value: data.critical_zones, color: '#f00' },
          ].map((stat, i) => (
            <div key={i} style={{ background: '#222', padding: '2rem', borderRadius: '1rem', textAlign: 'center' }}>
              <p style={{ color: '#aaa', marginBottom: '0.5rem' }}>{stat.label}</p>
              <h2 style={{ fontSize: '3rem', color: stat.color, fontWeight: 'bold' }}>{stat.value}</h2>
            </div>
          ))}
        </div>
      </section>

      {/* Zones */}
      <section style={{ padding: '3rem 2rem' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Zone Monitoring</h2>
          <p style={{ color: '#aaa', marginBottom: '2rem' }}>Real-time risk assessment using drone imagery</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem' }}>
            {data.zones.map((zone: any) => {
              const style = getRiskStyle(zone.risk_level);
              return (
                <div
                  key={zone.id}
                  style={{ background: style.bg, border: `4px solid ${style.border}`, borderRadius: '1rem', padding: '1.5rem', cursor: 'pointer' }}
                  onClick={() => openZone(zone)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                    <div>
                      <h3 style={{ fontSize: '1.5rem' }}>{zone.name}</h3>
                      <span style={{ color: '#aaa', fontSize: '0.9rem' }}>Zone {zone.id}</span>
                    </div>
                    <span
  style={{
    background: zone.risk_level === "High" ? "#ff4d4d" : "#4caf50",
    padding: "0.5rem 1rem",
    borderRadius: "12px",
    color: "#fff"
  }}
>
  {zone.risk_level}
</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                    <div>
                      <p style={{ color: '#aaa', fontSize: '0.9rem' }}>Detected</p>
                      <strong style={{ fontSize: '1.8rem', color: style.text }}>{zone.detected_people}</strong>
                    </div>
                    <div>
                      <p style={{ color: '#aaa', fontSize: '0.9rem' }}>Available Beds</p>
                      <strong style={{ fontSize: '1.8rem', color: style.text }}>{zone.available_beds}</strong>
                    </div>
                  </div>
                  <button style={{ marginTop: '1rem', padding: '0.7rem 1.5rem', background: '#0ff', color: '#000', border: 'none', borderRadius: '0.5rem', cursor: 'pointer', fontWeight: 'bold' }}>
                    View Details
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Alerts */}
      <aside style={{ padding: '3rem 2rem', background: '#111' }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
          <h2 style={{ fontSize: '2rem', marginBottom: '1.5rem' }}>Active Alerts</h2>
          {data.critical_zones === 0 ? (
            <div style={{ background: '#222', padding: '3rem', textAlign: 'center', borderRadius: '1rem' }}>
              <p style={{ fontSize: '1.5rem', color: '#0f0' }}>No critical alerts</p>
              <p style={{ color: '#aaa' }}>All zones operating normally</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {data.zones
                .filter((z: any) => z.risk_level === 'Severe' || z.risk_level === 'Elevated')
                .map((z: any) => (
                  <div key={z.id} style={{ background: '#7f1d1d', borderLeft: '6px solid #f00', padding: '1.5rem', borderRadius: '0.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '0.5rem' }}>
                      <span style={{ background: '#f00', color: '#fff', padding: '0.3rem 0.8rem', borderRadius: '1rem', fontSize: '0.8rem', fontWeight: 'bold' }}>CRITICAL</span>
                      <button style={{ background: 'none', border: 'none', color: '#aaa', fontSize: '1.5rem', cursor: 'pointer' }}>×</button>
                    </div>
                    <p style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Capacity exceeded in {z.name}</p>
                    <p style={{ color: '#faa', marginTop: '0.5rem' }}>{z.detected_people} people • {z.available_beds} beds left</p>
                  </div>
                ))}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

export default App;