// DOM elements
const userQueryInput = document.getElementById('userQuery');
const generateBtn = document.getElementById('generateBtn');
const resultCard = document.getElementById('resultCard');
const loadingCard = document.getElementById('loadingCard');
const errorCard = document.getElementById('errorCard');
const explanationText = document.getElementById('explanationText');
const recommendationsList = document.getElementById('recommendationsList');
const searchDetails = document.getElementById('searchDetails');
const craigslistLinks = document.getElementById('craigslistLinks');
const copyBtn = document.getElementById('copyBtn');
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');
const exampleTags = document.querySelectorAll('.example-tag');
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');

// State
let currentQuery = '';
let currentTheme = localStorage.getItem('theme') || 'light';

// Event listeners
generateBtn.addEventListener('click', handleGenerateClick);
userQueryInput.addEventListener('keydown', handleKeyDown);
copyBtn.addEventListener('click', handleCopyClick);
retryBtn.addEventListener('click', handleRetryClick);
themeToggle.addEventListener('click', toggleTheme);

// Example tag click handlers
exampleTags.forEach(tag => {
    tag.addEventListener('click', () => {
        const example = tag.getAttribute('data-example');
        userQueryInput.value = example;
        userQueryInput.focus();
    });
});

// Handle generate button click
async function handleGenerateClick() {
    const query = userQueryInput.value.trim();
    
    if (!query) {
        showError('Please enter a description of what you\'re looking for.');
        return;
    }
    
    currentQuery = query;
    await generateCraigslistLink(query);
}

// Handle Enter key in textarea
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleGenerateClick();
    }
}

// Handle copy button click
async function handleCopyClick() {
    try {
        // Get all Craigslist links
        const links = document.querySelectorAll('.craigslist-link');
        if (links.length === 0) {
            showError('No links to copy.');
            return;
        }
        
        // Create text with all links
        const linksText = Array.from(links).map(link => 
            `${link.textContent.trim()}: ${link.href}`
        ).join('\n\n');
        
        await navigator.clipboard.writeText(linksText);
        
        // Visual feedback
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i>';
        copyBtn.style.background = '#28a745';
        copyBtn.style.color = 'white';
        copyBtn.style.borderColor = '#28a745';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
            copyBtn.style.color = '';
            copyBtn.style.borderColor = '';
        }, 2000);
        
    } catch (err) {
        console.error('Failed to copy: ', err);
        showError('Failed to copy links to clipboard.');
    }
}

// Handle retry button click
function handleRetryClick() {
    hideAllCards();
    showSearchCard();
    userQueryInput.focus();
}

// Main function to generate Craigslist link
async function generateCraigslistLink(query) {
    try {
        // Show loading state
        hideAllCards();
        showLoadingCard();
        
        // Disable generate button
        generateBtn.disabled = true;
        
        // Make API call
        const response = await fetch('/api/generate-link', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate link');
        }
        
        if (!data.success) {
            throw new Error(data.error || 'Unknown error occurred');
        }
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An unexpected error occurred. Please try again.');
    } finally {
        // Re-enable generate button
        generateBtn.disabled = false;
    }
}

