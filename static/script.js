// DOM Elements
const fileInput = document.getElementById('fileInput');
const fileUploadArea = document.getElementById('fileUploadArea');
const selectedFile = document.getElementById('selectedFile');
const removeFile = document.getElementById('removeFile');
const submitBtn = document.getElementById('submitBtn');
const documentForm = document.getElementById('documentForm');
const progressContainer = document.getElementById('progressContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsSection = document.getElementById('resultsSection');
const summaryContent = document.getElementById('summaryContent');
const clauseAccordion = document.getElementById('clauseAccordion');
const questionInput = document.getElementById('questionInput');
const askQuestion = document.getElementById('askQuestion');
const qaHistory = document.getElementById('qaHistory');

// State Management
let currentDocument = null;
let currentSessionKey = null;
let isProcessing = false;

// Initialize Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    initializeFileUpload();
    initializeFormSubmission();
    initializeQuestionHandler();
    initializeSmoothAnimations();
});

// File Upload Functionality
function initializeFileUpload() {
    // Click to browse files
    fileUploadArea.addEventListener('click', () => {
        if (!isProcessing) {
            fileInput.click();
        }
    });

    // File selection change
    fileInput.addEventListener('change', handleFileSelection);

    // Drag and drop functionality
    fileUploadArea.addEventListener('dragover', handleDragOver);
    fileUploadArea.addEventListener('dragleave', handleDragLeave);
    fileUploadArea.addEventListener('drop', handleFileDrop);

    // Remove file functionality
    removeFile.addEventListener('click', clearSelectedFile);
}

function handleFileSelection(event) {
    const file = event.target.files[0];
    if (file) {
        if (isValidFileType(file)) {
            displaySelectedFile(file);
            enableSubmitButton();
        } else {
            showError('Please select a valid file type: PDF, DOC, DOCX, or TXT');
            clearSelectedFile();
        }
    }
}

function isValidFileType(file) {
    const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    ];
    const allowedExtensions = ['pdf', 'doc', 'docx', 'txt'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    return allowedTypes.includes(file.type) || allowedExtensions.includes(fileExtension);
}

function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
    if (!isProcessing) {
        fileUploadArea.classList.add('drag-over');
    }
}

function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    fileUploadArea.classList.remove('drag-over');
}

function handleFileDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    fileUploadArea.classList.remove('drag-over');
    
    if (isProcessing) return;
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (isValidFileType(file)) {
            // Manually set the file to the input
            const dt = new DataTransfer();
            dt.items.add(file);
            fileInput.files = dt.files;
            
            displaySelectedFile(file);
            enableSubmitButton();
        } else {
            showError('Please select a valid file type: PDF, DOC, DOCX, or TXT');
        }
    }
}

function displaySelectedFile(file) {
    const fileName = selectedFile.querySelector('.file-name');
    const fileSize = (file.size / 1024 / 1024).toFixed(2);
    fileName.textContent = `${file.name} (${fileSize} MB)`;
    
    selectedFile.style.display = 'block';
    selectedFile.classList.add('fade-in');
    
    // Add success state to upload area
    fileUploadArea.classList.add('success-state');
    
    currentDocument = file;
}

function clearSelectedFile() {
    selectedFile.style.display = 'none';
    selectedFile.classList.remove('fade-in');
    fileInput.value = '';
    fileUploadArea.classList.remove('success-state');
    disableSubmitButton();
    currentDocument = null;
    currentSessionKey = null;
    
    // Clear any error states
    fileUploadArea.classList.remove('error-state');
}

function enableSubmitButton() {
    submitBtn.disabled = false;
    submitBtn.classList.add('interactive');
}

function disableSubmitButton() {
    submitBtn.disabled = true;
    submitBtn.classList.remove('interactive');
}

// Form Submission and Processing
function initializeFormSubmission() {
    documentForm.addEventListener('submit', handleFormSubmission);
}

async function handleFormSubmission(event) {
    event.preventDefault();
    
    if (isProcessing || !currentDocument) {
        console.log('Cannot submit: processing =', isProcessing, 'document =', currentDocument);
        return;
    }
    
    isProcessing = true;
    showProgress();
    
    const formData = new FormData();
    formData.append('document', currentDocument);
    
    try {
        // Simulate processing steps for better UX
        await simulateProcessingSteps();
        
        console.log('Sending request to Flask backend...');
        
        // Submit to Flask backend
        const response = await fetch('/', {
            method: 'POST',
            body: formData
        });
        
        console.log('Response status:', response.status);
        
        if (response.ok) {
            const result = await response.json();
            console.log('Analysis result:', result);
            
            // Store session key for Q&A
            if (result.session_key) {
                currentSessionKey = result.session_key;
            }
            
            displayResults(result);
        } else {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            throw new Error(errorData.error || `Server error: ${response.status}`);
        }
    } catch (error) {
        console.error('Error processing document:', error);
        showError(`Failed to process document: ${error.message}`);
        fileUploadArea.classList.add('error-state');
    } finally {
        isProcessing = false;
        hideProgress();
    }
}

