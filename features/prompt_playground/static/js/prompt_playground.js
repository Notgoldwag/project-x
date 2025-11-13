/**
 * Multi-Model Prompt Playground
 * Compare and contrast outputs from multiple LLMs
 */

// State Management
let selectedModels = ['gemini-2.0-flash-exp', 'gpt-4-turbo', 'gpt-3.5-turbo'];
let isAnalyzing = false;
let currentResults = null;

// DOM Elements
const systemInstructionEl = document.getElementById('systemInstruction');
const userPromptEl = document.getElementById('userPrompt');
const analyzeButton = document.getElementById('analyzeButton');
const clearButton = document.getElementById('clearButton');
const resultsContainer = document.getElementById('resultsContainer');
const modelCards = document.querySelectorAll('.model-card');

// Initialize Event Listeners
function init() {
    // Model card selection
    modelCards.forEach(card => {
        const model = card.getAttribute('data-model');
        
        // Skip disabled models
        if (model === 'claude-3-opus') {
            return;
        }

        card.addEventListener('click', () => {
            toggleModelSelection(card, model);
        });
    });

    // Analyze button
    analyzeButton.addEventListener('click', handleAnalyze);

    // Clear button
    clearButton.addEventListener('click', clearResults);

    // Load saved state
    loadSavedState();
}

// Toggle model selection
function toggleModelSelection(card, model) {
    card.classList.toggle('selected');

    if (selectedModels.includes(model)) {
        selectedModels = selectedModels.filter(m => m !== model);
    } else {
        selectedModels.push(model);
    }

    // Update button state
    updateAnalyzeButton();
}

// Update analyze button state
function updateAnalyzeButton() {
    const hasPrompt = userPromptEl.value.trim().length > 0;
    const hasModels = selectedModels.length > 0;

    analyzeButton.disabled = !hasPrompt || !hasModels || isAnalyzing;

    if (!hasPrompt) {
        analyzeButton.innerHTML = '<span class="material-icons">psychology</span> Enter a prompt to analyze';
    } else if (!hasModels) {
        analyzeButton.innerHTML = '<span class="material-icons">psychology</span> Select at least one model';
    } else if (isAnalyzing) {
        analyzeButton.innerHTML = '<div class="spinner"></div> Analyzing...';
    } else {
        analyzeButton.innerHTML = '<span class="material-icons">psychology</span> Analyze Across Models';
    }
}

