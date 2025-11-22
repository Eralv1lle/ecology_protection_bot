const API_BASE_URL = window.location.origin;

async function fetchReports(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.status) params.append('status', filters.status);
    if (filters.waste_type) params.append('waste_type', filters.waste_type);
    if (filters.danger_level) params.append('danger_level', filters.danger_level);
    
    const url = `${API_BASE_URL}/api/reports${params.toString() ? '?' + params.toString() : ''}`;
    
    const response = await fetch(url);
    return await response.json();
}

async function fetchReport(reportId) {
    const response = await fetch(`${API_BASE_URL}/api/reports/${reportId}`);
    return await response.json();
}

async function fetchStats() {
    const response = await fetch(`${API_BASE_URL}/api/stats`);
    return await response.json();
}

function getPhotoUrl(photoPath) {
    return `${API_BASE_URL}/uploads/${photoPath}`;
}
