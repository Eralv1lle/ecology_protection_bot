let map;
let objectManager;
let currentFilters = {};

ymaps.ready(init);

function init() {
    map = new ymaps.Map('map', {
        center: [61.241778, 73.393032],
        zoom: 10,
        controls: ['zoomControl', 'fullscreenControl']
    });

    objectManager = new ymaps.ObjectManager({
        clusterize: true,
        gridSize: 64,
        clusterIconLayout: 'default#pieChart',
        clusterDisableClickZoom: false
    });

    map.geoObjects.add(objectManager);
    map.setCenter([61.241778, 73.393032], 10);


    loadReports();
    setupEventListeners();
}

async function loadReports(filters = {}) {
    const reports = await fetchReports(filters);
    displayReportsOnMap(reports);
}

function displayReportsOnMap(reports) {
    const features = reports.map(report => {
        const dangerColors = {
            'низкий': '#4CAF50',
            'средний': '#FF9800',
            'высокий': '#F44336',
            'критический': '#B71C1C'
        };

        const statusIcons = {
            'new': 'islands#blueCircleIcon',
            'reviewing': 'islands#orangeCircleIcon',
            'in_progress': 'islands#violetCircleIcon',
            'resolved': 'islands#greenCircleIcon',
            'rejected': 'islands#redCircleIcon'
        };

        return {
            type: 'Feature',
            id: report.id,
            geometry: {
                type: 'Point',
                coordinates: [report.latitude, report.longitude]
            },
            properties: {
                balloonContentHeader: `<strong>${report.waste_type}</strong>`,
                balloonContentBody: `
                    <p><strong>Уровень опасности:</strong> <span style="color: ${dangerColors[report.danger_level]}">${report.danger_level}</span></p>
                    <p><strong>Статус:</strong> ${getStatusName(report.status)}</p>
                    <p><strong>Описание:</strong> ${report.description}</p>
                    <p><a href="#" onclick="showReportCard(${report.id}); return false;">Подробнее</a></p>
                `,
                balloonContentFooter: `Дата: ${new Date(report.created_at).toLocaleDateString('ru-RU')}`,
                iconContent: report.id,
                hintContent: `${report.waste_type} - ${report.danger_level}`
            },
            options: {
                preset: statusIcons[report.status] || 'islands#blueCircleIcon'
            }
        };
    });

    objectManager.removeAll();
    objectManager.add({
        type: 'FeatureCollection',
        features: features
    });

    if (features.length > 0) {
        const bounds = objectManager.getBounds();
        if (bounds) {
            map.setBounds(bounds, {
                checkZoomRange: true,
                zoomMargin: 50
            });
        }
    }
}

async function showReportCard(reportId) {
    const report = await fetchReport(reportId);
    
    const statusNames = {
        'new': 'Новый',
        'reviewing': 'На рассмотрении',
        'in_progress': 'В работе',
        'resolved': 'Решён',
        'rejected': 'Отклонён'
    };

    const cardContent = `
        <img src="${getPhotoUrl(report.photo_path)}" alt="Фото загрязнения">
        <h3>Отчёт #${report.id} 
            <span class="status-badge status-${report.status}">${statusNames[report.status]}</span>
        </h3>
        <div class="report-info">
            <p><strong>👤 Пользователь:</strong> @${report.username || 'Неизвестно'}</p>
            <p><strong>🗑️ Тип отходов:</strong> ${report.waste_type}</p>
            <p><strong>⚠️ Уровень опасности:</strong> <span class="danger-${report.danger_level}">${report.danger_level}</span></p>
            <p><strong>📍 Координаты:</strong> ${report.latitude}, ${report.longitude}</p>
            ${report.address ? `<p><strong>📌 Адрес:</strong> ${report.address}</p>` : ''}
            <p><strong>📝 Описание:</strong> ${report.description}</p>
            <p><strong>📅 Дата создания:</strong> ${new Date(report.created_at).toLocaleString('ru-RU')}</p>
            <p><strong>🔄 Обновлён:</strong> ${new Date(report.updated_at).toLocaleString('ru-RU')}</p>
        </div>
        ${report.history && report.history.length > 0 ? `
            <h4 style="margin-top: 20px;">История изменений:</h4>
            <ul style="list-style: none; padding: 0;">
                ${report.history.map(h => `
                    <li style="padding: 10px; background: #f5f5f5; margin: 5px 0; border-radius: 5px;">
                        <strong>${getStatusName(h.old_status)} → ${getStatusName(h.new_status)}</strong><br>
                        ${h.comment ? `<em>${h.comment}</em><br>` : ''}
                        <small>${new Date(h.created_at).toLocaleString('ru-RU')}</small>
                    </li>
                `).join('')}
            </ul>
        ` : ''}
    `;

    document.getElementById('reportContent').innerHTML = cardContent;
    document.getElementById('reportCard').classList.remove('hidden');
}