// Handle analyze action
async function handleAnalyze() {
    if (isAnalyzing) return;

    const systemInstruction = systemInstructionEl.value.trim();
    const userPrompt = userPromptEl.value.trim();

    if (!userPrompt) {
        alert('Please enter a user prompt');
        return;
    }

    if (selectedModels.length === 0) {
        alert('Please select at least one model');
        return;
    }

    isAnalyzing = true;
    updateAnalyzeButton();

    // Show loading state
    resultsContainer.innerHTML = `
        <div class="flex flex-col items-center justify-center h-full text-center py-20">
            <div class="w-16 h-16 border-4 border-primary/30 border-t-primary rounded-full animate-spin mb-4"></div>
            <h3 class="text-xl font-semibold text-gray-200 mb-2">Analyzing across ${selectedModels.length} model${selectedModels.length > 1 ? 's' : ''}...</h3>
            <p class="text-gray-400 text-sm">This may take a few moments</p>
        </div>
    `;

    try {
        // Call API to run prompt across models
        const response = await fetch('/playground/api/run_prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                system_instruction: systemInstruction,
                prompt: userPrompt,
                models: selectedModels
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        currentResults = data.results;

        // Display results
        displayResults(data.results, userPrompt);

        // Get meta-analysis
        await getMetaAnalysis(data.results, userPrompt);

        // Save state
        saveState();

    } catch (error) {
        console.error('Error analyzing prompt:', error);
        resultsContainer.innerHTML = `
            <div class="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3">
                <span class="material-icons text-red-400">error</span>
                <div class="flex-1">
                    <div class="font-semibold text-red-400 mb-1">Error</div>
                    <div class="text-sm text-gray-300">Failed to analyze prompt: ${error.message}</div>
                    <div class="text-xs text-gray-500 mt-2">Check the browser console for more details.</div>
                </div>
            </div>
        `;
    } finally {
        isAnalyzing = false;
        updateAnalyzeButton();
    }
}

// Display results
function displayResults(results, originalPrompt) {
    clearButton.classList.remove('hidden');

    let html = '<div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">';

    results.forEach(result => {
        html += createResultCard(result);
    });

    html += '</div>';

    // Add placeholder for meta-analysis
    html += `
        <div id="metaAnalysis" class="acrylic rounded-2xl p-6 border border-primary/30" style="display: none;">
            <div class="flex items-center gap-3 mb-4">
                <span class="material-icons text-primary" style="font-size: 32px;">analytics</span>
                <h3 class="text-xl font-bold text-gray-200">AI Meta-Analysis by Gemini</h3>
            </div>
            <div class="text-center py-8">
                <div class="inline-block w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin mb-3"></div>
                <p class="text-gray-400 text-sm">Generating meta-analysis...</p>
            </div>
        </div>
    `;

    resultsContainer.innerHTML = html;
}

// Create result card HTML
function createResultCard(result) {
    const statusColors = {
        'Success': 'bg-green-500/20 text-green-400 border-green-500/30',
        'Configuration Required': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
        'Error': 'bg-red-500/20 text-red-400 border-red-500/30'
    };
    
    const statusClass = statusColors[result.status] || 'bg-gray-500/20 text-gray-400 border-gray-500/30';

    const modelDisplayNames = {
        'gemini-2.0-flash-exp': 'Gemini 2.0 Flash',
        'gpt-4-turbo': 'GPT-4 Turbo',
        'gpt-3.5-turbo': 'GPT-3.5 Turbo',
        'claude-3-opus': 'Claude 3 Opus'
    };

    const response = result.status === 'Success' ? result.response : 
                    result.status === 'Configuration Required' ? 
                    'This model requires configuration. Please add the necessary API keys to your .env file.' :
                    `Error: ${result.response}`;

    return `
        <div class="acrylic rounded-2xl p-5 border border-white/10 hover:border-primary/30 transition">
            <div class="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
                <h4 class="font-semibold text-gray-200">${modelDisplayNames[result.model] || result.model}</h4>
                <span class="px-2 py-1 text-xs font-medium rounded-lg border ${statusClass}">${result.status}</span>
            </div>
            
            <div class="bg-black/30 rounded-xl p-4 mb-4 font-mono text-sm text-gray-300 max-h-64 overflow-y-auto border border-white/5">
                ${escapeHtml(response).replace(/\n/g, '<br>')}
            </div>
            
            ${result.metadata ? `
                <div class="grid grid-cols-3 gap-3">
                    <div class="bg-white/5 rounded-lg p-3 text-center border border-white/10">
                        <div class="text-xs text-gray-400 mb-1">Latency</div>
                        <div class="text-sm font-bold text-primary">${result.metadata.latency.toFixed(2)}s</div>
                    </div>
                    <div class="bg-white/5 rounded-lg p-3 text-center border border-white/10">
                        <div class="text-xs text-gray-400 mb-1">Tokens</div>
                        <div class="text-sm font-bold text-primary">${result.metadata.tokens || 'N/A'}</div>
                    </div>
                    <div class="bg-white/5 rounded-lg p-3 text-center border border-white/10">
                        <div class="text-xs text-gray-400 mb-1">Cost</div>
                        <div class="text-sm font-bold text-primary">$${result.metadata.cost_estimate ? result.metadata.cost_estimate.toFixed(4) : 'N/A'}</div>
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

// Get meta-analysis from Gemini
async function getMetaAnalysis(results, originalPrompt) {
    const metaAnalysisEl = document.getElementById('metaAnalysis');
    metaAnalysisEl.style.display = 'block';

    try {
        const response = await fetch('/playground/api/analyze_results', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                results: results,
                original_prompt: originalPrompt
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayMetaAnalysis(data.analysis);

    } catch (error) {
        console.error('Error getting meta-analysis:', error);
        metaAnalysisEl.innerHTML = `
            <div class="flex items-center gap-3 mb-4">
                <span class="material-icons text-primary" style="font-size: 32px;">analytics</span>
                <h3 class="text-xl font-bold text-gray-200">AI Meta-Analysis</h3>
            </div>
            <div class="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3">
                <span class="material-icons text-red-400">error</span>
                <div class="text-sm text-gray-300">Failed to generate meta-analysis: ${error.message}</div>
            </div>
        `;
    }
}

// Display meta-analysis
function displayMetaAnalysis(analysis) {
    const metaAnalysisEl = document.getElementById('metaAnalysis');

    const html = `
        <div class="flex items-center gap-3 mb-6">
            <span class="material-icons text-primary" style="font-size: 32px;">analytics</span>
            <h3 class="text-xl font-bold text-gray-200">AI Meta-Analysis by Gemini</h3>
        </div>
        
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
            <div class="bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl p-4 text-center border border-primary/20">
                <div class="text-xs text-gray-400 uppercase tracking-wider mb-2">Clarity</div>
                <div class="text-3xl font-bold text-primary">${analysis.clarity_score}<span class="text-lg text-gray-500">/10</span></div>
            </div>
            <div class="bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl p-4 text-center border border-primary/20">
                <div class="text-xs text-gray-400 uppercase tracking-wider mb-2">Relevance</div>
                <div class="text-3xl font-bold text-primary">${analysis.relevance_score}<span class="text-lg text-gray-500">/10</span></div>
            </div>
            <div class="bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl p-4 text-center border border-primary/20">
                <div class="text-xs text-gray-400 uppercase tracking-wider mb-2">Accuracy</div>
                <div class="text-3xl font-bold text-primary">${analysis.factual_accuracy}<span class="text-lg text-gray-500">/10</span></div>
            </div>
            <div class="bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl p-4 text-center border border-primary/20">
                <div class="text-xs text-gray-400 uppercase tracking-wider mb-2">Reasoning</div>
                <div class="text-3xl font-bold text-primary">${analysis.reasoning_quality}<span class="text-lg text-gray-500">/10</span></div>
            </div>
            <div class="bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl p-4 text-center border border-primary/20">
                <div class="text-xs text-gray-400 uppercase tracking-wider mb-2">Conciseness</div>
                <div class="text-3xl font-bold text-primary">${analysis.conciseness}<span class="text-lg text-gray-500">/10</span></div>
            </div>
        </div>
        
        <div class="bg-black/30 rounded-xl p-5 border border-white/10">
            <h4 class="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Overall Summary</h4>
            <p class="text-gray-300 leading-relaxed">${escapeHtml(analysis.overall_summary)}</p>
        </div>
    `;

    metaAnalysisEl.innerHTML = html;
}

// Clear results
function clearResults() {
    resultsContainer.innerHTML = `
        <div class="flex flex-col items-center justify-center h-full text-center py-20">
            <div class="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <span class="material-icons text-primary" style="font-size: 48px;">psychology</span>
            </div>
            <h3 class="text-xl font-semibold text-gray-300 mb-2">No results yet</h3>
            <p class="text-gray-500 text-sm max-w-md">
                Select your models, enter a prompt, and click "Analyze" to compare AI responses side-by-side
            </p>
        </div>
    `;
    clearButton.classList.add('hidden');
    currentResults = null;
    localStorage.removeItem('playgroundState');
}

// Save state to localStorage
function saveState() {
    const state = {
        systemInstruction: systemInstructionEl.value,
        userPrompt: userPromptEl.value,
        selectedModels: selectedModels,
        results: currentResults,
        timestamp: new Date().toISOString()
    };
    localStorage.setItem('playgroundState', JSON.stringify(state));
}

// Load saved state from localStorage
function loadSavedState() {
    const savedState = localStorage.getItem('playgroundState');
    if (!savedState) return;

    try {
        const state = JSON.parse(savedState);
        
        // Check if state is from today
        const savedDate = new Date(state.timestamp);
        const today = new Date();
        if (savedDate.toDateString() !== today.toDateString()) {
            localStorage.removeItem('playgroundState');
            return;
        }

        // Restore inputs
        if (state.systemInstruction) {
            systemInstructionEl.value = state.systemInstruction;
        }
        if (state.userPrompt) {
            userPromptEl.value = state.userPrompt;
        }

        // Restore model selection
        if (state.selectedModels) {
            selectedModels = state.selectedModels;
            modelCards.forEach(card => {
                const model = card.getAttribute('data-model');
                if (selectedModels.includes(model)) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
            });
        }

        // Restore results if available
        if (state.results && state.results.length > 0) {
            currentResults = state.results;
            displayResults(state.results, state.userPrompt);
        }

    } catch (error) {
        console.error('Error loading saved state:', error);
        localStorage.removeItem('playgroundState');
    }
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-update button state on input
userPromptEl.addEventListener('input', updateAnalyzeButton);
systemInstructionEl.addEventListener('input', () => {
    if (currentResults) {
        saveState();
    }
});

// Initialize the app
init();

console.log('🎮 Multi-Model Prompt Playground initialized');
console.log('Selected models:', selectedModels);