async function simulateProcessingSteps() {
    const steps = [
        { progress: 15, text: 'Uploading document...' },
        { progress: 35, text: 'Reading document content...' },
        { progress: 55, text: 'Analyzing legal structure...' },
        { progress: 75, text: 'Extracting key clauses...' },
        { progress: 90, text: 'Generating explanations...' },
        { progress: 100, text: 'Finalizing summary...' }
    ];
    
    for (const step of steps) {
        await new Promise(resolve => setTimeout(resolve, 600));
        updateProgress(step.progress, step.text);
    }
}

function showProgress() {
    progressContainer.style.display = 'block';
    progressContainer.classList.add('fade-in');
    updateProgress(0, 'Initializing...');
    
    // Disable form during processing
    submitBtn.disabled = true;
    fileUploadArea.style.pointerEvents = 'none';
}

function updateProgress(percentage, text) {
    progressFill.style.width = `${percentage}%`;
    progressText.textContent = text;
}

function hideProgress() {
    setTimeout(() => {
        progressContainer.style.display = 'none';
        progressContainer.classList.remove('fade-in');
        
        // Re-enable form
        if (currentDocument) {
            enableSubmitButton();
        }
        fileUploadArea.style.pointerEvents = 'auto';
    }, 1000);
}

// Results Display
function displayResults(data) {
    // Clear any previous results
    summaryContent.innerHTML = '';
    clauseAccordion.innerHTML = '';
    qaHistory.innerHTML = '';
    
    // Show results section with animation
    resultsSection.style.display = 'block';
    resultsSection.classList.add('fade-in');
    
    // Display summary
    if (data.summary) {
        summaryContent.innerHTML = `<p>${data.summary}</p>`;
        animateTextReveal(summaryContent);
    }
    
    // Display clauses
    if (data.clauses && data.clauses.length > 0) {
        generateAccordion(data.clauses);
    } else {
        clauseAccordion.innerHTML = '<p>No specific clauses identified in this document.</p>';
    }
    
    // Show document type and key points if available
    if (data.document_type) {
        console.log('Document type detected:', data.document_type);
    }
    
    // Scroll to results smoothly
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 500);
}

function generateAccordion(clauses) {
    clauseAccordion.innerHTML = '';
    
    clauses.forEach((clause, index) => {
        const accordionItem = createAccordionItem(clause, index);
        clauseAccordion.appendChild(accordionItem);
        
        // Stagger animation
        setTimeout(() => {
            accordionItem.classList.add('fade-in');
        }, index * 100);
    });
}

function createAccordionItem(clause, index) {
    const item = document.createElement('div');
    item.className = 'accordion-item';
    item.innerHTML = `
        <div class="accordion-header clickable" data-index="${index}">
            <div class="accordion-title">${clause.title || `Clause ${index + 1}`}</div>
            <i class="fas fa-chevron-down accordion-icon"></i>
        </div>
        <div class="accordion-content">
            <div class="accordion-body">
                <div style="margin-bottom: 1rem;">
                    <strong style="color: var(--gold);">Original:</strong> 
                    <div style="margin-top: 0.5rem; font-style: italic; opacity: 0.8;">${clause.original}</div>
                </div>
                <div style="margin-bottom: 1rem;">
                    <strong style="color: var(--gold);">Simplified:</strong> 
                    <div style="margin-top: 0.5rem; color: var(--white);">${clause.simplified}</div>
                </div>
                ${clause.explanation ? `
                <div>
                    <strong style="color: var(--gold);">Explanation:</strong> 
                    <div style="margin-top: 0.5rem; color: var(--silver);">${clause.explanation}</div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
    
    // Add click handler for accordion
    const header = item.querySelector('.accordion-header');
    header.addEventListener('click', () => toggleAccordion(header, index));
    
    return item;
}

function toggleAccordion(header, index) {
    const content = header.nextElementSibling;
    const icon = header.querySelector('.accordion-icon');
    const isActive = header.classList.contains('active');
    
    // Close all other accordions
    document.querySelectorAll('.accordion-header.active').forEach(activeHeader => {
        if (activeHeader !== header) {
            activeHeader.classList.remove('active');
            activeHeader.nextElementSibling.classList.remove('active');
            activeHeader.querySelector('.accordion-icon').style.transform = 'rotate(0deg)';
        }
    });
    
    // Toggle current accordion
    if (isActive) {
        header.classList.remove('active');
        content.classList.remove('active');
        icon.style.transform = 'rotate(0deg)';
    } else {
        header.classList.add('active');
        content.classList.add('active');
        icon.style.transform = 'rotate(180deg)';
        
        // Smooth scroll to active accordion
        setTimeout(() => {
            header.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
    }
}

// Q&A Functionality
function initializeQuestionHandler() {
    askQuestion.addEventListener('click', handleQuestionSubmit);
    questionInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleQuestionSubmit();
        }
    });
    
    // Auto-resize and reactive input
    questionInput.addEventListener('input', handleQuestionInput);
}

