document.getElementById('downloadLogs').addEventListener('click', function() {
    fetch('/api/logs')
        .then(response => response.json())
        .then(data => {
            const blob = new Blob([data.logs.join('\n')], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'logs.txt';
            document.body.appendChild(a); // Добавляем элемент временно
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a); // Удаляем элемент
        })
        .catch(error => console.error('Error downloading logs:', error));
});
