let debounceTimer;

function debouncedSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(searchName, 500); // wait 0.5s after typing stops
}

async function searchName() {
  const name = document.getElementById("searchBox").value.trim();
  if (name.length < 2) { 
    document.getElementById("results").innerHTML = "<p>Type at least 2 characters...</p>";
    return;
  }

  const response = await fetch("http://127.0.0.1:5000/search_name", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });

  const data = await response.json();
  let html = "<h3>Results:</h3>";

  if (data.results.length === 0) {
    html += "<p>No matches found.</p>";
  } else {
    data.results.forEach((r, idx) => {
      const badge = idx === 0 ? `<span class="top-match">Top Match</span>` : "";
      html += `
        <div class="result-card">
          <p><b>Hindi:</b> ${r.name_hindi} ${badge}</p>
          <p><b>English:</b> ${r.name_english}</p>
          <p><b>Case ID:</b> ${r.case_id}</p>
          <div class="progress-container">
            <div class="progress-bar" style="width:${r.score}%; background:${getColor(r.score)}">
              ${r.score}%
            </div>
          </div>
        </div>
      `;
    });
  }

  document.getElementById("results").innerHTML = html;
}

function getColor(score) {
  if (score >= 85) return "#27ae60"; // green
  if (score >= 70) return "#f39c12"; // orange
  return "#e74c3c"; // red
}