function handleQuestionInput() {
    const question = questionInput.value.trim();
    
    if (question.length > 0 && currentSessionKey) {
        askQuestion.disabled = false;
        askQuestion.classList.add('interactive');
        questionInput.style.borderColor = 'var(--gold)';
    } else {
        askQuestion.disabled = true;
        askQuestion.classList.remove('interactive');
        questionInput.style.borderColor = 'var(--medium-gray)';
    }
}

async function handleQuestionSubmit() {
    const question = questionInput.value.trim();
    
    if (!question || !currentSessionKey) {
        if (!currentSessionKey) {
            showError('Please upload and analyze a document first');
        }
        return;
    }
    
    // Add question to history immediately
    addQuestionToHistory(question, 'Thinking...');
    questionInput.value = '';
    handleQuestionInput();
    
    try {
        // Send question to backend with session key
        const formData = new FormData();
        formData.append('question', question);
        formData.append('session_key', currentSessionKey);
        
        console.log('Asking question with session key:', currentSessionKey);
        
        const response = await fetch('/ask', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            updateLatestAnswer(result.answer);
        } else {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            throw new Error(errorData.error || 'Failed to get answer');
        }
    } catch (error) {
        console.error('Error asking question:', error);
        updateLatestAnswer(`Sorry, I couldn't process your question: ${error.message}`);
    }
}

function addQuestionToHistory(question, answer) {
    const qaItem = document.createElement('div');
    qaItem.className = 'qa-item';
    qaItem.innerHTML = `
        <div class="question">
            <strong>You:</strong> ${question}
        </div>
        <div class="answer loading">
            <strong>LegalZen:</strong> ${answer}
        </div>
    `;
    
    qaHistory.appendChild(qaItem);
    
    // Scroll to latest question
    setTimeout(() => {
        qaItem.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 100);
}

function updateLatestAnswer(answer) {
    const latestAnswer = qaHistory.querySelector('.qa-item:last-child .answer');
    if (latestAnswer) {
        latestAnswer.classList.remove('loading');
        latestAnswer.innerHTML = `<strong>LegalZen:</strong> ${answer}`;
        animateTextReveal(latestAnswer);
    }
}

// Utility Functions
function animateTextReveal(element) {
    element.style.opacity = '0';
    element.style.transform = 'translateY(10px)';
    
    setTimeout(() => {
        element.style.transition = 'all 0.5s ease';
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
    }, 100);
}

function showError(message) {
    console.error('Error:', message);
    
    // Create temporary error notification
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-notification';
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--error);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        max-width: 400px;
        word-wrap: break-word;
    `;
    errorDiv.textContent = message;
    
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.style.animation = 'slideOutRight 0.3s ease forwards';
        setTimeout(() => {
            if (document.body.contains(errorDiv)) {
                document.body.removeChild(errorDiv);
            }
        }, 300);
    }, 4000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success-notification';
    successDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--success);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        z-index: 10000;
        animation: slideInRight 0.3s ease;
    `;
    successDiv.textContent = message;
    
    document.body.appendChild(successDiv);
    
    setTimeout(() => {
        successDiv.style.animation = 'slideOutRight 0.3s ease forwards';
        setTimeout(() => {
            if (document.body.contains(successDiv)) {
                document.body.removeChild(successDiv);
            }
        }, 300);
    }, 3000);
}

// Smooth Animations and Micro-interactions
function initializeSmoothAnimations() {
    addHoverEffects();
    initializeScrollAnimations();
    initializeTypingIndicator();
}

function addHoverEffects() {
    const premiumElements = document.querySelectorAll('.submit-btn, .ask-btn, .accordion-header');
    
    premiumElements.forEach(element => {
        element.addEventListener('mouseenter', () => {
            if (!element.disabled && !isProcessing) {
                element.classList.add('premium-glow');
            }
        });
        
        element.addEventListener('mouseleave', () => {
            element.classList.remove('premium-glow');
        });
    });
}

function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
            }
        });
    }, observerOptions);
    
    // Observe elements that should animate on scroll
    document.querySelectorAll('.summary-panel, .clauses-panel, .qa-panel').forEach(el => {
        observer.observe(el);
    });
}

function initializeTypingIndicator() {
    questionInput.addEventListener('input', () => {
        const inputLength = questionInput.value.length;
        
        if (inputLength > 0 && currentSessionKey) {
            questionInput.style.boxShadow = '0 0 0 2px rgba(212, 175, 55, 0.2)';
        } else {
            questionInput.style.boxShadow = 'none';
        }
    });
}

