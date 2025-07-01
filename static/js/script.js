document.addEventListener('DOMContentLoaded', () => {
    // Get references to all necessary DOM elements
    const uploadForm = document.getElementById('upload-form');
    const pdfFilesInput = document.getElementById('pdf-files');
    const uploadStatus = document.getElementById('upload-status');
    const generateGraphBtn = document.getElementById('generate-graph-btn');
    const graphStatus = document.getElementById('graph-status');
    const uploadedDocsList = document.getElementById('uploaded-docs-list');
    const docCountSpan = document.getElementById('doc-count');
    const chatMessages = document.getElementById('chat-messages');
    const userQuestionInput = document.getElementById('user-question');
    const sendBtn = document.getElementById('send-btn');
    const clearChatBtn = document.getElementById('clear-chat-btn'); // This button now only clears frontend chat display

    // Frontend variables to store data, as backend sessions are not used.
    // This data is transient and will be lost on browser refresh.
    let currentExtractedTriplets = [];
    let currentDocumentText = "";
    let currentUploadedDocName = ""; // Stores the name of the currently uploaded PDF

    // --- Helper Functions ---

    /**
     * Displays a message in the chat area.
     * @param {string} role - 'user' or 'assistant'
     * @param {string} content - The message content.
     */
    function displayMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', role);
        messageDiv.innerHTML = `<div class="message-bubble">${content}</div>`;
        chatMessages.appendChild(messageDiv);
        // Automatically scroll to the bottom of the chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /**
     * Updates the UI to show the name and count of the uploaded document.
     * In this single-PDF context, it shows only one document or none.
     * @param {string} docName - The name of the uploaded document, or empty string if none.
     */
    function updateUploadedDocumentsUI(docName) {
        uploadedDocsList.innerHTML = ''; // Clear any existing list items
        if (docName) {
            const listItem = document.createElement('li');
            listItem.textContent = docName;
            uploadedDocsList.appendChild(listItem);
            docCountSpan.textContent = '1'; // Indicate one document is loaded
        } else {
            docCountSpan.textContent = '0'; // Indicate no documents are loaded
        }
    }

    // --- Initial UI Setup on Page Load ---
    // Since backend sessions are not used, the UI starts in a clean state.
    // No fetches for /get_chat_history or /get_docs_info needed here.
    updateUploadedDocumentsUI(currentUploadedDocName); // Initializes with 0 docs
    generateGraphBtn.style.display = 'none'; // Ensure button is hidden initially

    // --- Event Listeners ---

    // Handles the PDF file upload form submission
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent default form submission and page reload

        uploadStatus.textContent = 'Uploading and processing...';
        graphStatus.textContent = ''; // Clear previous graph status
        generateGraphBtn.style.display = 'none'; // Hide button until processing is complete

        const files = pdfFilesInput.files;
        if (files.length === 0) {
            uploadStatus.textContent = 'Please select at least one PDF file.';
            return; // Stop if no files selected
        }

        // Create FormData object to send file(s)
        const formData = new FormData();
        // For single-PDF logic, append only the first selected file
        formData.append('pdf_files', files[0]);

        try {
            const response = await fetch('/upload_pdf', {
                method: 'POST',
                body: formData, // Send form data with the PDF file
            });
            const data = await response.json(); // Parse the JSON response from backend

            if (response.ok && data.success) { // Check both HTTP status and custom success flag
                uploadStatus.textContent = data.message;
                
                // Store extracted data in frontend variables
                currentExtractedTriplets = data.extracted_triplets || [];
                currentDocumentText = data.document_text || "";
                currentUploadedDocName = data.uploaded_doc_name || "";

                // Display Generate Graph button if triplets were extracted
                if (currentExtractedTriplets.length > 0) {
                    generateGraphBtn.style.display = 'block';
                }
                
                // Update UI with the uploaded document name
                updateUploadedDocumentsUI(currentUploadedDocName);
                chatMessages.innerHTML = ''; // Clear chat history when a new document is loaded
                displayMessage('assistant', `Document "${currentUploadedDocName}" uploaded and processed.`);

            } else {
                // Handle API errors (e.g., 4xx, 5xx) or custom success: false
                const errorMessage = data.message || `Server error: ${response.status} ${response.statusText}`;
                uploadStatus.textContent = `Error: ${errorMessage}`;
                console.error('Upload API error:', data);
                
                // Clear frontend state on error
                currentExtractedTriplets = [];
                currentDocumentText = "";
                currentUploadedDocName = "";
                updateUploadedDocumentsUI('');
            }
        } catch (error) {
            // Handle network errors (e.g., server unreachable)
            uploadStatus.textContent = `Network error: ${error.message}. Please check server and try again.`;
            console.error('Upload fetch error:', error);
            
            // Clear frontend state on network error
            currentExtractedTriplets = [];
            currentDocumentText = "";
            currentUploadedDocName = "";
            updateUploadedDocumentsUI('');
        }
    });

    // Handles the "Generate Graph in Neo4j" button click
    generateGraphBtn.addEventListener('click', async () => {
        graphStatus.textContent = 'Generating graph...';

        // Check if there are triplets to send before making the API call
        if (currentExtractedTriplets.length === 0) {
            graphStatus.textContent = 'Error: No triplets available to generate graph. Please upload a PDF first.';
            return;
        }

        try {
            const response = await fetch('/generate_graph', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                // Send the stored triplets directly in the request body
                body: JSON.stringify({ triplets: currentExtractedTriplets }),
            });
            const data = await response.json(); // Parse the JSON response

            if (response.ok && data.success) {
                graphStatus.textContent = data.message;
                // You can choose to hide the button here if you only allow one graph generation per document upload cycle
                // generateGraphBtn.style.display = 'none';
            } else {
                const errorMessage = data.message || `Server error: ${response.status} ${response.statusText}`;
                graphStatus.textContent = `Error: ${errorMessage}`;
                console.error('Generate Graph API error:', data);
            }
        } catch (error) {
            graphStatus.textContent = `Network error: ${error.message}. Please check server and try again.`;
            console.error('Generate Graph fetch error:', error);
        }
    });

    // Handles the chat message sending via the send button or Enter key
    sendBtn.addEventListener('click', sendMessage);
    userQuestionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    /**
     * Sends the user's question to the backend for RAG processing.
     */
    async function sendMessage() {
        const question = userQuestionInput.value.trim();
        if (question === '') return; // Don't send empty messages

        displayMessage('user', question); // Display user's message immediately
        userQuestionInput.value = ''; // Clear input field

        // Ensure a document has been processed and text is available for RAG
        if (!currentDocumentText) {
            displayMessage('assistant', "Please upload a PDF first to enable question answering.");
            return;
        }

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    document_text: currentDocumentText // Send document text with the question for RAG
                }),
            });
            const data = await response.json();

            if (response.ok && data.success) {
                displayMessage('assistant', data.response);
            } else {
                const errorMessage = data.message || `Server error: ${response.status} ${response.statusText}`;
                displayMessage('assistant', `Error: ${errorMessage}`);
                console.error('Chat API error:', data);
            }
        } catch (error) {
            displayMessage('assistant', `Network error: ${error.message}. Please check server and try again.`);
            console.error('Chat fetch error:', error);
        }
    }

    // Handles the "Clear Chat History" button click (only clears frontend display)
    clearChatBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to clear the chat history from this session?')) {
            chatMessages.innerHTML = ''; // Clear messages from UI
            displayMessage('assistant', 'Chat history cleared.'); // Confirm action in chat
        }
    });
});