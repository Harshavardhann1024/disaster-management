const BASE_URL = "http://localhost:8000/api";

export async function getZones() {
  const res = await fetch(`${BASE_URL}/zones`);
  return res.json();
}

export async function getZone(id: number) {
  const res = await fetch(`${BASE_URL}/zones/${id}`);
  return res.json();
}

export async function getAlerts() {
  const res = await fetch(`${BASE_URL}/alerts`);
  return res.json();
}