// Advanced UI Enhancements
function createRippleEffect(event, element) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(212, 175, 55, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
    `;
    
    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);
    
    setTimeout(() => {
        if (element.contains(ripple)) {
            ripple.remove();
        }
    }, 600);
}

// Add ripple effect to buttons
document.addEventListener('click', (event) => {
    if (event.target.matches('.submit-btn, .ask-btn') && !event.target.disabled) {
        createRippleEffect(event, event.target);
    }
});

// Demo/Testing Functions
function loadDemoDocument() {
    console.log('Loading demo document...');
    
    // Simulate demo document upload
    currentSessionKey = 'demo_session';
    
    fetch('/demo')
        .then(response => response.json())
        .then(data => {
            console.log('Demo data loaded:', data);
            displayResults(data);
            showSuccess('Demo document loaded successfully!');
        })
        .catch(error => {
            console.error('Error loading demo:', error);
            showError('Failed to load demo document');
        });
}

// Debug function to check backend connectivity
async function testBackendConnection() {
    try {
        const response = await fetch('/health');
        if (response.ok) {
            const health = await response.json();
            console.log('Backend health:', health);
            showSuccess('Backend connection successful');
        } else {
            throw new Error(`Health check failed: ${response.status}`);
        }
    } catch (error) {
        console.error('Backend connection error:', error);
        showError('Cannot connect to backend server');
    }
}

// Keyboard Shortcuts
document.addEventListener('keydown', (event) => {
    // Ctrl/Cmd + U to upload file
    if ((event.ctrlKey || event.metaKey) && event.key === 'u') {
        event.preventDefault();
        if (!isProcessing) {
            fileInput.click();
        }
    }
    
    // Escape to clear file
    if (event.key === 'Escape' && currentDocument) {
        clearSelectedFile();
    }
    
    // Ctrl/Cmd + Enter to submit form
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter' && currentDocument && !isProcessing) {
        documentForm.dispatchEvent(new Event('submit'));
    }
    
    // D for demo (development shortcut)
    if (event.key === 'd' && event.ctrlKey && event.shiftKey) {
        event.preventDefault();
        loadDemoDocument();
    }
    
    // T for backend test (development shortcut)
    if (event.key === 't' && event.ctrlKey && event.shiftKey) {
        event.preventDefault();
        testBackendConnection();
    }
});


const advancedAnimations = `
@keyframes ripple {
    from { transform: scale(0); opacity: 1; }
    to { transform: scale(2); opacity: 0; }
}

@keyframes slideInRight {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

@keyframes slideOutRight {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
}

@keyframes textReveal {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

.text-reveal {
    animation: textReveal 0.6s ease forwards;
}

.bounce-in {
    animation: bounceIn 0.5s ease;
}

@keyframes bounceIn {
    0% { transform: scale(0.3); opacity: 0; }
    50% { transform: scale(1.05); opacity: 0.8; }
    100% { transform: scale(1); opacity: 1; }
}

.processing-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
}
`;

 const styleSheet = document.createElement('style');
styleSheet.textContent = advancedAnimations;
document.head.appendChild(styleSheet);

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

 function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = event.target.dataset.tooltip;
    tooltip.style.cssText = `
        position: absolute;
        background: var(--black);
        color: var(--gold);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-size: 0.8rem;
        z-index: 10000;
        pointer-events: none;
        opacity: 0;
        transform: translateY(10px);
        transition: all 0.3s ease;
        border: 1px solid var(--gold);
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = event.target.getBoundingClientRect();
    tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
    
    setTimeout(() => {
        tooltip.style.opacity = '1';
        tooltip.style.transform = 'translateY(0)';
    }, 10);
    
    event.target._tooltip = tooltip;
}

function hideTooltip(event) {
    if (event.target._tooltip) {
        event.target._tooltip.remove();
        delete event.target._tooltip;
    }
}

 document.addEventListener('DOMContentLoaded', () => {
    initializeTooltips();
    
     setTimeout(() => {
        testBackendConnection();
    }, 1000);
    
     setTimeout(() => {
        const heroSection = document.querySelector('.hero-section');
        const uploadSection = document.querySelector('.upload-section');
        
        if (heroSection) {
            heroSection.style.animationDelay = '0.1s';
        }
        if (uploadSection) {
            uploadSection.style.animationDelay = '0.3s';
        }
    }, 100);
});

 
window.LegalZenUI = {
    displayResults,
    showProgress,
    hideProgress,
    updateProgress,
    loadDemoDocument,
    testBackendConnection,
    showError,
    showSuccess,
    currentDocument: () => currentDocument,
    currentSessionKey: () => currentSessionKey
};