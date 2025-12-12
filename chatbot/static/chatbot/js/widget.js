/**
 * Chatbot Widget JavaScript
 */

class ChatbotWidget {
    constructor() {
        this.isOpen = false;
        this.sessionId = null;
        this.apiBase = '/chatbot/';
        this.currentInteractionId = null;
        this.currentTheme = this.loadThemePreference();
        this.welcomeBubbleShown = false;
        
        this.init();
    }
    
    init() {
        // Get configuration from HTML
        this.loadConfig();
        
        // Bind events
        this.bindEvents();
        
        // Load session history
        this.loadSessionHistory();
        
        // Auto-resize textarea
        this.setupTextareaResize();
        
        // Initialize theme
        this.initializeTheme();
        
        // Listen for system theme changes
        this.setupSystemThemeListener();
        
        // Show welcome bubble after initialization
        this.showWelcomeBubble();
        
        console.log('Chatbot widget initialized');
    }
    
    loadConfig() {
        const configElement = document.getElementById('chatbot-data');
        if (configElement) {
            try {
                const config = JSON.parse(configElement.textContent);
                this.sessionId = config.session_id;
                this.apiBase = config.api_base || '/chatbot/';
                
                // Load existing history if any
                if (config.history && config.history.length > 0) {
                    this.displayHistory(config.history);
                }
            } catch (e) {
                console.error('Error loading chatbot config:', e);
            }
        }
        
        // Generate session ID if not provided
        if (!this.sessionId) {
            this.sessionId = this.generateSessionId();
        }
    }
    
