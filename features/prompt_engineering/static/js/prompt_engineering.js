/**
 * n8n Webhook Chat Integration (via Flask Proxy)
 * Handles communication with n8n webhook through Flask proxy to avoid CORS
 */

(function() {
  'use strict';

  // Configuration - use Flask proxy to avoid CORS issues
  const CHAT_API = '/api/chat';

  const chatInput = document.getElementById('securityChatInput');
  const sendBtn = document.getElementById('sendSecurityMessage');
  const messagesContainer = document.getElementById('securityChatMessages');

  let isTyping = false;

  // Add message to chat
  function addMessage(content, isUser = false, isLoading = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${isUser ? 'justify-end' : 'items-start gap-3'}`;

    if (isUser) {
      messageDiv.innerHTML = `
        <div class="bg-primary rounded-2xl p-3 max-w-[85%] shadow-md shadow-primary/20">
          <p class="text-sm md:text-base text-black">${content}</p>
        </div>
      `;
    } else {
      messageDiv.innerHTML = `
        <div class="w-7 h-7 rounded-full bg-red-500 flex-shrink-0 grid place-items-center shadow-md shadow-red-500/30">
          <span class="material-icons text-white text-[18px]">security</span>
        </div>
        <div class="bg-white/5 border border-white/10 rounded-2xl p-3 max-w-[85%]">
          ${isLoading ? `
            <div class="flex items-center gap-2">
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              <span class="text-sm text-gray-300">AI Assistant is thinking...</span>
            </div>
          ` : `
            <div class="text-sm md:text-base text-gray-100">${content}</div>
          `}
        </div>
      `;
    }

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return messageDiv;
  }

  // Send message to n8n webhook via Flask proxy
  async function sendMessage() {
    if (isTyping) return;

    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage(message, true);
    chatInput.value = '';

    // Add loading message
    const loadingMessage = addMessage('', false, true);
    isTyping = true;
    
    // Disable send button
    sendBtn.style.opacity = '0.5';
    sendBtn.disabled = true;

    try {
      console.log('Sending message to Flask proxy:', message);
      
      const response = await fetch(CHAT_API, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json' 
        },
        body: JSON.stringify({ 
          message: message 
        })
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Network error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Response data:', data);

      // Remove loading message
      loadingMessage.remove();

      // Add AI response
      const aiResponse = data.reply || 'Sorry, I could not generate a response at the moment.';
      addMessage(aiResponse, false);

    } catch (error) {
      console.error('Chat error:', error);

      // Remove loading message and show error
      loadingMessage.remove();
      
      // Show user-friendly error message
      let errorMessage = 'Sorry, I encountered an error. Please check your connection and try again.';
      if (error.message.includes('Network error')) {
        errorMessage = 'Unable to connect to the AI service. Please try again.';
      } else if (error.message.includes('Failed to fetch')) {
        errorMessage = 'Network connection failed. Please check your internet and try again.';
      }
      
      addMessage(errorMessage, false);

    } finally {
      isTyping = false;
      // Re-enable send button
      sendBtn.disabled = false;
      sendBtn.style.opacity = chatInput.value.trim() ? '1' : '0.5';
    }
  }

  // Event listeners
  if (sendBtn) {
    sendBtn.addEventListener('click', sendMessage);
  }

  if (chatInput) {
    chatInput.addEventListener('keypress', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Disable send button when typing
    chatInput.addEventListener('input', function () {
      if (sendBtn) {
        sendBtn.style.opacity = this.value.trim() ? '1' : '0.5';
      }
    });
  }

  // Initialize send button state
  if (sendBtn) {
    sendBtn.style.opacity = '0.5';
  }

  // Test function - automatically send a ping on page load
  async function testWebhook() {
    if (!chatInput || !sendBtn) {
      console.log('Chat elements not found, skipping webhook test');
      return;
    }

    console.log('Testing n8n webhook connection...');
    
    try {
      // Wait a bit for the page to fully load
      setTimeout(async () => {
        chatInput.value = 'ping';
        console.log('Sending test message: ping');
        await sendMessage();
        console.log('Test message sent successfully');
      }, 2000);
    } catch (error) {
      console.error('Webhook test failed:', error);
    }
  }

  // Run test on page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', testWebhook);
  } else {
    testWebhook();
  }

  // Export for potential external use
  window.n8nChat = {
    sendMessage,
    addMessage,
    testWebhook
  };

})();