// Global state
let apiKey = localStorage.getItem('recallgpt_api_key') || '';
let currentThreadId = null;
let conversations = [];

// API Base URL
const API_BASE = window.location.origin;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (apiKey) {
        showChatInterface();
        loadConversations();
    } else {
        showApiKeySetup();
    }
});

// Show/Hide sections
function showApiKeySetup() {
    document.getElementById('apiKeySetup').style.display = 'flex';
    document.getElementById('chatInterface').style.display = 'none';
}

function showChatInterface() {
    document.getElementById('apiKeySetup').style.display = 'none';
    document.getElementById('chatInterface').style.display = 'flex';
}

// API Key Management
function setApiKey() {
    const input = document.getElementById('apiKeyInput');
    const key = input.value.trim();
    
    if (!key) {
        alert('Please enter a valid API key');
        return;
    }
    
    if (!key.startsWith('recallgpt_')) {
        alert('Invalid API key format. Key should start with "recallgpt_"');
        return;
    }
    
    apiKey = key;
    localStorage.setItem('recallgpt_api_key', apiKey);
    showChatInterface();
    loadConversations();
}

async function generateApiKey() {
    const userId = prompt('Enter your user ID:');
    const name = prompt('Enter a name for this API key:');
    
    if (!userId || !name) return;
    
    try {
        const response = await fetch(`${API_BASE}/auth/generate-key`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId, name: name })
        });
        
        const data = await response.json();
        
        if (data.api_key) {
            document.getElementById('apiKeyInput').value = data.api_key;
            alert(`API Key generated!\n\n${data.api_key}\n\nPlease save this key securely.`);
        }
    } catch (error) {
        alert('Error generating API key: ' + error.message);
    }
}

// Load conversations
async function loadConversations() {
    try {
        const response = await fetch(`${API_BASE}/threads/list`, {
            headers: { 'X-API-Key': apiKey }
        });
        
        if (!response.ok) throw new Error('Failed to load conversations');
        
        const data = await response.json();
        conversations = data.threads;
        renderConversations();
    } catch (error) {
        console.error('Error loading conversations:', error);
        document.getElementById('conversationsList').innerHTML = 
            '<div class="loading-conversations">Failed to load conversations</div>';
    }
}

function renderConversations() {
    const container = document.getElementById('conversationsList');
    
    if (conversations.length === 0) {
        container.innerHTML = '<div class="loading-conversations">No conversations yet</div>';
        return;
    }
    
    container.innerHTML = conversations.map(conv => `
        <div class="conversation-item ${conv.thread_id === currentThreadId ? 'active' : ''}" 
             onclick="loadThread(${conv.thread_id}, '${conv.thread_name}')">
            ${conv.thread_name}
        </div>
    `).join('');
}

// Thread Management
async function loadThread(threadId, threadName) {
    currentThreadId = threadId;
    document.getElementById('chatTitle').textContent = threadName;
    renderConversations();
    
    try {
        const response = await fetch(`${API_BASE}/threads/${threadId}/history?limit=50`, {
            headers: { 'X-API-Key': apiKey }
        });
        
        const data = await response.json();
        renderMessages(data.messages);
    } catch (error) {
        console.error('Error loading thread:', error);
    }
}

function showNewThreadModal() {
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <h2 style="margin-bottom: 16px;">New Conversation</h2>
        <input type="text" id="newThreadName" placeholder="Conversation name..." 
               style="width: 100%; padding: 12px; border: 1px solid var(--border-color); 
                      border-radius: 8px; font-size: 14px; margin-bottom: 16px;
                      background: var(--bg-primary); color: var(--text-primary);">
        <button onclick="createNewThread()" 
                style="width: 100%; padding: 12px; background: var(--accent-color); 
                       color: white; border: none; border-radius: 8px; 
                       font-weight: 500; cursor: pointer;">
            Create
        </button>
    `;
    openModal();
}

async function createNewThread() {
    const name = document.getElementById('newThreadName').value.trim();
    
    if (!name) {
        alert('Please enter a conversation name');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/threads/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey
            },
            body: JSON.stringify({ thread_name: name })
        });
        
        const data = await response.json();
        closeModal();
        await loadConversations();
        loadThread(data.thread_id, data.thread_name);
    } catch (error) {
        alert('Error creating thread: ' + error.message);
    }
}

// Message Rendering
function renderMessages(messages) {
    const container = document.getElementById('messagesContainer');
    
    if (!messages || messages.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">💬</div>
                <h2>Start chatting</h2>
                <p>Type a message below to begin the conversation</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = messages.map(msg => {
        const isUser = msg.role === 'user';
        const avatar = isUser ? '👤' : '🤖';
        
        return `
            <div class="message ${msg.role}">
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    ${formatMessage(msg.content)}
                </div>
            </div>
        `;
    }).join('');
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

function formatMessage(content) {
    // Basic markdown formatting
    content = content.replace(/``````/g, '<pre><code>$2</code></pre>');
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    content = content.replace(/\*(.*?)\*/g, '<em>$1</em>');
    content = content.replace(/\n/g, '<br>');
    return content;
}

function appendMessage(role, content) {
    const container = document.getElementById('messagesContainer');
    const isEmpty = container.querySelector('.empty-state');
    
    if (isEmpty) {
        container.innerHTML = '';
    }
    
    const isUser = role === 'user';
    const avatar = isUser ? '👤' : '🤖';
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${role === 'assistant' ? '<div class="loading-dots"><span></span><span></span><span></span></div>' : formatMessage(content)}
        </div>
    `;
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
    
    return messageDiv;
}

