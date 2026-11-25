
const fileList = document.getElementById("fileList");
const totalFiles = document.getElementById("totalFiles");
const totalStorage = document.getElementById("totalStorage");
const fileInput = document.getElementById("fileInput");
const searchInput = document.getElementById("searchInput");
const csrfToken = document.querySelector(
    'meta[name="csrf-token"]'
).content;
// Format file sizes
function formatSize(bytes) {
    if (bytes < 1024) {
        return bytes + " Bytes";
    }

    if (bytes < 1024 * 1024) {
        return (bytes / 1024).toFixed(2) + " KB";
    }

    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
}

// Load documents from Flask API
async function loadFiles(search = "") {
    try {
        const url = search
            ? `/search?name=${encodeURIComponent(search)}`
            : "/files";

        const response = await fetch(url);
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Unable to load documents");
        }

        const files = search ? data.results : data.files;

        if (!search) {
            totalFiles.textContent = data.total_files;

            const storage = files.reduce(
                (total, file) => total + file.size,
                0
            );

            totalStorage.textContent = formatSize(storage);
        }

        fileList.innerHTML = "";

        if (files.length === 0) {
            fileList.innerHTML = `
                <tr>
                    <td colspan="4">No documents found.</td>
                </tr>
            `;
            return;
        }

        files.forEach(file => {
            const row = document.createElement("tr");

            const nameCell = document.createElement("td");
            nameCell.textContent = "📄 " + file.filename;

            const sizeCell = document.createElement("td");
            sizeCell.textContent = formatSize(file.size);

            const dateCell = document.createElement("td");
            dateCell.textContent =
                new Date(file.last_modified).toLocaleString();

            const actionsCell = document.createElement("td");

            const downloadButton = document.createElement("button");
            downloadButton.textContent = "Download";
            downloadButton.className = "action-button download-btn";
            downloadButton.addEventListener("click", () => {
                downloadFile(file.filename);
            });

            const deleteButton = document.createElement("button");
            deleteButton.textContent = "Delete";
            deleteButton.className = "action-button delete-btn";
            deleteButton.addEventListener("click", () => {
                deleteFile(file.filename);
            });

            actionsCell.append(downloadButton, deleteButton);

            row.append(nameCell, sizeCell, dateCell, actionsCell);
            fileList.appendChild(row);
        });

    } catch (error) {
        console.error(error);
        fileList.innerHTML = `
            <tr>
                <td colspan="4">Error: ${error.message}</td>
            </tr>
        `;
    }
}

// Upload document
fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];

    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/upload", {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken
            },
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Upload failed");
        }

        alert("Document uploaded successfully!");
        fileInput.value = "";
        loadFiles();

    } catch (error) {
        alert("Upload failed: " + error.message);
    }
});

// Download document
function downloadFile(filename) {
    window.location.href =
        `/download/${encodeURIComponent(filename).replaceAll("%2F", "/")}`;
}

// Delete document
async function deleteFile(filename) {
    const confirmed = confirm(
        `Are you sure you want to delete ${filename}?`
    );

    if (!confirmed) return;

    try {
        const response = await fetch(
            `/delete/${encodeURIComponent(filename).replaceAll("%2F", "/")}`,
            {
                method: "DELETE",
                headers: {
                    "X-CSRFToken": csrfToken
                },

            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Delete failed");
        }

        alert("Document deleted successfully!");
        loadFiles(searchInput.value);

    } catch (error) {
        alert("Delete failed: " + error.message);
    }
}

// Search documents
searchInput.addEventListener("input", () => {
    loadFiles(searchInput.value.trim());
});

// Load documents when page opens
loadFiles();
