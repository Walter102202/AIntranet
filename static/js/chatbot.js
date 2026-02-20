/**
 * Chatbot con IA - Frontend
 * Maneja la interfaz y comunicación con el backend del chatbot
 */

class Chatbot {
    constructor() {
        this.isOpen = false;
        this.isLoading = false;
        this.sessionId = null;
        this.messageHistory = [];

        this.init();
    }

    init() {
        // Crear elementos del DOM
        this.createChatbotElements();

        // Event listeners
        document.getElementById('chatbot-button').addEventListener('click', () => this.toggle());
        document.getElementById('chatbot-close').addEventListener('click', () => this.close());
        document.getElementById('chatbot-send').addEventListener('click', () => this.sendMessage());
        document.getElementById('chatbot-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Botones de gestión
        const newChatBtn = document.getElementById('chatbot-new');
        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => this.newSession());
        }

        const summaryBtn = document.getElementById('chatbot-summary');
        if (summaryBtn) {
            summaryBtn.addEventListener('click', () => this.showSessionSummary());
        }

        const clearBtn = document.getElementById('chatbot-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearHistory());
        }

        // Cargar historial al abrir
        this.loadHistory();
    }

    createChatbotElements() {
        // Verificar si ya existe
        if (document.getElementById('chatbot-container')) {
            return;
        }

        const container = document.createElement('div');
        container.id = 'chatbot-container';
        container.innerHTML = `
            <!-- Botón flotante -->
            <button id="chatbot-button" title="Abrir asistente virtual">
                <i class="bi bi-chat-dots-fill"></i>
            </button>

            <!-- Widget del chatbot -->
            <div id="chatbot-widget">
                <!-- Header -->
                <div id="chatbot-header">
                    <h3>
                        <i class="bi bi-robot me-2"></i>
                        Asistente Virtual
                    </h3>
                    <div class="chatbot-action-btns">
                        <button class="chatbot-action-btn" id="chatbot-summary" title="Ver resumen de sesión">
                            <i class="bi bi-info-circle"></i>
                        </button>
                        <button class="chatbot-action-btn" id="chatbot-clear" title="Limpiar historial">
                            <i class="bi bi-trash"></i>
                        </button>
                        <button class="chatbot-action-btn" id="chatbot-new" title="Nueva conversación">
                            <i class="bi bi-arrow-clockwise"></i>
                        </button>
                        <button class="chatbot-action-btn" id="chatbot-close" title="Cerrar">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                </div>

                <!-- Mensajes -->
                <div id="chatbot-messages">
                    <!-- Los mensajes se agregarán aquí dinámicamente -->
                </div>

                <!-- Input -->
                <div id="chatbot-input-area">
                    <textarea
                        id="chatbot-input"
                        placeholder="Escribe tu mensaje..."
                        rows="1"
                    ></textarea>
                    <button id="chatbot-send">
                        <i class="bi bi-send-fill"></i>
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(container);
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        this.isOpen = true;
        document.getElementById('chatbot-widget').classList.add('show');
        document.getElementById('chatbot-button').classList.add('active');

        // Si no hay mensajes, mostrar mensaje de bienvenida
        if (this.messageHistory.length === 0) {
            this.showWelcomeMessage();
        }

        // Focus en el input
        document.getElementById('chatbot-input').focus();
    }

    close() {
        this.isOpen = false;
        document.getElementById('chatbot-widget').classList.remove('show');
        document.getElementById('chatbot-button').classList.remove('active');
    }

    showWelcomeMessage() {
        const messagesContainer = document.getElementById('chatbot-messages');
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <i class="bi bi-robot"></i>
                <h4>¡Hola! Soy tu asistente virtual</h4>
                <p>Puedo ayudarte con información y acciones en la intranet.</p>
            </div>
            <div class="quick-suggestions">
                <button class="quick-suggestion" onclick="chatbot.sendQuickMessage('¿Cuántos documentos hay disponibles?')">
                    <i class="bi bi-file-earmark-text me-2"></i>
                    ¿Cuántos documentos hay disponibles?
                </button>
                <button class="quick-suggestion" onclick="chatbot.sendQuickMessage('¿Cuáles son mis vacaciones pendientes?')">
                    <i class="bi bi-calendar-check me-2"></i>
                    Ver mis vacaciones
                </button>
                <button class="quick-suggestion" onclick="chatbot.sendQuickMessage('Quiero crear un ticket de soporte')">
                    <i class="bi bi-ticket-perforated me-2"></i>
                    Crear ticket de soporte
                </button>
            </div>
        `;
    }

    sendQuickMessage(message) {
        document.getElementById('chatbot-input').value = message;
        this.sendMessage();
    }

    async sendMessage() {
        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();

        if (!message || this.isLoading) {
            return;
        }

        // Limpiar input
        input.value = '';
        input.style.height = 'auto';

        // Agregar mensaje del usuario
        this.addMessage('user', message);

        // Mostrar indicador de carga
        this.showLoading();
        this.isLoading = true;

        try {
            // Enviar al backend
            const response = await fetch('/chatbot/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            // Ocultar indicador de carga
            this.hideLoading();

            if (data.success) {
                // Agregar respuesta del asistente
                this.addMessage('bot', data.response);
                this.sessionId = data.session_id;
            } else {
                // Mostrar error
                this.addMessage('bot', `Lo siento, ha ocurrido un error: ${data.error}`);
            }

        } catch (error) {
            this.hideLoading();
            this.addMessage('bot', 'Lo siento, no puedo conectarme con el servidor en este momento. Por favor, intenta más tarde.');
            console.error('Error al enviar mensaje:', error);
        } finally {
            this.isLoading = false;
        }
    }

    addMessage(role, content) {
        const messagesContainer = document.getElementById('chatbot-messages');

        // Si es el primer mensaje, limpiar mensaje de bienvenida
        if (messagesContainer.querySelector('.welcome-message')) {
            messagesContainer.innerHTML = '';
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${role}`;

        const avatarIcon = role === 'user' ? 'bi-person-fill' : 'bi-robot';
        const avatarClass = role === 'user' ? 'user-avatar' : 'bot';

        // Construir avatar de forma segura
        const avatarDiv = document.createElement('div');
        avatarDiv.className = `message-avatar ${avatarClass}`;
        const avatarI = document.createElement('i');
        avatarI.className = avatarIcon;
        avatarDiv.appendChild(avatarI);

        // Construir contenido del mensaje de forma segura (previene XSS)
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        this.renderSafeMessage(contentDiv, content);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);

        // Scroll al final
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Guardar en historial
        this.messageHistory.push({ role, content });
    }

    renderSafeMessage(container, content) {
        /**
         * Renderiza contenido de mensaje de forma segura, sin usar innerHTML.
         * Convierte saltos de línea y URLs sin inyectar HTML directamente.
         */
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const lines = content.split('\n');

        lines.forEach((line, lineIndex) => {
            if (lineIndex > 0) {
                container.appendChild(document.createElement('br'));
            }

            // Separar la línea en segmentos de texto y URLs
            let lastIndex = 0;
            let match;
            const regex = new RegExp(urlRegex.source, 'g');

            while ((match = regex.exec(line)) !== null) {
                // Texto antes de la URL
                if (match.index > lastIndex) {
                    container.appendChild(
                        document.createTextNode(line.substring(lastIndex, match.index))
                    );
                }

                // Crear enlace seguro
                const link = document.createElement('a');
                link.href = match[1];
                link.target = '_blank';
                link.rel = 'noopener noreferrer';
                link.textContent = match[1];
                container.appendChild(link);

                lastIndex = regex.lastIndex;
            }

            // Texto restante después de la última URL
            if (lastIndex < line.length) {
                container.appendChild(
                    document.createTextNode(line.substring(lastIndex))
                );
            }
        });
    }

    showLoading() {
        const messagesContainer = document.getElementById('chatbot-messages');
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chatbot-message bot loading';
        loadingDiv.id = 'loading-indicator';
        loadingDiv.innerHTML = `
            <div class="message-avatar bot">
                <i class="bi bi-robot"></i>
            </div>
            <div class="message-content">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        `;

        messagesContainer.appendChild(loadingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Deshabilitar input y botón
        document.getElementById('chatbot-input').disabled = true;
        document.getElementById('chatbot-send').disabled = true;
    }

    hideLoading() {
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }

        // Habilitar input y botón
        document.getElementById('chatbot-input').disabled = false;
        document.getElementById('chatbot-send').disabled = false;
        document.getElementById('chatbot-input').focus();
    }

    async loadHistory() {
        try {
            const response = await fetch('/chatbot/history');
            const data = await response.json();

            if (data.success && data.messages.length > 0) {
                this.sessionId = data.session_id;
                this.messageHistory = data.messages;

                // Renderizar historial
                const messagesContainer = document.getElementById('chatbot-messages');
                messagesContainer.innerHTML = '';

                data.messages.forEach(msg => {
                    this.addMessage(msg.role, msg.content);
                });
            }
        } catch (error) {
            console.error('Error al cargar historial:', error);
        }
    }

    async newSession() {
        if (!confirm('¿Estás seguro de que quieres iniciar una nueva conversación? Se perderá el historial actual.')) {
            return;
        }

        try {
            const response = await fetch('/chatbot/new-session', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                // Limpiar historial y UI
                this.messageHistory = [];
                this.sessionId = data.session_id;
                document.getElementById('chatbot-messages').innerHTML = '';
                this.showWelcomeMessage();
            }
        } catch (error) {
            console.error('Error al crear nueva sesión:', error);
            alert('Error al crear nueva conversación');
        }
    }

    async showSessionSummary() {
        /**
         * Muestra un resumen de la sesión actual con estadísticas
         */
        try {
            const response = await fetch('/chatbot/session-summary');
            const data = await response.json();

            if (data.success && data.summary.active) {
                const summary = data.summary;

                // Formatear fechas
                const started = summary.started ? new Date(summary.started).toLocaleString('es-ES') : 'Desconocido';
                const lastMsg = summary.last_message ? new Date(summary.last_message).toLocaleString('es-ES') : 'Desconocido';

                // Construir mensaje con resumen
                let summaryText = `📊 **Resumen de Sesión**\n\n`;
                summaryText += `**ID:** ${summary.session_id}\n`;
                summaryText += `**Iniciada:** ${started}\n`;
                summaryText += `**Último mensaje:** ${lastMsg}\n\n`;
                summaryText += `**Estadísticas:**\n`;
                summaryText += `• Total de mensajes: ${summary.total_messages}\n`;
                summaryText += `• Mensajes del usuario: ${summary.user_messages}\n`;
                summaryText += `• Respuestas del asistente: ${summary.assistant_messages}\n`;
                summaryText += `• Tokens estimados: ~${summary.estimated_tokens}\n\n`;

                if (summary.actions_executed && summary.actions_executed.length > 0) {
                    summaryText += `**Acciones ejecutadas:**\n`;
                    summary.actions_executed.forEach(action => {
                        summaryText += `• ${action.type}: ${action.count} veces (${action.successful} exitosas)\n`;
                    });
                } else {
                    summaryText += `**Acciones ejecutadas:** Ninguna\n`;
                }

                this.addMessage('bot', summaryText);
            } else {
                this.addMessage('bot', 'No hay sesión activa o no se pudo obtener el resumen.');
            }
        } catch (error) {
            console.error('Error al obtener resumen de sesión:', error);
            this.addMessage('bot', 'Error al obtener el resumen de la sesión.');
        }
    }

    async clearHistory() {
        /**
         * Limpia el historial de la sesión actual
         */
        if (!confirm('¿Estás seguro de que deseas limpiar todo el historial de conversación? Esta acción no se puede deshacer.')) {
            return;
        }

        try {
            const response = await fetch('/chatbot/clear-history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                // Limpiar mensajes del DOM
                document.getElementById('chatbot-messages').innerHTML = '';
                this.messageHistory = [];

                // Mostrar mensaje de bienvenida
                this.showWelcomeMessage();

                this.addMessage('bot', '✅ Historial limpiado exitosamente. Comenzando conversación nueva.');
            } else {
                this.addMessage('bot', `Error al limpiar historial: ${data.error}`);
            }
        } catch (error) {
            console.error('Error al limpiar historial:', error);
            this.addMessage('bot', 'Error al limpiar el historial.');
        }
    }
}

// Inicializar chatbot cuando el DOM esté listo
let chatbot;
document.addEventListener('DOMContentLoaded', function() {
    chatbot = new Chatbot();
});
