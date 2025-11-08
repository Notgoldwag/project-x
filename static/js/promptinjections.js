// Prompt Injection Protection Dashboard JavaScript

(function() {
  'use strict';

  // State management
  const state = {
    protectionLevel: 'basic',
    blockedKeywords: ['ignore', 'override', 'bypass', 'forget', 'system'],
    realTimeMonitoring: true,
    autoBlock: true,
    emailNotifications: false,
    detailedLogging: true,
    stats: {
      threatsBlocked: 247,
      successRate: 99.8,
      avgResponseTime: 1.2
    }
  };

  // DOM elements
  const elements = {
    protectionLevelInputs: document.querySelectorAll('input[name="protectionLevel"]'),
    testPromptTextarea: document.querySelector('textarea'),
    analyzeBtn: document.querySelector('button:has(+ button)'),
    clearBtn: document.querySelector('button:last-of-type'),
    keywordInput: document.querySelector('input[placeholder="Add keyword..."]'),
    addKeywordBtn: document.querySelector('button:contains("Add")'),
    keywordTags: null, // Will be set after DOM is ready
    settingsCheckboxes: document.querySelectorAll('input[type="checkbox"]')
  };

  // Initialize the dashboard
  function init() {
    setupEventListeners();
    updateUI();
    simulateRealTimeData();
  }

  // Event listeners
  function setupEventListeners() {
    // Protection level change
    elements.protectionLevelInputs.forEach(input => {
      input.addEventListener('change', handleProtectionLevelChange);
    });

    // Test prompt analysis
    if (elements.analyzeBtn) {
      elements.analyzeBtn.addEventListener('click', analyzePrompt);
    }

    if (elements.clearBtn) {
      elements.clearBtn.addEventListener('click', clearTestPrompt);
    }

    // Keyword management
    if (elements.keywordInput) {
      elements.keywordInput.addEventListener('keypress', handleKeywordInput);
    }

    // Settings checkboxes
    elements.settingsCheckboxes.forEach((checkbox, index) => {
      checkbox.addEventListener('change', handleSettingChange);
    });
  }

  // Handle protection level change
  function handleProtectionLevelChange(event) {
    state.protectionLevel = event.target.value;
    console.log(`Protection level changed to: ${state.protectionLevel}`);
    
    // Update UI to reflect new protection level
    updateProtectionLevelUI();
  }

  // Update protection level UI
  function updateProtectionLevelUI() {
    const levelConfig = {
      basic: { color: 'text-blue-400', icon: 'shield_outline' },
      advanced: { color: 'text-yellow-400', icon: 'verified_user' },
      strict: { color: 'text-red-400', icon: 'gpp_good' }
    };

    // You can add visual feedback here
    console.log(`UI updated for ${state.protectionLevel} protection level`);
  }

  // Analyze test prompt
  function analyzePrompt() {
    const prompt = elements.testPromptTextarea?.value.trim();
    if (!prompt) {
      alert('Please enter a prompt to analyze');
      return;
    }

    const analysis = performPromptAnalysis(prompt);
    displayAnalysisResults(analysis);
  }

  // Perform actual prompt analysis
  function performPromptAnalysis(prompt) {
    const analysis = {
      prompt: prompt,
      riskLevel: 'low',
      threats: [],
      confidence: 0,
      timestamp: new Date()
    };

    // Check for blocked keywords
    state.blockedKeywords.forEach(keyword => {
      if (prompt.toLowerCase().includes(keyword.toLowerCase())) {
        analysis.threats.push({
          type: 'Blocked Keyword',
          pattern: keyword,
          severity: 'high'
        });
        analysis.riskLevel = 'high';
      }
    });

    // Check for common injection patterns
    const injectionPatterns = [
      { 
        pattern: /ignore\s+(previous|all)\s+instructions?/i, 
        name: 'Ignore instructions',
        severity: 'critical'
      },
      { 
        pattern: /forget\s+(everything|all|previous)/i, 
        name: 'Memory reset attempt',
        severity: 'high'
      },
      { 
        pattern: /(you\s+are\s+now|act\s+as\s+if)/i, 
        name: 'Role override attempt',
        severity: 'high'
      },
      { 
        pattern: /system\s*:|<\s*system\s*>/i, 
        name: 'System prompt injection',
        severity: 'critical'
      },
      {
        pattern: /(\[|\()?system(\]|\))?.*?(\[|\()?\/system(\]|\))?/i,
        name: 'System tag manipulation',
        severity: 'high'
      }
    ];

    injectionPatterns.forEach(({pattern, name, severity}) => {
      if (pattern.test(prompt)) {
        analysis.threats.push({
          type: name,
          severity: severity,
          pattern: pattern.source
        });
        
        if (severity === 'critical') {
          analysis.riskLevel = 'critical';
        } else if (severity === 'high' && analysis.riskLevel !== 'critical') {
          analysis.riskLevel = 'high';
        } else if (severity === 'medium' && analysis.riskLevel === 'low') {
          analysis.riskLevel = 'medium';
        }
      }
    });

    // Calculate confidence based on number of threats and protection level
    const threatCount = analysis.threats.length;
    const baseConfidence = threatCount > 0 ? Math.min(85 + (threatCount * 5), 99) : 95;
    
    const levelMultiplier = {
      'basic': 0.8,
      'advanced': 0.9,
      'strict': 1.0
    };

    analysis.confidence = Math.round(baseConfidence * levelMultiplier[state.protectionLevel]);

    return analysis;
  }

  // Display analysis results
  function displayAnalysisResults(analysis) {
    const resultContainer = createResultContainer();
    
    const riskConfig = {
      low: { 
        color: 'green', 
        icon: 'check_circle', 
        title: 'Prompt Appears Safe',
        bgClass: 'bg-green-500/10 border-green-500/20'
      },
      medium: { 
        color: 'yellow', 
        icon: 'warning', 
        title: 'Medium Risk Detected',
        bgClass: 'bg-yellow-500/10 border-yellow-500/20'
      },
      high: { 
        color: 'red', 
        icon: 'error', 
        title: 'High Risk Detected',
        bgClass: 'bg-red-500/10 border-red-500/20'
      },
      critical: { 
        color: 'red', 
        icon: 'dangerous', 
        title: 'Critical Threat Detected',
        bgClass: 'bg-red-500/20 border-red-500/30'
      }
    };

    const config = riskConfig[analysis.riskLevel];
    
    resultContainer.className = `mt-4 p-4 rounded-2xl border ${config.bgClass}`;
    
    let threatsHTML = '';
    if (analysis.threats.length > 0) {
      threatsHTML = `
        <div class="mt-3">
          <div class="text-gray-300 text-sm font-medium mb-2">Detected threats:</div>
          <ul class="text-gray-400 text-sm space-y-1">
            ${analysis.threats.map(threat => `
              <li class="flex items-center gap-2">
                <span class="material-icons text-${config.color}-400 text-[16px]">fiber_manual_record</span>
                ${threat.type} (${threat.severity})
              </li>
            `).join('')}
          </ul>
        </div>
      `;
    }

    resultContainer.innerHTML = `
      <div class="flex items-start gap-3">
        <span class="material-icons text-${config.color}-400 text-[24px]">${config.icon}</span>
        <div class="flex-1">
          <div class="text-${config.color}-400 font-semibold text-lg">${config.title}</div>
          <div class="text-gray-300 mt-1">
            Analysis confidence: ${analysis.confidence}% 
            (${state.protectionLevel} mode)
          </div>
          ${threatsHTML}
          <div class="text-gray-500 text-xs mt-3">
            Analyzed at ${analysis.timestamp.toLocaleTimeString()}
          </div>
        </div>
      </div>
    `;

    // Log the detection if threats were found
    if (analysis.threats.length > 0) {
      logThreatDetection(analysis);
    }
  }

  // Create result container
  function createResultContainer() {
    // Remove existing result if any
    const existingResult = document.querySelector('.analysis-result');
    if (existingResult) {
      existingResult.remove();
    }

    const container = document.createElement('div');
    container.classList.add('analysis-result');
    
    // Insert after the analyze button
    if (elements.analyzeBtn && elements.analyzeBtn.parentElement) {
      elements.analyzeBtn.parentElement.insertAdjacentElement('afterend', container);
    }
    
    return container;
  }

  // Log threat detection
  function logThreatDetection(analysis) {
    // Update statistics
    state.stats.threatsBlocked++;
    
    // In a real application, this would send to a backend
    console.log('Threat detection logged:', analysis);
  }

  // Clear test prompt
  function clearTestPrompt() {
    if (elements.testPromptTextarea) {
      elements.testPromptTextarea.value = '';
    }
    
    // Remove analysis result
    const existingResult = document.querySelector('.analysis-result');
    if (existingResult) {
      existingResult.remove();
    }
  }

  // Handle keyword input
  function handleKeywordInput(event) {
    if (event.key === 'Enter') {
      addKeyword();
    }
  }

  // Add keyword to blocked list
  function addKeyword() {
    const keyword = elements.keywordInput?.value.trim();
    if (keyword && !state.blockedKeywords.includes(keyword.toLowerCase())) {
      state.blockedKeywords.push(keyword.toLowerCase());
      elements.keywordInput.value = '';
      updateKeywordDisplay();
    }
  }

  // Update keyword display
  function updateKeywordDisplay() {
    // This would update the keyword tags in the UI
    console.log('Updated blocked keywords:', state.blockedKeywords);
  }

  // Handle setting changes
  function handleSettingChange(event) {
    const checkbox = event.target;
    const setting = checkbox.closest('label')?.textContent.trim();
    
    switch(setting) {
      case 'Real-time monitoring':
        state.realTimeMonitoring = checkbox.checked;
        break;
      case 'Auto-block threats':
        state.autoBlock = checkbox.checked;
        break;
      case 'Email notifications':
        state.emailNotifications = checkbox.checked;
        break;
      case 'Detailed logging':
        state.detailedLogging = checkbox.checked;
        break;
    }
    
    console.log('Setting changed:', setting, checkbox.checked);
  }

  // Update UI with current state
  function updateUI() {
    // Set protection level
    const levelInput = document.querySelector(`input[value="${state.protectionLevel}"]`);
    if (levelInput) {
      levelInput.checked = true;
    }

    // Set checkbox states
    const checkboxes = elements.settingsCheckboxes;
    if (checkboxes.length >= 4) {
      checkboxes[0].checked = state.realTimeMonitoring;
      checkboxes[1].checked = state.autoBlock;
      checkboxes[2].checked = state.emailNotifications;
      checkboxes[3].checked = state.detailedLogging;
    }
  }

  // Simulate real-time data updates
  function simulateRealTimeData() {
    if (!state.realTimeMonitoring) return;

    setInterval(() => {
      // Randomly update stats
      if (Math.random() < 0.1) { // 10% chance per interval
        state.stats.threatsBlocked += Math.floor(Math.random() * 3);
        updateStatsDisplay();
      }
    }, 5000); // Check every 5 seconds
  }

  // Update statistics display
  function updateStatsDisplay() {
    // Update the stats in the UI
    console.log('Stats updated:', state.stats);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Export for global access if needed
  window.PromptInjectionDashboard = {
    analyzePrompt: performPromptAnalysis,
    addKeyword: addKeyword,
    getState: () => ({ ...state })
  };

})();
