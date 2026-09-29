const API_URL = "http://127.0.0.1:8000";

let selectedDocumentId = null;


// ===============================
// Load documents
// ===============================

async function loadDocuments() {

    const documentsList = document.getElementById("documentsList");

    try {

        const response = await fetch(`${API_URL}/documents`);

        if (!response.ok) {
            throw new Error("Failed to load documents");
        }

        const documents = await response.json();

        documentsList.innerHTML = "";

        if (documents.length === 0) {

            documentsList.innerHTML =
                "<p>No documents uploaded yet.</p>";

            return;
        }

        documents.forEach(doc => {

        const div = document.createElement("div");

        div.className = "document";

        div.innerHTML = `
            <div class="document-info">

                <span class="document-name">
                    📄 ${doc.filename || doc.title}
                </span>

                <span class="document-id">
                    Document ID: ${doc.id}
                </span>

            </div>

            <div class="document-actions">

                <button onclick="selectDocument(${doc.id}, '${escapeHtml(doc.filename || doc.title)}')">
                    Ask
                </button>

                <button
                    class="delete-btn"
                    onclick="deleteDocument(${doc.id})"
                >
                    Delete
                </button>

            </div>
        `;

        documentsList.appendChild(div);

});

    } catch (error) {

        console.error(error);

        documentsList.innerHTML =
            "<p>Could not connect to the API.</p>";
    }
}


// ===============================
// Select document
// ===============================

function selectDocument(documentId, filename) {

    selectedDocumentId = documentId;

    const selectedDocument =
        document.getElementById("selectedDocument");

    selectedDocument.textContent =
        `Selected document: ${filename}`;

}


// ===============================
// Upload PDF
// ===============================

async function uploadDocument() {

    const fileInput =
        document.getElementById("pdfFile");

    const status =
        document.getElementById("uploadStatus");

    if (fileInput.files.length === 0) {

        status.textContent =
            "Please select a PDF file.";

        return;
    }

    const file = fileInput.files[0];

    const formData = new FormData();

    formData.append("file", file);

    status.textContent = "Uploading and processing...";

    try {

        const response = await fetch(
            `${API_URL}/documents/upload`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Upload failed"
            );
        }

        status.textContent =
            "Document uploaded successfully!";

        fileInput.value = "";

        await loadDocuments();

    } catch (error) {

        console.error(error);

        status.textContent =
            `Error: ${error.message}`;
    }
}


// ===============================
// Delete document
// ===============================

async function deleteDocument(documentId) {

    const confirmed = confirm(
        "Are you sure you want to delete this document?"
    );

    if (!confirmed) {
        return;
    }

    try {

        const response = await fetch(
            `${API_URL}/documents/${documentId}`,
            {
                method: "DELETE"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Delete failed"
            );
        }

        if (selectedDocumentId === documentId) {

            selectedDocumentId = null;

            document.getElementById(
                "selectedDocument"
            ).textContent =
                "Select a document first.";
        }

        await loadDocuments();

    } catch (error) {

        console.error(error);

        alert(
            `Error deleting document: ${error.message}`
        );
    }
}


// ===============================
// Ask question
// ===============================

async function askQuestion() {

    const questionInput =
        document.getElementById("question");

    const answerDiv =
        document.getElementById("answer");

    const question =
        questionInput.value.trim();

    if (!selectedDocumentId) {

        answerDiv.textContent =
            "Please select a document first.";

        return;
    }

    if (!question) {

        answerDiv.textContent =
            "Please enter a question.";

        return;
    }

    answerDiv.textContent =
        "Thinking...";

    try {

        const response = await fetch(
            `${API_URL}/documents/${selectedDocumentId}/ask`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    question: question
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Question failed"
            );
        }


        // Create answer section

        const formattedAnswer = formatAnswer(data.answer);

        let html = `
            <div class="answer-content">
                <h3>Answer</h3>
                <div class="answer-text">
                    ${formattedAnswer}
                </div>
            </div>
        `;


        // Add sources

        if (data.sources && data.sources.length > 0) {

            html += `
                <div class="sources">

                    <h3>Sources</h3>

                    <ul>
            `;

            data.sources.forEach(source => {

                html += `
                    <li>
                        Chunk ${source.chunk_index}
                        —
                        Relevance:
                        ${source.score.toFixed(3)}
                    </li>
                `;

            });

            html += `
                    </ul>

                </div>
            `;
        }


        answerDiv.innerHTML = html;

    } catch (error) {

        console.error(error);

        answerDiv.textContent =
            `Error: ${error.message}`;
    }
}


// ===============================
// Simple HTML escaping
// ===============================

function formatAnswer(text) {
    const lines = text.split("\n");

    let html = "";
    let inList = false;

    lines.forEach(line => {
        line = line.trim();

        if (!line) {
            if (inList) {
                html += "</ul>";
                inList = false;
            }
            return;
        }

        // Heading
        if (line.startsWith("### ")) {
            if (inList) {
                html += "</ul>";
                inList = false;
            }

            html += `<h4>${escapeHtml(line.substring(4))}</h4>`;
            return;
        }

        // Bullet point
        if (line.startsWith("- ") || line.startsWith("* ")) {
            if (!inList) {
                html += "<ul>";
                inList = true;
            }

            html += `<li>${escapeHtml(line.substring(2))}</li>`;
            return;
        }

        // Numbered list
        if (/^\d+\.\s/.test(line)) {
            if (inList) {
                html += "</ul>";
                inList = false;
            }

            const content = line.replace(/^\d+\.\s/, "");

            html += `<p class="numbered-item">${escapeHtml(content)}</p>`;
            return;
        }

        // Normal paragraph
        if (inList) {
            html += "</ul>";
            inList = false;
        }

        html += `<p>${escapeHtml(line)}</p>`;
    });

    if (inList) {
        html += "</ul>";
    }

    return html;
}

function escapeHtml(text) {

    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ===============================
// Button events
// ===============================

document
    .getElementById("uploadBtn")
    .addEventListener(
        "click",
        uploadDocument
    );

document
    .getElementById("askBtn")
    .addEventListener(
        "click",
        askQuestion
    );


// ===============================
// Load documents on page load
// ===============================

loadDocuments();