    bindEvents() {
        // Toggle button
        const toggleBtn = document.getElementById('chatbot-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.hideWelcomeBubble(); // Hide bubble when opening chat
                this.toggle();
            });
        }
        
        // Welcome bubble click
        const welcomeBubble = document.getElementById('chatbot-welcome-bubble');
        if (welcomeBubble) {
            welcomeBubble.addEventListener('click', () => {
                this.hideWelcomeBubble();
                this.open(); // Open chat when clicking bubble
            });
        }
        
        // Close button
        const closeBtn = document.getElementById('chatbot-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }
        
        // Clear button
        const clearBtn = document.getElementById('chatbot-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearConversation());
        }
        
        // Theme toggle button
        const themeBtn = document.getElementById('chatbot-theme-toggle');
        if (themeBtn) {
            themeBtn.addEventListener('click', () => this.toggleTheme());
        }
        
        // Send button
        const sendBtn = document.getElementById('chatbot-send');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }
        
        // Input field
        const input = document.getElementById('chatbot-input');
        if (input) {
            input.addEventListener('keydown', (e) => this.handleKeyDown(e));
            input.addEventListener('input', () => this.updateSendButton());
        }
        
        // Suggestion buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggestion-button')) {
                const question = e.target.getAttribute('data-question');
                this.sendPredefinedQuestion(question);
            }
        });
        
        // Feedback buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('feedback-button')) {
                this.handleFeedback(e.target);
            }
        });
    }
    
    setupTextareaResize() {
        const input = document.getElementById('chatbot-input');
        if (input) {
            input.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 100) + 'px';
            });
        }
    }
    
    generateSessionId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }
    
    open() {
        const container = document.getElementById('chatbot-container');
        if (container) {
            container.style.display = 'flex';
            this.isOpen = true;
            
            // Focus input
            setTimeout(() => {
                const input = document.getElementById('chatbot-input');
                if (input) input.focus();
            }, 100);
            
            // Hide badge
            this.hideBadge();
            
            // Scroll to bottom
            this.scrollToBottom();
        }
    }
    
    close() {
        const container = document.getElementById('chatbot-container');
        if (container) {
            container.style.display = 'none';
            this.isOpen = false;
        }
    }
    
    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }
    
    updateSendButton() {
        const input = document.getElementById('chatbot-input');
        const sendBtn = document.getElementById('chatbot-send');
        
        if (input && sendBtn) {
            const hasText = input.value.trim().length > 0;
            sendBtn.disabled = !hasText;
        }
    }
    
    sendPredefinedQuestion(question) {
        const input = document.getElementById('chatbot-input');
        if (input) {
            input.value = question;
            this.sendMessage();
        }
    }
    
    async sendMessage() {
        const input = document.getElementById('chatbot-input');
        if (!input) return;
        
        const message = input.value.trim();
        if (!message) return;
        
        // Clear input
        input.value = '';
        input.style.height = 'auto';
        this.updateSendButton();
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Show loading indicator
        this.showLoading();
        
        try {
            // Send to API
            const response = await this.callAPI('ask/', {
                pregunta: message,
                session_id: this.sessionId
            });
            
            // Hide loading
            this.hideLoading();
            
            if (response.success) {
                // Add bot response
                this.addMessage(response.respuesta, 'bot', response.interaction_id);
                this.currentInteractionId = response.interaction_id;
                
                // Save to session storage
                this.saveToSessionStorage(message, response.respuesta, response.interaction_id);
            } else {
                // Show error message
                this.addMessage(
                    response.error || 'Lo siento, ocurrió un error. Por favor, intenta de nuevo.',
                    'bot'
                );
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideLoading();
            this.addMessage(
                'Lo siento, no pude conectar con el servidor. Por favor, verifica tu conexión e intenta de nuevo.',
                'bot'
            );
        }
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    async callAPI(endpoint, data) {
        const url = this.apiBase + endpoint;
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return await response.json();
    }
    
    addMessage(text, sender, interactionId = null) {
        const messagesContainer = document.getElementById('chatbot-messages');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;
        
        const now = new Date();
        const timeStr = now.toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    ${sender === 'bot' 
                        ? '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>'
                        : '<path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>'
                    }
                </svg>
            </div>
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(text)}</div>
                <div class="message-time">${timeStr}</div>
                ${sender === 'bot' && interactionId ? this.createFeedbackButtons(interactionId) : ''}
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        
        // Remove suggestions after first user message
        if (sender === 'user') {
            const suggestions = messagesContainer.querySelector('.chatbot-suggestions');
            if (suggestions) {
                suggestions.remove();
            }
        }
    }
    
    createFeedbackButtons(interactionId) {
        return `
            <div class="message-feedback">
                <button class="feedback-button positive" data-interaction-id="${interactionId}" data-useful="true">
                    👍 Útil
                </button>
                <button class="feedback-button negative" data-interaction-id="${interactionId}" data-useful="false">
                    👎 No útil
                </button>
            </div>
        `;
    }
    
    async handleFeedback(button) {
        const interactionId = button.getAttribute('data-interaction-id');
        const wasUseful = button.getAttribute('data-useful') === 'true';
        
        try {
            await this.callAPI('feedback/', {
                interaction_id: parseInt(interactionId),
                fue_util: wasUseful
            });
            
            // Mark buttons as used
            const feedbackContainer = button.parentElement;
            const buttons = feedbackContainer.querySelectorAll('.feedback-button');
            buttons.forEach(btn => {
                btn.classList.add('selected');
                btn.disabled = true;
            });
            
            // Show thank you message
            button.textContent = wasUseful ? '👍 ¡Gracias!' : '👎 Gracias por tu feedback';
            
        } catch (error) {
            console.error('Error sending feedback:', error);
        }
    }
    
    showLoading() {
        const loadingElement = document.getElementById('chatbot-loading');
        if (loadingElement) {
            loadingElement.style.display = 'flex';
            this.scrollToBottom();
        }
    }
    
    hideLoading() {
        const loadingElement = document.getElementById('chatbot-loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
    
    scrollToBottom() {
        const messagesContainer = document.getElementById('chatbot-messages');
        if (messagesContainer) {
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 100);
        }
    }
    
    showBadge(count = 1) {
        const badge = document.getElementById('chatbot-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = 'flex';
        }
    }
    
    hideBadge() {
        const badge = document.getElementById('chatbot-badge');
        if (badge) {
            badge.style.display = 'none';
        }
    }
    
    saveToSessionStorage(question, response, interactionId) {
        try {
            const history = JSON.parse(sessionStorage.getItem('chatbot_history') || '[]');
            history.push({
                pregunta: question,
                respuesta: response,
                timestamp: new Date().toISOString(),
                interaction_id: interactionId
            });
            
            // Keep only last 50 messages
            if (history.length > 50) {
                history.splice(0, history.length - 50);
            }
            
            sessionStorage.setItem('chatbot_history', JSON.stringify(history));
        } catch (e) {
            console.error('Error saving to session storage:', e);
        }
    }
    
    loadSessionHistory() {
        try {
            const history = JSON.parse(sessionStorage.getItem('chatbot_history') || '[]');
            this.displayHistory(history);
        } catch (e) {
            console.error('Error loading session history:', e);
        }
    }
    
    displayHistory(history) {
        if (!history || history.length === 0) return;
        
        // Remove welcome message and suggestions if history exists
        const messagesContainer = document.getElementById('chatbot-messages');
        if (messagesContainer && history.length > 0) {
            const welcomeMessage = messagesContainer.querySelector('.bot-message');
            const suggestions = messagesContainer.querySelector('.chatbot-suggestions');
            
            if (welcomeMessage) welcomeMessage.remove();
            if (suggestions) suggestions.remove();
        }
        
        // Add history messages
        history.forEach(item => {
            this.addMessage(item.pregunta, 'user');
            this.addMessage(item.respuesta, 'bot', item.interaction_id);
        });
        
        this.scrollToBottom();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    clearConversation() {
        // Clear conversation without confirmation
            // Clear messages container completely and restore initial state
            const messagesContainer = document.getElementById('chatbot-messages');
            if (messagesContainer) {
                // Clear all messages
                messagesContainer.innerHTML = '';
                
                // Restore welcome message
                const welcomeMessage = `
                    <div class="chatbot-message bot-message">
                        <div class="message-avatar">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                            </svg>
                        </div>
                        <div class="message-content">
                            <div class="message-text">
                                ¡Hola! Soy el asistente virtual del Centro Fray Bartolomé de las Casas. 
                                Puedo ayudarte con información sobre cursos, inscripciones, horarios y más. 
                                ¿En qué puedo ayudarte?
                            </div>
                            <div class="message-time">${new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}</div>
                        </div>
                    </div>
                `;
                
                // Restore suggestions
                const suggestions = `
                    <div class="chatbot-suggestions">
                        <div class="suggestions-title">Preguntas frecuentes:</div>
                        <button class="suggestion-button" data-question="¿Cuándo empiezan las inscripciones?">
                            ¿Cuándo empiezan las inscripciones?
                        </button>
                        <button class="suggestion-button" data-question="¿Qué cursos están disponibles?">
                            ¿Qué cursos están disponibles?
                        </button>
                        <button class="suggestion-button" data-question="¿Cuáles son los requisitos para inscribirme?">
                            ¿Cuáles son los requisitos para inscribirme?
                        </button>
                        <button class="suggestion-button" data-question="¿Dónde está ubicado el centro?">
                            ¿Dónde está ubicado el centro?
                        </button>
                    </div>
                `;
                
                messagesContainer.innerHTML = welcomeMessage + suggestions;
            }
            
            // Clear session storage
            try {
                sessionStorage.removeItem('chatbot_history');
            } catch (e) {
                console.error('Error clearing session storage:', e);
            }
            
            // Clear session history on server
            this.clearServerHistory();
            
            // Reset current interaction ID
            this.currentInteractionId = null;
            
            // Generate new session ID
            this.sessionId = this.generateSessionId();
            
            // Show success message briefly
            this.showTemporaryMessage('Conversación limpiada. ¡Empecemos de nuevo!', 'success');
    }
    
    clearServerHistory() {
        // Call server endpoint to clear history
        fetch(this.apiBase + 'clear-history/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                session_id: this.sessionId
            })
        })
        .catch(error => {
            console.error('Error clearing server history:', error);
        });
    }
    
    getCsrfToken() {
        // Get CSRF token from cookie or meta tag
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        
        if (cookieValue) {
            return cookieValue;
        }
        
        // Fallback: get from meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Fallback: get from config
        const configElement = document.getElementById('chatbot-data');
        if (configElement) {
            try {
                const config = JSON.parse(configElement.textContent);
                return config.csrf_token;
            } catch (e) {
                console.error('Error getting CSRF token from config:', e);
            }
        }
        
        return '';
    }
    
    showTemporaryMessage(text, type = 'info') {
        const messagesContainer = document.getElementById('chatbot-messages');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message bot-message temporary-message ${type}`;
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
            </div>
            <div class="message-content">
                <div class="message-text">${this.escapeHtml(text)}</div>
            </div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Remove after 2 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 2000);
    }
    
    loadThemePreference() {
        // Load theme preference from localStorage
        try {
            return localStorage.getItem('chatbot-theme') || 'auto';
        } catch (e) {
            console.error('Error loading theme preference:', e);
            return 'auto';
        }
    }
    
    saveThemePreference(theme) {
        // Save theme preference to localStorage
        try {
            localStorage.setItem('chatbot-theme', theme);
        } catch (e) {
            console.error('Error saving theme preference:', e);
        }
    }
    
    initializeTheme() {
        // Apply the current theme
        this.applyTheme(this.currentTheme);
        this.updateThemeIcon();
    }
    
    toggleTheme() {
        // Cycle through themes: auto -> light -> dark -> auto
        switch (this.currentTheme) {
            case 'auto':
                this.currentTheme = 'light';
                break;
            case 'light':
                this.currentTheme = 'dark';
                break;
            case 'dark':
                this.currentTheme = 'auto';
                break;
            default:
                this.currentTheme = 'light';
        }
        
        this.applyTheme(this.currentTheme);
        this.updateThemeIcon();
        this.saveThemePreference(this.currentTheme);
        
        // Show temporary message about theme change
        const themeNames = {
            'auto': 'automático (sigue el sistema)',
            'light': 'claro',
            'dark': 'oscuro'
        };
        
        this.showTemporaryMessage(`Tema cambiado a: ${themeNames[this.currentTheme]}`, 'info');
    }
    
    applyTheme(theme) {
        const widget = document.getElementById('chatbot-widget');
        if (!widget) return;
        
        // Remove existing theme classes
        widget.classList.remove('light-mode', 'dark-mode');
        
        // Apply new theme class
        if (theme === 'light') {
            widget.classList.add('light-mode');
        } else if (theme === 'dark') {
            widget.classList.add('dark-mode');
        }
        // 'auto' theme uses no class, letting CSS media queries handle it
    }
    
    updateThemeIcon() {
        const lightIcon = document.querySelector('.theme-icon-light');
        const darkIcon = document.querySelector('.theme-icon-dark');
        const themeBtn = document.getElementById('chatbot-theme-toggle');
        
        if (!lightIcon || !darkIcon || !themeBtn) return;
        
        // Update icon based on current theme - Luna en modo claro, Sol en modo oscuro
        switch (this.currentTheme) {
            case 'light':
                // Modo claro: mostrar luna (para cambiar a oscuro)
                lightIcon.style.display = 'none';
                darkIcon.style.display = 'block';
                themeBtn.title = 'Cambiar a modo oscuro';
                break;
            case 'dark':
                // Modo oscuro: mostrar sol (para cambiar a claro)
                lightIcon.style.display = 'block';
                darkIcon.style.display = 'none';
                themeBtn.title = 'Cambiar a modo automático';
                break;
            case 'auto':
            default:
                // Modo automático: mostrar el opuesto del sistema actual
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                if (prefersDark) {
                    // Sistema oscuro: mostrar sol (para cambiar a claro)
                    lightIcon.style.display = 'block';
                    darkIcon.style.display = 'none';
                } else {
                    // Sistema claro: mostrar luna (para cambiar a oscuro)
                    lightIcon.style.display = 'none';
                    darkIcon.style.display = 'block';
                }
                themeBtn.title = 'Cambiar a modo claro';
                break;
        }
    }
    
    setupSystemThemeListener() {
        // Listen for system theme changes when in auto mode
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        const handleSystemThemeChange = () => {
            if (this.currentTheme === 'auto') {
                this.updateThemeIcon();
            }
        };
        
        // Modern browsers
        if (mediaQuery.addEventListener) {
            mediaQuery.addEventListener('change', handleSystemThemeChange);
        } else {
            // Fallback for older browsers
            mediaQuery.addListener(handleSystemThemeChange);
        }
    }
    
    showWelcomeBubble() {
        // Only show if not already shown and no chat history exists
        if (this.welcomeBubbleShown || this.isOpen) {
            return;
        }
        
        // Check if there's existing chat history
        try {
            const history = JSON.parse(sessionStorage.getItem('chatbot_history') || '[]');
            if (history.length > 0) {
                return; // Don't show bubble if user has chat history
            }
        } catch (e) {
            // Continue to show bubble if there's an error reading history
        }
        
        // Check if we're on the homepage or main page
        const isHomePage = this.isHomePage();
        if (!isHomePage) {
            return; // Only show on homepage
        }
        
        const bubble = document.getElementById('chatbot-welcome-bubble');
        if (!bubble) return;
        
        // Show bubble after a short delay
        setTimeout(() => {
            bubble.style.display = 'block';
            this.welcomeBubbleShown = true;
            
            // Hide bubble after 3 seconds
            setTimeout(() => {
                this.hideWelcomeBubble();
            }, 3000);
        }, 1000); // Show after 1 second of page load
    }
    
    hideWelcomeBubble() {
        const bubble = document.getElementById('chatbot-welcome-bubble');
        if (!bubble) return;
        
        // Add fade-out animation
        bubble.classList.add('fade-out');
        
        // Remove from DOM after animation
        setTimeout(() => {
            bubble.style.display = 'none';
            bubble.classList.remove('fade-out');
        }, 300);
    }
    
    isHomePage() {
        // Check if current page is homepage
        const path = window.location.pathname;
        const isHome = path === '/' || 
                      path === '/index.html' || 
                      path === '/home' || 
                      path === '/inicio' || 
                      path.endsWith('/') && path.split('/').length <= 2;
        
        return isHome;
    }
}

// Initialize widget when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('chatbot-widget')) {
        window.chatbotWidget = new ChatbotWidget();
        
        // Debug: Verificar que los botones estén presentes
        setTimeout(() => {
            const clearBtn = document.getElementById('chatbot-clear');
            const closeBtn = document.getElementById('chatbot-close');
            
            console.log('Chatbot Clear Button:', clearBtn ? 'Found' : 'NOT FOUND');
            console.log('Chatbot Close Button:', closeBtn ? 'Found' : 'NOT FOUND');
            
            if (clearBtn) {
                console.log('Clear button styles:', window.getComputedStyle(clearBtn).display);
            }
            if (closeBtn) {
                console.log('Close button styles:', window.getComputedStyle(closeBtn).display);
            }
        }, 1000);
    }
});