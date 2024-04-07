document.addEventListener("DOMContentLoaded", function() {
    loadResources();

    document.getElementById("domainSearchInput").addEventListener("input", () => loadResources());
    document.getElementById("domainZoneFilter").addEventListener("change", () => loadResources());
    document.getElementById("statusFilter").addEventListener("change", () => loadResources());
});

function loadResources(page = 1) {
    const domainSearchInput = document.getElementById("domainSearchInput").value;
    const domainZoneFilter = document.getElementById("domainZoneFilter").value;
    const statusFilter = document.getElementById("statusFilter").value;

    let apiUrl = `/api/resources?page=${page}`;
    const params = new URLSearchParams();
    if (domainSearchInput) params.append("domain", domainSearchInput);
    if (domainZoneFilter) params.append("zone", domainZoneFilter);
    if (statusFilter) params.append("status", statusFilter);
    if (params.toString()) apiUrl += `&${params.toString()}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            updateTable(data.resources);
            updatePagination(data.page, data.pages);
        })
        .catch(error => console.error('Error loading resources:', error));
}

function updateTable(resources) {
    const tableBody = document.getElementById("resourceTableBody");
    tableBody.innerHTML = '';
    resources.forEach((resource, index) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <th scope="row">${index + 1}</th>
            <td><a href="/resource/${resource.id}">${resource.url}</a></td>
            <td>${resource.domain}</td>
            <td>${resource.status}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteResource('${resource.id}')">Delete</button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

function updatePagination(currentPage, totalPages) {
    const pagination = document.getElementById("pagination");
    pagination.innerHTML = ''; 

    // Previous page
    let li = document.createElement("li");
    li.className = `page-item ${currentPage === 1 ? "disabled" : ""}`;
    li.innerHTML = `<a class="page-link" href="#" onclick="loadResources(${currentPage - 1})">Previous</a>`;
    pagination.appendChild(li);

    // Page numbers
    for (let page = 1; page <= totalPages; page++) {
        li = document.createElement("li");
        li.className = `page-item ${page === currentPage ? "active" : ""}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="loadResources(${page})">${page}</a>`;
        pagination.appendChild(li);
    }

    // Next page
    li = document.createElement("li");
    li.className = `page-item ${currentPage === totalPages ? "disabled" : ""}`;
    li.innerHTML = `<a class="page-link" href="#" onclick="loadResources(${currentPage + 1})">Next</a>`;
    pagination.appendChild(li);
}

function deleteResource(resourceId) {
    if (confirm("Are you sure you want to delete this resource?")) {
        fetch(`/api/delete_resource/${resourceId}`, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json',
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Delete successful', data);
            loadResources(); // Refresh the list
        })
        .catch(error => console.error('Error:', error));
    }
}
