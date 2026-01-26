/**
 * Upload Zone JavaScript for AJAX file handling.
 *
 * Task 6.2: Implement upload zone JavaScript for AJAX file handling
 * Requirements: 1.1, 1.4, 1.6, 8.1
 *
 * Handles:
 * - Drag-and-drop events with visual feedback
 * - Client-side file type validation before upload
 * - AJAX file submission with progress indication
 * - Error display and retry functionality
 */

(function() {
    'use strict';

    // Allowed file types for validation
    const ALLOWED_TYPES = [
        'application/pdf',
        'image/jpeg',
        'image/png'
    ];

    const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];

    // Maximum file size (10MB)
    const MAX_FILE_SIZE = 10 * 1024 * 1024;

    // DOM element references (populated on DOMContentLoaded)
    let uploadZone;
    let fileInput;
    let documentTypeSelect;
    let uploadForm;
    let submitButton;
    let loadingIndicator;
    let loadingText;
    let errorMessage;
    let errorText;
    let retryButton;
    let selectedFileDisplay;
    let selectedFileName;
    let clearFileButton;
    let noResults;
    let resultsContent;
    let successMessage;
    let warningsArea;
    let extractedFields;
    let clearResultsButton;

    // Current state
    let currentFile = null;
    let isUploading = false;

    // Accumulated extraction results (persisted across uploads)
    let extractedData = {
        passport: null,
        g28: null
    };

    /**
     * Initialize all DOM element references.
     */
    function initElements() {
        uploadZone = document.getElementById('upload-zone');
        fileInput = document.getElementById('file');
        documentTypeSelect = document.getElementById('document_type');
        uploadForm = document.getElementById('upload-form');
        submitButton = document.getElementById('submit-btn');
        loadingIndicator = document.getElementById('loading-indicator');
        loadingText = document.getElementById('loading-text');
        errorMessage = document.getElementById('error-message');
        errorText = document.getElementById('error-text');
        retryButton = document.getElementById('retry-btn');
        selectedFileDisplay = document.getElementById('selected-file');
        selectedFileName = document.getElementById('selected-file-name');
        clearFileButton = document.getElementById('clear-file');
        noResults = document.getElementById('no-results');
        resultsContent = document.getElementById('results-content');
        successMessage = document.getElementById('success-message');
        warningsArea = document.getElementById('warnings-area');
        extractedFields = document.getElementById('extracted-fields');
        clearResultsButton = document.getElementById('clear-results-btn');
    }

    /**
     * Set up all event listeners.
     */
    function initEventListeners() {
        // Drag and drop events on upload zone
        uploadZone.addEventListener('dragover', handleDragOver);
        uploadZone.addEventListener('dragleave', handleDragLeave);
        uploadZone.addEventListener('drop', handleDrop);
        uploadZone.addEventListener('click', handleZoneClick);
        uploadZone.addEventListener('keydown', handleZoneKeydown);

        // File input change
        fileInput.addEventListener('change', handleFileSelect);

        // Document type change
        documentTypeSelect.addEventListener('change', updateSubmitButton);

        // Form submission
        uploadForm.addEventListener('submit', handleSubmit);

        // Clear file button
        if (clearFileButton) {
            clearFileButton.addEventListener('click', handleClearFile);
        }

        // Retry button
        if (retryButton) {
            retryButton.addEventListener('click', handleRetry);
        }

        // Clear results button
        if (clearResultsButton) {
            clearResultsButton.addEventListener('click', handleClearResults);
        }

        // Prevent default drag behaviors on the whole document
        document.addEventListener('dragover', function(e) {
            e.preventDefault();
        });
        document.addEventListener('drop', function(e) {
            e.preventDefault();
        });
    }

    /**
     * Handle dragover event - show visual feedback.
     * @param {DragEvent} e
     */
    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.add('drag-over');
    }

    /**
     * Handle dragleave event - remove visual feedback.
     * @param {DragEvent} e
     */
    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.remove('drag-over');
    }

    /**
     * Handle drop event - process dropped file.
     * @param {DragEvent} e
     */
    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        uploadZone.classList.remove('drag-over');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            processFile(files[0]);
        }
    }

    /**
     * Handle click on upload zone - trigger file input.
     * @param {MouseEvent} e
     */
    function handleZoneClick(e) {
        // Don't trigger if clicking on the clear button
        if (e.target === clearFileButton || clearFileButton.contains(e.target)) {
            return;
        }
        fileInput.click();
    }

    /**
     * Handle keyboard interaction on upload zone.
     * @param {KeyboardEvent} e
     */
    function handleZoneKeydown(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            fileInput.click();
        }
    }

    /**
     * Handle file input change event.
     * @param {Event} e
     */
    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            processFile(files[0]);
        }
    }

    /**
     * Process a selected file - validate and update UI.
     * @param {File} file
     */
    function processFile(file) {
        // Clear any previous errors
        hideError();

        // Validate file type
        if (!validateFileType(file)) {
            showError('Unsupported file format. Supported: PDF, JPEG, PNG');
            return;
        }

        // Validate file size
        if (!validateFileSize(file)) {
            showError('File size exceeds maximum allowed (10MB)');
            return;
        }

        // Store the file and update UI
        currentFile = file;
        updateFileDisplay(file);
        updateSubmitButton();
    }

    /**
     * Validate file type against allowed types.
     * @param {File} file
     * @returns {boolean}
     */
    function validateFileType(file) {
        // Check MIME type
        if (ALLOWED_TYPES.includes(file.type)) {
            return true;
        }

        // Fallback to extension check
        const filename = file.name.toLowerCase();
        return ALLOWED_EXTENSIONS.some(ext => filename.endsWith(ext));
    }

    /**
     * Validate file size.
     * @param {File} file
     * @returns {boolean}
     */
    function validateFileSize(file) {
        return file.size <= MAX_FILE_SIZE;
    }

    /**
     * Update the file display area with selected file info.
     * @param {File} file
     */
    function updateFileDisplay(file) {
        if (selectedFileName && selectedFileDisplay) {
            selectedFileName.textContent = file.name;
            selectedFileDisplay.classList.remove('d-none');
        }

        // Also update the hidden file input with the file
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
    }

    /**
     * Clear the selected file.
     * @param {Event} e
     */
    function handleClearFile(e) {
        e.preventDefault();
        e.stopPropagation();
        clearSelectedFile();
    }

    /**
     * Clear the selected file state and UI.
     */
    function clearSelectedFile() {
        currentFile = null;
        fileInput.value = '';
        if (selectedFileDisplay) {
            selectedFileDisplay.classList.add('d-none');
        }
        if (selectedFileName) {
            selectedFileName.textContent = '';
        }
        updateSubmitButton();
    }

    /**
     * Update submit button enabled state.
     */
    function updateSubmitButton() {
        const hasFile = currentFile !== null || (fileInput.files && fileInput.files.length > 0);
        const hasDocType = documentTypeSelect.value !== '';

        submitButton.disabled = !hasFile || !hasDocType || isUploading;
    }

    /**
     * Handle form submission via AJAX.
     * @param {Event} e
     */
    function handleSubmit(e) {
        e.preventDefault();

        if (isUploading) {
            return;
        }

        // Validate before submission
        const docType = documentTypeSelect.value;
        if (!docType) {
            showError('Please select a document type before uploading');
            return;
        }

        const file = currentFile || (fileInput.files && fileInput.files[0]);
        if (!file) {
            showError('Please select a file to upload');
            return;
        }

        // Start upload
        uploadFile(file, docType);
    }

    /**
     * Upload file via AJAX fetch API.
     * @param {File} file
     * @param {string} documentType
     */
    async function uploadFile(file, documentType) {
        isUploading = true;
        showLoading('Uploading and processing document...');
        hideError();
        updateSubmitButton();
        uploadZone.classList.add('uploading');

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('document_type', documentType);

            // Get CSRF token from window global
            const csrfToken = window.CSRF_TOKEN;

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                handleUploadSuccess(data);
            } else {
                handleUploadError(data.error || 'Upload failed', data.error_code);
            }

        } catch (error) {
            console.error('Upload error:', error);
            handleUploadError('Network error occurred. Please check your connection and try again.', 'NETWORK_ERROR');
        } finally {
            isUploading = false;
            hideLoading();
            updateSubmitButton();
            uploadZone.classList.remove('uploading');
        }
    }

    /**
     * Handle successful upload response.
     * @param {Object} data - Response data from server
     */
    function handleUploadSuccess(data) {
        // Show success message
        if (successMessage) {
            successMessage.classList.remove('d-none');
        }

        // Display warnings if any
        displayWarnings(data.warnings || []);

        // Store extracted data by document type (accumulate, don't replace)
        const docType = data.document_type;
        if (docType === 'passport' || docType === 'g28') {
            extractedData[docType] = data.extracted_fields || {};
        }

        // Display all accumulated extracted fields
        displayAllExtractedFields();

        // Show results area, hide no-results placeholder
        if (noResults) {
            noResults.classList.add('d-none');
        }
        if (resultsContent) {
            resultsContent.classList.remove('d-none');
        }

        // Clear the file selection for next upload
        clearSelectedFile();
    }

    /**
     * Handle upload error response.
     * @param {string} message - Error message
     * @param {string} errorCode - Error code
     */
    function handleUploadError(message, errorCode) {
        showError(message);

        // If it's a network error, show retry more prominently
        if (errorCode === 'NETWORK_ERROR') {
            if (retryButton) {
                retryButton.classList.remove('d-none');
            }
        }
    }

    /**
     * Handle retry button click.
     * @param {Event} e
     */
    function handleRetry(e) {
        e.preventDefault();
        hideError();

        // If there's still a file and document type, resubmit
        const docType = documentTypeSelect.value;
        const file = currentFile || (fileInput.files && fileInput.files[0]);

        if (file && docType) {
            uploadFile(file, docType);
        }
    }

    /**
     * Show loading indicator.
     * @param {string} message
     */
    function showLoading(message) {
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
            loadingIndicator.classList.add('show');
        }
        if (loadingText) {
            loadingText.textContent = message;
        }
    }

    /**
     * Hide loading indicator.
     */
    function hideLoading() {
        if (loadingIndicator) {
            loadingIndicator.classList.add('d-none');
            loadingIndicator.classList.remove('show');
        }
    }

    /**
     * Show error message.
     * @param {string} message
     */
    function showError(message) {
        if (errorMessage && errorText) {
            errorText.textContent = message;
            errorMessage.classList.add('show');
            errorMessage.classList.remove('d-none');
        }
    }

    /**
     * Hide error message.
     */
    function hideError() {
        if (errorMessage) {
            errorMessage.classList.remove('show');
            errorMessage.classList.add('d-none');
        }
    }

    /**
     * Display warning messages.
     * @param {Array} warnings
     */
    function displayWarnings(warnings) {
        if (!warningsArea) return;

        warningsArea.innerHTML = '';

        if (warnings.length === 0) {
            warningsArea.classList.add('d-none');
            return;
        }

        warningsArea.classList.remove('d-none');

        warnings.forEach(function(warning) {
            const div = document.createElement('div');
            div.className = 'alert alert-warning';
            div.textContent = warning;
            warningsArea.appendChild(div);
        });
    }

    /**
     * Display all accumulated extracted fields (both passport and G-28).
     */
    function displayAllExtractedFields() {
        if (!extractedFields) return;

        // Clear display
        extractedFields.innerHTML = '';

        // Display passport data if available
        if (extractedData.passport && Object.keys(extractedData.passport).length > 0) {
            displayExtractedFieldsSection(extractedData.passport, 'passport');
        }

        // Display G-28 data if available
        if (extractedData.g28 && Object.keys(extractedData.g28).length > 0) {
            displayExtractedFieldsSection(extractedData.g28, 'g28');
        }
    }

    /**
     * Display extracted fields for a single document type section.
     * @param {Object} fields - Extracted fields object
     * @param {string} documentType - Type of document
     */
    function displayExtractedFieldsSection(fields, documentType) {
        if (!extractedFields) return;

        // Create section container
        const section = document.createElement('div');
        section.className = 'mb-4';
        section.id = 'section-' + documentType;

        // Create header
        const header = document.createElement('h6');
        header.className = 'text-muted mb-3';
        header.textContent = documentType === 'passport' ? 'Passport Data' : 'G-28 Form Data';
        section.appendChild(header);

        // Create table for fields
        const table = document.createElement('table');
        table.className = 'table table-sm table-bordered';

        const tbody = document.createElement('tbody');

        // Field name mappings for display
        const fieldLabels = {
            'applicant_surname': 'Last Name',
            'applicant_given_names': 'First Name',
            'applicant_dob': 'Date of Birth',
            'applicant_sex': 'Sex',
            'passport_number': 'Passport Number',
            'nationality': 'Nationality',
            'passport_expiry': 'Passport Expiry',
            'a_number': 'A-Number',
            'attorney_surname': 'Attorney Last Name',
            'attorney_given_names': 'Attorney First Name',
            'attorney_email': 'Attorney Email',
            'attorney_phone': 'Attorney Phone'
        };

        for (const [fieldId, fieldData] of Object.entries(fields)) {
            const row = document.createElement('tr');

            const labelCell = document.createElement('td');
            labelCell.className = 'fw-semibold';
            labelCell.textContent = fieldLabels[fieldId] || fieldId;

            const valueCell = document.createElement('td');
            const value = typeof fieldData === 'object' ? fieldData.value : fieldData;
            valueCell.textContent = value || '-';

            // Add confidence badge if available
            if (typeof fieldData === 'object' && fieldData.confidence !== null && fieldData.confidence !== undefined) {
                const confidence = (fieldData.confidence * 100).toFixed(0);
                const badge = document.createElement('span');
                badge.className = 'badge ms-2 ' + getConfidenceBadgeClass(fieldData.confidence);
                badge.textContent = confidence + '%';
                valueCell.appendChild(badge);
            }

            row.appendChild(labelCell);
            row.appendChild(valueCell);
            tbody.appendChild(row);
        }

        table.appendChild(tbody);
        section.appendChild(table);
        extractedFields.appendChild(section);
    }

    /**
     * Get Bootstrap badge class based on confidence level.
     * @param {number} confidence
     * @returns {string}
     */
    function getConfidenceBadgeClass(confidence) {
        if (confidence >= 0.9) return 'bg-success';
        if (confidence >= 0.7) return 'bg-warning text-dark';
        return 'bg-danger';
    }

    /**
     * Handle clear results button click.
     * @param {Event} e
     */
    function handleClearResults(e) {
        e.preventDefault();
        clearResults();
    }

    /**
     * Clear all results from the display.
     */
    function clearResults() {
        // Clear accumulated data
        extractedData = {
            passport: null,
            g28: null
        };

        // Hide results content
        if (resultsContent) {
            resultsContent.classList.add('d-none');
        }

        // Show no-results placeholder
        if (noResults) {
            noResults.classList.remove('d-none');
        }

        // Hide success message
        if (successMessage) {
            successMessage.classList.add('d-none');
        }

        // Clear warnings
        if (warningsArea) {
            warningsArea.innerHTML = '';
            warningsArea.classList.add('d-none');
        }

        // Clear extracted fields
        if (extractedFields) {
            extractedFields.innerHTML = '';
        }

        // Optional: call clear endpoint
        fetch('/clear', {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.CSRF_TOKEN
            }
        }).catch(function(err) {
            console.log('Clear request failed:', err);
        });
    }

    /**
     * Initialize the upload functionality when DOM is ready.
     */
    function init() {
        initElements();

        // Check if required elements exist
        if (!uploadZone || !fileInput || !uploadForm) {
            console.warn('Upload.js: Required elements not found');
            return;
        }

        initEventListeners();
        updateSubmitButton();

        console.log('Upload.js initialized');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