// Send Message
async function sendMessage() {
    if (!currentThreadId) {
        alert('Please select or create a conversation first');
        return;
    }
    
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Disable input
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    input.disabled = true;
    
    // Show user message
    appendMessage('user', message);
    input.value = '';
    autoResize(input);
    
    // Show loading for assistant
    const loadingMsg = appendMessage('assistant', '');
    
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey
            },
            body: JSON.stringify({
                thread_id: currentThreadId,
                message: message,
                max_tokens: 3000,
                top_k: 20
            })
        });
        
        const data = await response.json();
        
        // Update loading message with response
        loadingMsg.querySelector('.message-content').innerHTML = formatMessage(data.assistant_response);
        
        // Update token count
        document.getElementById('tokenCount').textContent = `${data.token_count} tokens | ${data.retrieved_messages} context msgs`;
        
    } catch (error) {
        loadingMsg.querySelector('.message-content').innerHTML = 
            '<span style="color: red;">Error: ' + error.message + '</span>';
    } finally {
        sendBtn.disabled = false;
        input.disabled = false;
        input.focus();
    }
}

// Input handling
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

// Modal
function openModal() {
    document.getElementById('modal').classList.add('active');
}

function closeModal() {
    document.getElementById('modal').classList.remove('active');
}

// Settings
function showSettings() {
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <h2 style="margin-bottom: 16px;">⚙️ Settings</h2>
        <div style="margin-bottom: 16px;">
            <label style="display: block; margin-bottom: 8px; font-weight: 500;">API Key</label>
            <input type="text" value="${apiKey}" readonly
                   style="width: 100%; padding: 12px; border: 1px solid var(--border-color); 
                          border-radius: 8px; font-size: 14px; background: var(--bg-secondary);
                          color: var(--text-primary);">
        </div>
        <button onclick="logout()" 
                style="width: 100%; padding: 12px; background: #dc2626; 
                       color: white; border: none; border-radius: 8px; 
                       font-weight: 500; cursor: pointer;">
            Logout
        </button>
    `;
    openModal();
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('recallgpt_api_key');
        apiKey = '';
        currentThreadId = null;
        closeModal();
        showApiKeySetup();
    }
}

// Analytics
async function showAnalytics() {
    try {
        const response = await fetch(`${API_BASE}/analytics`, {
            headers: { 'X-API-Key': apiKey }
        });
        
        const data = await response.json();
        
        const modalBody = document.getElementById('modalBody');
        modalBody.innerHTML = `
            <h2 style="margin-bottom: 16px;">📊 Analytics</h2>
            <div style="display: grid; gap: 12px;">
                <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: 600;">${data.total_retrievals}</div>
                    <div style="color: var(--text-secondary); font-size: 14px;">Total Queries</div>
                </div>
                <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: 600;">${data.total_tokens_used}</div>
                    <div style="color: var(--text-secondary); font-size: 14px;">Tokens Used</div>
                </div>
                <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: 600;">${data.avg_retrieved_messages.toFixed(1)}</div>
                    <div style="color: var(--text-secondary); font-size: 14px;">Avg Context Messages</div>
                </div>
                <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px;">
                    <div style="font-size: 24px; font-weight: 600;">${data.threads_accessed}</div>
                    <div style="color: var(--text-secondary); font-size: 14px;">Active Threads</div>
                </div>
            </div>
        `;
        openModal();
    } catch (error) {
        alert('Error loading analytics: ' + error.message);
    }
}

// Dark mode
function toggleDarkMode() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Load theme preference
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);

// Mobile sidebar toggle
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}
