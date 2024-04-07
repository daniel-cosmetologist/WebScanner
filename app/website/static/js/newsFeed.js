document.addEventListener("DOMContentLoaded", function() {
    const newsFeed = document.getElementById('newsFeed');

    function updateNewsFeed() {
        fetch('/api/logs')
            .then(response => response.json())
            .then(data => {
                newsFeed.innerHTML = ''; // Очистить текущие события
                data.logs.forEach(log => {
                    const logItem = document.createElement('div');
                    logItem.textContent = log;
                    newsFeed.appendChild(logItem);
                });
            })
            .catch(error => console.error('Error fetching news feed:', error));
    }

    setInterval(updateNewsFeed, 10000); // Обновлять каждые 10 секунд
});
