const typeData = JSON.parse(document.getElementById("by-type-data").textContent);
const statusData = JSON.parse(document.getElementById("by-status-data").textContent);

new Chart(document.getElementById("typeChart"), {
    type: "bar",
    data: {
        labels: typeData.map(d => d.event_type),
        datasets: [{ label: "Amount (₹)", data: typeData.map(d => d.amount), backgroundColor: "#f59e0b" }]
    },
    options: { responsive: true, plugins: { legend: { display: false } } }
});

new Chart(document.getElementById("statusChart"), {
    type: "doughnut",
    data: {
        labels: statusData.map(d => d.status),
        datasets: [{
            data: statusData.map(d => d.count),
            backgroundColor: ["#475569", "#3b82f6", "#f59e0b", "#10b981", "#64748b", "#a855f7"]
        }]
    },
    options: { responsive: true }
});