// Display results in the UI
function displayResults(data) {
    // Hide loading, show results
    hideAllCards();
    showResultCard();
    
    // Update explanation text
    explanationText.textContent = data.explanation || 
        `Based on your request for "${data.query}", here are our recommendations:`;
    
    // Update recommendations list
    updateRecommendationsList(data.recommendations);
    
    // Update search details
    updateSearchDetails(data);
    
    // Update Craigslist links
    console.log('Received data:', data); // Debug logging
    updateCraigslistLinks(data.craigslist_links || []);
    
    // Scroll to results
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Update recommendations list
function updateRecommendationsList(recommendations) {
    recommendationsList.innerHTML = '';
    
    if (recommendations && recommendations.length > 0) {
        recommendations.forEach(item => {
            const itemElement = document.createElement('span');
            itemElement.className = 'recommendation-item';
            itemElement.textContent = item;
            recommendationsList.appendChild(itemElement);
        });
    } else {
        const noRecsElement = document.createElement('span');
        noRecsElement.className = 'recommendation-item';
        noRecsElement.textContent = 'General search';
        noRecsElement.style.background = '#f8f9fa';
        noRecsElement.style.color = '#6c757d';
        recommendationsList.appendChild(noRecsElement);
    }
}

// Update search details
function updateSearchDetails(data) {
    searchDetails.innerHTML = '';
    
    const details = [];
    
    if (data.city && data.city !== 'sfbay') {
        details.push(`Location: ${data.city.toUpperCase()}`);
    }
    
    if (data.zip_code) {
        details.push(`Zip Code: ${data.zip_code}`);
    }
    
    if (data.radius) {
        details.push(`Radius: ${data.radius} miles`);
    }
    
    if (data.min_price || data.max_price) {
        let priceText = 'Price: ';
        if (data.min_price && data.max_price) {
            priceText += `$${data.min_price} - $${data.max_price}`;
        } else if (data.min_price) {
            priceText += `$${data.min_price}+`;
        } else if (data.max_price) {
            priceText += `Up to $${data.max_price}`;
        }
        details.push(priceText);
    }
    
    if (details.length > 0) {
        details.forEach(detail => {
            const detailElement = document.createElement('span');
            detailElement.className = 'search-detail-item';
            detailElement.textContent = detail;
            searchDetails.appendChild(detailElement);
        });
    } else {
        const noDetailsElement = document.createElement('span');
        noDetailsElement.className = 'search-detail-item';
        noDetailsElement.textContent = 'General search area';
        noDetailsElement.style.background = '#f8f9fa';
        noDetailsElement.style.color = '#6c757d';
        searchDetails.appendChild(noDetailsElement);
    }
}

// Update Craigslist links
function updateCraigslistLinks(links) {
    craigslistLinks.innerHTML = '';
    
    if (links && links.length > 0) {
        links.forEach(linkData => {
            const linkContainer = document.createElement('div');
            linkContainer.className = 'individual-link-container';
            
            const linkElement = document.createElement('a');
            linkElement.href = linkData.url;
            linkElement.target = '_blank';
            linkElement.className = 'craigslist-link';
            linkElement.innerHTML = `
                <i class="fas fa-external-link-alt"></i>
                Search for "${linkData.item}"
            `;
            
            linkContainer.appendChild(linkElement);
            craigslistLinks.appendChild(linkContainer);
        });
    } else {
        const noLinksElement = document.createElement('p');
        noLinksElement.className = 'no-links';
        noLinksElement.textContent = 'No search links generated';
        noLinksElement.style.color = '#6c757d';
        noLinksElement.style.textAlign = 'center';
        craigslistLinks.appendChild(noLinksElement);
    }
}

// Show error message
function showError(message) {
    hideAllCards();
    showErrorCard();
    errorMessage.textContent = message;
}

// Card visibility functions
function hideAllCards() {
    resultCard.classList.add('hidden');
    loadingCard.classList.add('hidden');
    errorCard.classList.add('hidden');
}

function showSearchCard() {
    // Search card is always visible, just ensure others are hidden
    hideAllCards();
}

function showResultCard() {
    resultCard.classList.remove('hidden');
}

function showLoadingCard() {
    loadingCard.classList.remove('hidden');
}

function showErrorCard() {
    errorCard.classList.remove('hidden');
}

// Utility function to format price
function formatPrice(price) {
    if (!price) return '';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(price);
}

// Theme management
function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', currentTheme);
    applyTheme();
}

function applyTheme() {
    document.body.className = currentTheme;
    
    // Update icon
    if (currentTheme === 'dark') {
        themeIcon.className = 'fas fa-sun';
        themeToggle.title = 'Switch to light theme';
    } else {
        themeIcon.className = 'fas fa-moon';
        themeToggle.title = 'Switch to dark theme';
    }
}

// Add some visual polish - focus input on page load
document.addEventListener('DOMContentLoaded', () => {
    // Apply saved theme
    applyTheme();
    
    userQueryInput.focus();
    
    // Add subtle animation to the search card
    const searchCard = document.querySelector('.search-card');
    searchCard.style.opacity = '0';
    searchCard.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        searchCard.style.transition = 'all 0.6s ease';
        searchCard.style.opacity = '1';
        searchCard.style.transform = 'translateY(0)';
    }, 100);
});

// Add loading state to generate button
function setButtonLoading(loading) {
    if (loading) {
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        generateBtn.disabled = true;
    } else {
        generateBtn.innerHTML = '<i class="fas fa-magic"></i> Generate Link';
        generateBtn.disabled = false;
    }
}

// Add some keyboard shortcuts
document.addEventListener('keydown', (event) => {
    // Ctrl/Cmd + Enter to generate
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        event.preventDefault();
        handleGenerateClick();
    }
    
    // Escape to clear and focus input
    if (event.key === 'Escape') {
        userQueryInput.value = '';
        userQueryInput.focus();
        hideAllCards();
        showSearchCard();
    }
});

// Add some helpful tooltips and accessibility
document.addEventListener('DOMContentLoaded', () => {
    // Add ARIA labels
    userQueryInput.setAttribute('aria-label', 'Describe what you\'re looking for on Craigslist');
    generateBtn.setAttribute('aria-label', 'Generate Craigslist search link');
    copyBtn.setAttribute('aria-label', 'Copy Craigslist link to clipboard');
    
    // Add helpful hints
    userQueryInput.setAttribute('title', 'Describe what you want to find on Craigslist (e.g., "reliable car under $10,000")');
    
    // Add example suggestions on focus
    userQueryInput.addEventListener('focus', () => {
        if (!userQueryInput.value) {
            userQueryInput.placeholder = 'e.g., "I want a reliable car under $10,000" or "cheap laptop for coding under $500"';
        }
    });
    
    userQueryInput.addEventListener('blur', () => {
        if (!userQueryInput.value) {
            userQueryInput.placeholder = 'e.g., "I want a reliable car under $10,000" or "cheap laptop for coding under $500"';
        }
    });
});
