const socket = io('http://127.0.0.1:5000');

let animationInterval = null;

// ── Incoming emergency from backend ──────────────────────
socket.on('new_emergency', async (data) => {
    const alertBox = document.getElementById('alertBox');
    alertBox.style.borderColor = '#e94560';
    alertBox.innerHTML = `
        <span style="color:#e94560; font-size:1.1rem; font-weight:bold;"> EMERGENCY ALERT!</span><br><br>
        <b>Patient:</b> ${data.name}<br>
        <b>Location:</b> ${data.lat.toFixed(4)}, ${data.lon.toFixed(4)}<br><br>
        <span style="color:#aaa; font-size:0.85rem;">Processing optimal route...</span>
    `;
    showStatus(" Running A* algorithm on Chennai roads...", "");
    await processRoute(data.name, data.lat, data.lon);
});

// ── Route ready — start animation ─────────────────────────
socket.on('route_ready', (data) => {
    showStatus(
        ` Route Ready!\n\n` +
        ` Patient: ${data.patient}\n` +
        ` Road Distance: ${data.distance_km} km\n` +
        ` Path Nodes (A*): ${data.nodes}\n\n` +
        ` Ambulance is on the way...`,
        "success"
    );

    // Start ambulance animation after map loads
    setTimeout(() => {
        startAmbulanceAnimation(data.path_coords, data.patient);
    }, 3000);
});

// ── Ambulance animation ────────────────────────────────────
function startAmbulanceAnimation(pathCoords, patientName) {
    if (!pathCoords || pathCoords.length === 0) return;

    const mapFrame = document.getElementById('routeMap');
    let step = 0;
    const totalSteps = pathCoords.length;

    // Clear previous animation
    if (animationInterval) clearInterval(animationInterval);

    // Update status
    showStatus(
        ` Ambulance Moving...\n\n` +
        `Patient: ${patientName}\n` +
        `Progress: 0%`,
        "success"
    );

    animationInterval = setInterval(() => {
        if (step >= totalSteps) {
            clearInterval(animationInterval);
            showStatus(
                ` Ambulance Arrived!\n\n` +
                `Patient: ${patientName}\n` +
                `Status: Help is here!`,
                "success"
            );

            // Flash alert box green
            const alertBox = document.getElementById('alertBox');
            alertBox.style.borderColor = '#00c853';
            alertBox.innerHTML = `
                <span style="color:#00c853; font-size:1.1rem; font-weight:bold;"> AMBULANCE ARRIVED!</span><br><br>
                <b>Patient:</b> ${patientName}<br>
                <b>Status:</b> Help is on scene!
            `;
            return;
        }

        // Send current position to map iframe
        const lat = pathCoords[step][0];
        const lon = pathCoords[step][1];
        const progress = Math.round((step / totalSteps) * 100);

        // Post message to iframe to update ambulance position
        mapFrame.contentWindow.postMessage({
            type: 'updateAmbulance',
            lat: lat,
            lon: lon,
            progress: progress
        }, '*');

        // Update status
        showStatus(
            ` Ambulance Moving...\n\n` +
            `Patient: ${patientName}\n` +
            `Progress: ${progress}%`,
            "success"
        );

        step += 1; // Move 3 steps at a time for speed
    }, 80); // Update every 100ms
}

// ── Process route ──────────────────────────────────────────
async function processRoute(name, lat, lon) {
    try {
        const response = await fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, lat, lon })
        });

        const data = await response.json();

        if (data.success) {
            const mapFrame = document.getElementById('routeMap');
            mapFrame.src = 'route_map.html?t=' + Date.now();
            document.getElementById('mapMsg').style.display = 'none';
            loadAmbulances();
        } else {
            showStatus(` ${data.error}`, "error");
        }
    } catch (err) {
        showStatus(" Could not connect to server!", "error");
    }
}

// ── Load ambulances ────────────────────────────────────────
async function loadAmbulances() {
    try {
        const res = await fetch('/ambulances');
        const data = await res.json();
        const list = document.getElementById('ambulanceList');
        list.innerHTML = '';
        for (const [id, amb] of Object.entries(data)) {
            const div = document.createElement('div');
            div.className = 'ambulance-item';
            div.innerHTML = `
                <span> ${id}</span>
                <span class="${amb.status}">${amb.status.toUpperCase()}</span>
            `;
            list.appendChild(div);
        }
    } catch (err) {
        document.getElementById('ambulanceList').innerText = " Could not load ambulances";
    }
}

// ── Reset ──────────────────────────────────────────────────
async function resetAmbulances() {
    if (animationInterval) clearInterval(animationInterval);
    await fetch('/reset', { method: 'POST' });
    loadAmbulances();
    showStatus(" All ambulances reset to available!", "success");
    document.getElementById('alertBox').innerHTML = "Waiting for emergency...";
    document.getElementById('alertBox').style.borderColor = '';
    document.getElementById('routeMap').src = '';
    document.getElementById('mapMsg').style.display = 'block';
}

// ── Status ─────────────────────────────────────────────────
function showStatus(message, type) {
    const box = document.getElementById('status');
    box.innerText = message;
    box.className = `status-box ${type}`;
}

window.onload = () => loadAmbulances();
