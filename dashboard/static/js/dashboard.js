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