document.addEventListener('DOMContentLoaded', function () {
    const socket = io();

    // Khởi tạo biểu đồ
    const ctx = document.getElementById('performanceChart').getContext('2d');
    const performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({ length: 30 }, (_, i) => i + 1),
            datasets: [{
                label: 'Số dư (USD)',
                data: Array.from({ length: 30 }, () => Math.random() * 100 + 1000).map(Math.round),
                borderColor: '#00bfa5',
                backgroundColor: 'rgba(0, 191, 165, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            }
        }
    });

    // Cập nhật trạng thái
    socket.on('status_update', function (status) {
        const statusText = document.getElementById('statusText');
        const statusIndicator = document.getElementById('statusIndicator');
        const uptime = document.getElementById('uptime');
        const configText = document.getElementById('configText');
        const lastSignalDiv = document.getElementById('lastSignal');

        statusText.textContent = status.is_running ? '🟢 Đang chạy' : '🔴 Dừng';
        statusIndicator.style.background = status.is_running ? '#00c853' : '#d50000';
        uptime.textContent = status.uptime;

        if (status.config) {
            configText.textContent = `${status.config.symbol} | ${status.config.interval}`;
        }

        if (status.last_signal) {
            const s = status.last_signal;
            lastSignalDiv.innerHTML = `
                <div class="signal ${s.side === 'BUY' ? 'buy' : 'sell'}">
                    <div class="signal-info">
                        <strong>${s.side} ${s.strategy}</strong> 
                        @ ${s.entry.toFixed(8)} 
                        <br><small>Tin cậy: ${(s.final_confidence * 100).toFixed(1)}% | 
                        ${new Date(s.timestamp).toLocaleTimeString()}</small>
                    </div>
                    <div class="signal-actions">
                        <button class="btn btn-sm btn-outline-light">Xem chi tiết</button>
                    </div>
                </div>
            `;
        } else {
            lastSignalDiv.textContent = "Chưa có tín hiệu nào";
        }
    });

    // Cập nhật log
    socket.on('log_update', function (data) {
        const logDiv = document.getElementById('log');
        const entry = document.createElement('div');
        entry.textContent = data.log;
        logDiv.appendChild(entry);
        logDiv.scrollTop = logDiv.scrollHeight;
    });

    // Nút điều khiển
    document.getElementById('startBtn').onclick = () => socket.emit('start_bot');
    document.getElementById('stopBtn').onclick = () => socket.emit('stop_bot');

    document.getElementById('saveConfigBtn').onclick = () => {
        const strategies = Array.from(
            document.getElementById('strategySelect').selectedOptions
        ).map(o => o.value);

        socket.emit('update_config', {
            symbol: document.getElementById('symbolInput').value,
            active_strategies: strategies
        });
    };
});

// Thêm vào dashboard.js
function updatePerformanceChart(data) {
    const ctx = document.getElementById('performanceChart').getContext('2d');
    
    // Real-time performance tracking
    if (performanceChart.data.labels.length > 50) {
        performanceChart.data.labels.shift();
        performanceChart.data.datasets[0].data.shift();
    }
    
    performanceChart.data.labels.push(new Date().toLocaleTimeString());
    performanceChart.data.datasets[0].data.push(data.current_balance);
    performanceChart.update();
}

// Strategy performance comparison
function createStrategyComparisonChart(strategyData) {
    const ctx = document.getElementById('strategyChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(strategyData),
            datasets: [{
                label: 'Confidence Score',
                data: Object.values(strategyData).map(s => s.avg_confidence),
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
            }]
        }
    });
}

// dashboard.js - Thêm trạng thái UI
let botControlEnabled = true;

document.getElementById('startBtn').onclick = () => {
    if (!botControlEnabled) return;
    
    botControlEnabled = false;
    document.getElementById('startBtn').disabled = true;
    document.getElementById('startBtn').innerHTML = '⏳ Đang khởi động...';
    
    socket.emit('start_bot');
    
    // Re-enable sau 3 giây
    setTimeout(() => {
        botControlEnabled = true;
        document.getElementById('startBtn').disabled = false;
        document.getElementById('startBtn').innerHTML = '🟢 Bật Bot';
    }, 3000);
};

document.getElementById('stopBtn').onclick = () => {
    if (!botControlEnabled) return;
    
    if (confirm('Bạn có chắc muốn dừng bot?')) {
        botControlEnabled = false;
        document.getElementById('stopBtn').disabled = true;
        document.getElementById('stopBtn').innerHTML = '⏳ Đang dừng...';
        
        socket.emit('stop_bot');
        
        setTimeout(() => {
            botControlEnabled = true;
            document.getElementById('stopBtn').disabled = false;
            document.getElementById('stopBtn').innerHTML = '🔴 Dừng Bot';
        }, 3000);
    }
};

// Cập nhật UI theo trạng thái thực tế
socket.on('status_update', function (status) {
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    
    if (status.is_running) {
        startBtn.style.opacity = '0.5';
        stopBtn.style.opacity = '1';
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } else {
        startBtn.style.opacity = '1';
        stopBtn.style.opacity = '0.5';
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
});