let map, markers = [];

function initMap(lat, lng) {
  if (!map) {
    map = L.map("map").setView([lat, lng], 14);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19
    }).addTo(map);
  } else {
    map.setView([lat, lng], 14);
  }
}

function clearMarkers() {
  markers.forEach(m => m.remove());
  markers = [];
}

function addMarker(lat, lng, text) {
  const m = L.marker([lat, lng]).addTo(map).bindPopup(text);
  markers.push(m);
}

function renderResults(items) {
  const el = document.getElementById("results");
  el.innerHTML = "";

  items.forEach((p) => {
    const div = document.createElement("div");
    div.className = "result";
    div.innerHTML = `
        <strong>${p.name}</strong>
        <div class="small">${p.address ?? "Address not available"}</div>
        <div class="pill">distance: ${p.distance_m}m · score: ${p.score} · boost: ${p.personal_boost ?? 0}</div>
        <div style="margin-top:8px; display:flex; gap:8px;">
            <button data-action="like" data-id="${p.place_id}" data-cat="${(p.categories && p.categories[0]) || ""}">👍 Like</button>
            <button data-action="dislike" data-id="${p.place_id}" data-cat="${(p.categories && p.categories[0]) || ""}">👎 Dislike</button>
        </div>
    `;


  // feedback buttons
  el.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", async () => {
      const user_id = document.getElementById("user_id").value.trim();
      if (!user_id) return alert("Set a user_id to save feedback");

      await fetch("/feedback", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
          user_id,
          place_id: btn.dataset.id,
          action: "like",
          category_hint: btn.dataset.cat || null
        })
      });
      document.getElementById("status").textContent = "Saved 👍 — search again to see boost";
    });
  });
}

document.getElementById("btnSearch").addEventListener("click", async () => {
  const query = document.getElementById("query").value;
  const user_id = document.getElementById("user_id").value.trim() || null;
  const lat = parseFloat(document.getElementById("lat").value);
  const lng = parseFloat(document.getElementById("lng").value);
  const radius_m = parseInt(document.getElementById("radius_m").value, 10);
  const max_results = parseInt(document.getElementById("max_results").value, 10);

  document.getElementById("status").textContent = "Searching...";

  initMap(lat, lng);
  clearMarkers();
  addMarker(lat, lng, "You");

  const resp = await fetch("/recommend", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ lat, lng, query, radius_m, max_results, open_now: true, user_id })
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    document.getElementById("status").textContent = `Error: ${err.detail || resp.status}`;
    return;
  }

  const data = await resp.json();
  const items = data.results || [];

  renderResults(items);
  items.forEach(p => addMarker(p.lat, p.lng, `${p.name}<br/>score: ${p.score}`));
  document.getElementById("status").textContent = `Found ${items.length} places`;
});

// auto-search once on page load
document.getElementById("btnSearch").click();
