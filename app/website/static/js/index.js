function deleteNote(noteId) {
    fetch("/delete-note", {
      method: "POST",
      body: JSON.stringify({ noteId: noteId }),
    }).then((_res) => {
      window.location.href = "/";
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    const singleForm = document.querySelector("#addResourceForm");
    const bulkForm = document.querySelector("#bulkAddResourcesForm");

    singleForm.addEventListener("submit", function(e) {
        e.preventDefault();
        const url = document.querySelector("#urlInput").value;
        submitSingleResource(url);
    });

    bulkForm.addEventListener("submit", function(e) {
        e.preventDefault();
        const fileInput = document.querySelector("#fileInput");
        submitBulkResources(fileInput.files[0]);
    });

    function submitSingleResource(url) {
        fetch('/api/add_resource', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url }),
        })
        .then(response => response.json())
        .then(data => {
            displayMessage('success', 'Resource added successfully.');
        })
        .catch((error) => {
            displayMessage('error', 'Failed to add resource.');
        });
    }

    function submitBulkResources(file) {
        const formData = new FormData();
        formData.append('file', file);

        fetch('/api/bulk_add_resources', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            displayMessage('success', 'Bulk resources added successfully.');
        })
        .catch((error) => {
            displayMessage('error', 'Failed to add bulk resources.');
        });
    }

    function displayMessage(type, message) {
        const messageBox = document.querySelector("#messageBox");
        messageBox.className = `alert ${type === 'error' ? 'alert-danger' : 'alert-success'}`;
        messageBox.textContent = message;
        messageBox.style.display = 'block';
    }
});

