document.addEventListener("DOMContentLoaded", function() {
    // Извлекаем ID ресурса из data-атрибута элемента newsFeed
    const newsFeed = document.getElementById('newsFeed');
    const resourceId = newsFeed.getAttribute('data-resource-id');

    function updateNewsFeed() {
        fetch(`/api/news_by_resource/${resourceId}`)
            .then(response => response.json())
            .then(data => {
                newsFeed.innerHTML = ''; // Очищаем текущий список новостей
                data.news.forEach(newsItem => {
                    // Для каждой новости создаём элементы и заполняем их данными
                    const item = document.createElement('div');
                    const title = document.createElement('h4');
                    const content = document.createElement('p');

                    title.textContent = newsItem.title;
                    content.textContent = newsItem.content;

                    item.appendChild(title);
                    item.appendChild(content);

                    newsFeed.appendChild(item);
                });
            })
            .catch(error => console.error('Error fetching news:', error));
    }

    updateNewsFeed();
});
