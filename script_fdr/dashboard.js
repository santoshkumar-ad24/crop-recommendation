const API_URL = 'http://127.0.0.1:5000';


(function(){
            const form = document.getElementById('cropForm');
            const resetBtn = document.getElementById('resetBtn');
            const resultCard = document.getElementById('resultCard');

            function clearResults(){
                if (resultCard) resultCard.innerHTML = '';
            }

            // Expose a global function in case other code calls resetForm()
            window.resetForm = function(){ if(form) form.reset(); clearResults(); };

            if (resetBtn) {
                resetBtn.addEventListener('click', function(e){
                    e.preventDefault();
                    if (form) form.reset();
                    clearResults();
                    try { document.activeElement && document.activeElement.blur(); } catch (err) {}
                });
            }
        })();
// Optional: ping server on load and update indicator if present


async function checkServer() {
  const statusEl = document.getElementById('serverStatus');
  if (!statusEl) return;
  try {
    const r = await fetch(`${API_URL}/health`);
    if (r.ok) {
      statusEl.textContent = 'Server: Online';
      statusEl.style.color = 'green';
    } else {
      statusEl.textContent = 'Server: Unreachable';
      statusEl.style.color = 'orange';
    }
  } catch (e) {
    statusEl.textContent = 'Server: Offline';
    statusEl.style.color = 'red';
  }
}

checkServer();

document.getElementById("cropForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const form = e.target;
  const resultCard = document.getElementById("resultCard");
  resultCard.innerHTML = `<p>⏳ Predicting the best crops...</p>`;

  // 1. Get input values safely by name if available, fallback to indexed
  const getVal = (name, idx) => {
    const el = form.elements[name] || form.elements[idx];
    return el ? el.value : undefined;
  };

  const payload = {
    N: parseFloat(getVal('N', 0)),
    P: parseFloat(getVal('P', 1)),
    K: parseFloat(getVal('K', 2)),
    temperature: parseFloat(getVal('temperature', 3)),
    humidity: parseFloat(getVal('humidity', 4)),
    ph: parseFloat(getVal('ph', 5)),
    rainfall: parseFloat(getVal('rainfall', 6))
  };

  // Validate numeric inputs
  const nanFields = Object.keys(payload).filter(k => Number.isNaN(payload[k]));
  if (nanFields.length) {
    resultCard.innerHTML = `<p style="color:red;">Please enter valid numbers for: ${nanFields.join(', ')}</p>`;
    return;
  }

  try {
    // 2. Call Flask API for predictions
    const res = await fetch(`${API_URL}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (!res.ok) {
      const msg = data && data.error ? data.error : `Server returned ${res.status}`;
      resultCard.innerHTML = `<p style="color:red">❌ ${msg}</p>`;
      return;
    }

    // API returns { predictions: [ {crop, confidence}, ... ] }
    const predictions = (data && data.predictions) ? data.predictions : [];
    if (!predictions.length) {
      resultCard.innerHTML = `<p>No predictions returned.</p>`;
      return;
    }

    // 3. Load crop info JSON (optional) - fail gracefully if not present
    let cropInfo = {};
    try {
      const infoRes = await fetch("./dataset/crop_info.json");
      if (infoRes.ok) cropInfo = await infoRes.json();
    } catch (e) {
      // ignore, we'll show basic results
    }

    // 4. Generate HTML for top crops
    let output = "";
    predictions.forEach(p => {
      const cropName = (p.crop !== undefined && p.crop !== null) ? String(p.crop) : 'Unknown';
      const confidence = (p.confidence !== undefined) ? Number(p.confidence) : null;
      const cropKey = cropName.toLowerCase();
      if (cropInfo && cropInfo[cropKey]) {
          const crop = cropInfo[cropKey];
          const img = crop.image || 'rsc/home-rsc/hero.png';
          const season = crop.season || 'N/A';
          const tips = crop.tips || '';
          output += `
            
            <div class="crop-card">
              <img src="${img}" alt="${cropName}" loading="lazy" />
              <div class="card-body">
                <h3>${cropName}</h3>
                <p>${crop.desc}</p>
                <p><b>Market Price:</b> ${crop.price}</p>
                <p><b>Season:</b> ${season}</p>
                ${tips ? `<p class="tips" style="margin-top:8px; color:#2b3b2b; font-size:0.95rem"><strong style="color:#000000;">Tip:</strong> ${tips}</p>` : ''}
                <div class="confidence">
                  <div class="badge">${confidence !== null ? confidence + '%' : 'N/A'}</div>
                  <div class="bar"><i style="width:0%" data-target="${Math.max(0, Math.min(100, confidence || 0))}"></i></div>
                </div>
              </div>
            </div>
            
          `;
        } else {
          output += `
            <div class="crop-card">
              <div class="card-body">
                <h3>🌾 ${cropName}</h3>
                <p>No additional info available</p>
                <div class="confidence">
                  <div class="badge">${confidence !== null ? confidence + '%' : 'N/A'}</div>
                  <div class="bar"><i style="width:0%" data-target="${Math.max(0, Math.min(100, confidence || 0))}"></i></div>
                </div>
              </div>
            </div>
          `;
        }
    });

    // 5. Display results
    resultCard.innerHTML = output;

    // animate confidence bars and attach tips toggle handlers
    document.querySelectorAll('.confidence .bar > i').forEach(el => {
      const target = el.getAttribute('data-target') || '0';
      // small timeout so transition can apply if CSS has it
      setTimeout(() => { el.style.width = target + '%'; }, 40);
    });

    // No tips toggle: tips (if present) are shown inline as a short paragraph.

    // update server status indicator if present
    const statusEl = document.getElementById('serverStatus');
    if (statusEl) { statusEl.textContent = 'Server: Online'; statusEl.style.color = 'green'; }

  } catch (err) {
    resultCard.innerHTML = `<p style="color:red;">❌ Error: ${err.message}</p>`;
    const statusEl = document.getElementById('serverStatus');
    if (statusEl) { statusEl.textContent = 'Server: Offline'; statusEl.style.color = 'red'; }
  }
});
