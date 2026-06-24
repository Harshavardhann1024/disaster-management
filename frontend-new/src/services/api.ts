const BASE_URL = "http://localhost:8000/api";

const fetchWithTimeout = (url: string, timeout = 5000) => {
  return Promise.race([
    fetch(url),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error("API timeout")), timeout)
    ),
  ]);
};

export async function getZones() {
  try {
    const res = await fetchWithTimeout(`${BASE_URL}/zones`, 8000);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("getZones error:", err);
    return [];
  }
}

export async function getZone(id: number) {
  try {
    const res = await fetchWithTimeout(`${BASE_URL}/zones/${id}`, 8000);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("getZone error:", err);
    return null;
  }
}

export async function getAlerts() {
  try {
    const res = await fetchWithTimeout(`${BASE_URL}/alerts`, 8000);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("getAlerts error:", err);
    return [];
  }
}

export async function getPrediction(zoneId: number) {
  try {
    const res = await fetchWithTimeout(`${BASE_URL}/predict/${zoneId}`, 8000);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("getPrediction error:", err);
    return null;
  }
}

export async function getMedicalAlerts() {
  try {
    const res = await fetchWithTimeout(`${BASE_URL}/medical-alerts`, 8000);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("getMedicalAlerts error:", err);
    return [];
  }
}
