// Prompt Injection Detection Script
document.addEventListener('DOMContentLoaded', function() {
  const analyzeBtn = document.getElementById('analyzeBtn');
  const testPrompt = document.getElementById('testPrompt');
  const results = document.getElementById('results');
  const resultsContent = document.getElementById('resultsContent');

  async function analyzePrompt() {
    const prompt = testPrompt.value.trim();
    if (!prompt) {
      alert('Please enter a prompt to analyze');
      return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';

    try {
      const res = await fetch("/api/prompt_injection_detector/score", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ prompt })
      });
      
      const data = await res.json();
      
      results.classList.remove('hidden');
      
      const isInjection = data.is_injection || false;
      const confidence = data.confidence || 0;
      
      resultsContent.innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-lg font-semibold">Detection Result:</span>
            <span class="px-4 py-2 rounded-lg font-bold ${isInjection ? 'bg-red-600' : 'bg-green-600'}">
              ${isInjection ? 'INJECTION DETECTED' : 'SAFE'}
            </span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-gray-300">Confidence:</span>
            <span class="text-white font-medium">${(confidence * 100).toFixed(1)}%</span>
          </div>
          ${data.explanation ? `
            <div class="border-t border-gray-700 pt-4">
              <span class="text-gray-300 block mb-2">Explanation:</span>
              <p class="text-white">${data.explanation}</p>
            </div>
          ` : ''}
        </div>
      `;
    } catch (error) {
      resultsContent.innerHTML = `
        <div class="text-red-400">
          <p>Error analyzing prompt: ${error.message}</p>
        </div>
      `;
      results.classList.remove('hidden');
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = 'Analyze for Injection';
    }
  }

  analyzeBtn.addEventListener('click', analyzePrompt);
  
  testPrompt.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
      analyzePrompt();
    }
  });
});
