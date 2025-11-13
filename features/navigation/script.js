// Navigation Feature - Left rail navigation and panel switching
(function () {
  'use strict';

  // Get UI elements
  const settingsBtn = document.getElementById('settingsBtn');
  const editorBtn = document.getElementById('editorBtn');
  const backToEditor = document.getElementById('backToEditor');
  const editorPanel = document.getElementById('editor-pane');
  const promptInjectionsPanel = document.getElementById('promptInjectionsPanel');

  // History panels
  const historyPanel = document.getElementById('history-panel');
  const promptInjectionsHistory = document.getElementById('promptInjectionsHistory');

  // AI Assistant panels
  const assistantPanel = document.getElementById('assistant-panel');

  // Global mode tracking
  window.promptInjectionMode = false;

  // Update UI states
  function showEditor() {
    window.promptInjectionMode = false;

    // Show editor panels
    editorPanel.classList.remove('hidden');
    historyPanel.classList.remove('hidden');
    assistantPanel.classList.remove('hidden');

    // Hide prompt injection panels and playground
    promptInjectionsPanel.classList.add('hidden');
    promptInjectionsHistory.classList.add('hidden');
    const playgroundPanel = document.getElementById('playgroundPanel');
    if (playgroundPanel) playgroundPanel.classList.add('hidden');

    // Update button states
    editorBtn.classList.add('text-black', 'bg-primary', 'shadow-lg', 'shadow-primary/30');
    editorBtn.classList.remove('text-gray-300');
    settingsBtn.classList.remove('text-black', 'bg-primary', 'shadow-lg', 'shadow-primary/30');
    settingsBtn.classList.add('text-gray-300');
    const playgroundBtn = document.getElementById('playgroundBtn');
    if (playgroundBtn) {
      playgroundBtn.classList.remove('text-black', 'bg-primary', 'shadow-lg', 'shadow-primary/30');
      playgroundBtn.classList.add('text-gray-300');
    }

    // **BIDIRECTIONAL INTEGRATION**: Sync text editor with the most recent AI response when returning to editor mode
    setTimeout(() => {
      if (window.chatManager && window.chatManager.messages) {
        const lastAiMessage = window.chatManager.messages
          .slice()
          .reverse()
          .find(msg => msg.role === 'ai');

        if (lastAiMessage) {
          window.chatManager.updateTextEditor(lastAiMessage.content);
          console.log('Mode Switch: Formatted editor synced with latest AI response');
        } else {
          console.log('Mode Switch: No AI messages found to sync');
        }
      } else {
        console.log('Mode Switch: Chat manager not available for sync');
      }
    }, 100);
  }

  function showSettings() {
    window.promptInjectionMode = true;

    // Hide editor panels and playground
    editorPanel.classList.add('hidden');
    historyPanel.classList.add('hidden');
    assistantPanel.classList.add('hidden');
    const playgroundPanel = document.getElementById('playgroundPanel');
    if (playgroundPanel) playgroundPanel.classList.add('hidden');

    // Show prompt injection panels
    promptInjectionsPanel.classList.remove('hidden');
    promptInjectionsHistory.classList.remove('hidden');

    // Update button states
    settingsBtn.classList.add('text-black', 'bg-primary', 'shadow-lg', 'shadow-primary/30');
    settingsBtn.classList.remove('text-gray-300');
    editorBtn.classList.remove('text-black', 'bg-primary', 'shadow-lg', 'shadow-primary/30');
    editorBtn.classList.add('text-gray-300');
    const playgroundBtn = document.getElementById('playgroundBtn');
    if (playgroundBtn) {
      playgroundBtn.classList.remove('text-black', 'bg-primary', 'shadow-lg', 'shadow-primary/30');
      playgroundBtn.classList.add('text-gray-300');
    }

    // Sync with Supabase when entering prompt injection mode
    if (window.promptInjectionSupabase) {
      window.promptInjectionSupabase.sync().then(() => {
        // Update security history display after sync
        if (typeof window.updateSecurityHistoryDisplay === 'function') {
          window.updateSecurityHistoryDisplay();
        }
      });
    } else {
      // Update security history display when switching to security mode
      if (typeof window.updateSecurityHistoryDisplay === 'function') {
        window.updateSecurityHistoryDisplay();
      }
    }
  }

  function showPlayground() {
    console.log('showPlayground() called');
    window.promptInjectionMode = false;

    // Hide all other panels
    if (editorPanel) editorPanel.classList.add('hidden');
    if (historyPanel) historyPanel.classList.add('hidden');
    if (assistantPanel) assistantPanel.classList.add('hidden');
    if (promptInjectionsPanel) promptInjectionsPanel.classList.add('hidden');
    if (promptInjectionsHistory) promptInjectionsHistory.classList.add('hidden');

    // Show playground panel
    const playgroundPanel = document.getElementById('playgroundPanel');
    console.log('Playground panel element:', playgroundPanel);

    if (playgroundPanel) {
      playgroundPanel.classList.remove('hidden');
      console.log('Playground panel should now be visible');

      // Initialize playground if not already done
      if (!window.playgroundInitialized) {
        try {
          console.log('Initializing playground...');
          if (typeof initializePlayground === 'function') {
            initializePlayground();
            window.playgroundInitialized = true;
            console.log('Playground initialized successfully');
          } else {
            console.error('initializePlayground function not found');
          }
        } catch (error) {
          console.error('Failed to initialize playground:', error);
        }
      }
    } else {
      console.error('Playground panel not found in DOM!');
    }

    // Update button states
    const playgroundBtn = document.getElementById('playgroundBtn');
    if (playgroundBtn) {
      playgroundBtn.classList.add('text-black', 'bg-primary', 'shadow-lg', 'shadow-primary/30');
      playgroundBtn.classList.remove('text-gray-300');
    }
    editorBtn.classList.remove('text-black', 'bg-primary', 'shadow-lg', 'shadow-primary/30');
    editorBtn.classList.add('text-gray-300');
    settingsBtn.classList.remove('text-black', 'bg-primary', 'shadow-lg', 'shadow-primary/30');
    settingsBtn.classList.add('text-gray-300');
  }

  // Event listeners
  if (settingsBtn) settingsBtn.addEventListener('click', showSettings);
  if (editorBtn) editorBtn.addEventListener('click', showEditor);
  if (backToEditor) backToEditor.addEventListener('click', showEditor);

  const playgroundBtn = document.getElementById('playgroundBtn');
  if (playgroundBtn) {
    playgroundBtn.addEventListener('click', showPlayground);
    console.log('Playground button event listener attached');
  } else {
    console.error('Playground button not found!');
  }

  // Initialize - ensure editor mode is active by default
  showEditor(); // Ensure proper initial state

  console.log('Navigation feature loaded');
})();