function getStatusName(status) {
    const names = {
        'new': 'Новый',
        'reviewing': 'На рассмотрении',
        'in_progress': 'В работе',
        'resolved': 'Решён',
        'rejected': 'Отклонён'
    };
    return names[status] || status;
}

async function showStats() {
    const stats = await fetchStats();

    const statusNames = {
        'new': 'Новые',
        'reviewing': 'На рассмотрении',
        'in_progress': 'В работе',
        'resolved': 'Решённые',
        'rejected': 'Отклонённые'
    };

    let statsHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <h3>${stats.total_reports}</h3>
                <p>Всего отчётов</p>
            </div>
            <div class="stat-card">
                <h3>${stats.total_users}</h3>
                <p>Активных пользователей</p>
            </div>
        </div>

        <h3>По статусам:</h3>
        <div class="stats-grid">
            ${Object.entries(stats.reports_by_status).map(([status, count]) => `
                <div class="stat-card">
                    <h3>${count}</h3>
                    <p>${statusNames[status]}</p>
                </div>
            `).join('')}
        </div>

        <h3 style="margin-top: 30px;">По типам отходов:</h3>
        <div class="stats-grid">
            ${Object.entries(stats.reports_by_type).map(([type, count]) => `
                <div class="stat-card">
                    <h3>${count}</h3>
                    <p>${type}</p>
                </div>
            `).join('')}
        </div>

        <h3 style="margin-top: 30px;">Топ пользователей:</h3>
        <table style="width: 100%; margin-top: 20px; border-collapse: collapse;">
            <thead>
                <tr style="background: #667eea; color: white;">
                    <th style="padding: 10px; text-align: left;">Место</th>
                    <th style="padding: 10px; text-align: left;">Пользователь</th>
                    <th style="padding: 10px; text-align: center;">Отчётов</th>
                    <th style="padding: 10px; text-align: center;">Рейтинг</th>
                </tr>
            </thead>
            <tbody>
                ${stats.top_users.map((user, index) => `
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px;">${index + 1}</td>
                        <td style="padding: 10px;">@${user.username || 'Неизвестно'}</td>
                        <td style="padding: 10px; text-align: center;">${user.reports_count}</td>
                        <td style="padding: 10px; text-align: center;">${user.rating} ⭐</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    document.getElementById('statsContent').innerHTML = statsHTML;
    document.getElementById('statsPanel').classList.remove('hidden');
    document.getElementById('map').parentElement.style.display = 'none';
}

function setupEventListeners() {
    document.getElementById('closeCardBtn').addEventListener('click', () => {
        document.getElementById('reportCard').classList.add('hidden');
    });

    document.getElementById('filterBtn').addEventListener('click', () => {
        document.getElementById('filterPanel').classList.toggle('hidden');
    });

    document.getElementById('applyFiltersBtn').addEventListener('click', () => {
        currentFilters = {
            status: document.getElementById('statusFilter').value,
            waste_type: document.getElementById('wasteTypeFilter').value,
            danger_level: document.getElementById('dangerFilter').value
        };
        loadReports(currentFilters);
        document.getElementById('filterPanel').classList.add('hidden');
    });

    document.getElementById('resetFiltersBtn').addEventListener('click', () => {
        document.getElementById('statusFilter').value = '';
        document.getElementById('wasteTypeFilter').value = '';
        document.getElementById('dangerFilter').value = '';
        currentFilters = {};
        loadReports();
        document.getElementById('filterPanel').classList.add('hidden');
    });

    document.getElementById('allReportsBtn').addEventListener('click', () => {
        document.getElementById('statsPanel').classList.add('hidden');
        document.getElementById('map').parentElement.style.display = 'block';
        loadReports(currentFilters);
        
        document.querySelectorAll('nav button').forEach(btn => btn.classList.remove('active'));
        document.getElementById('allReportsBtn').classList.add('active');
    });

    document.getElementById('statsBtn').addEventListener('click', () => {
        showStats();
        document.querySelectorAll('nav button').forEach(btn => btn.classList.remove('active'));
        document.getElementById('statsBtn').classList.add('active');
    });
}
