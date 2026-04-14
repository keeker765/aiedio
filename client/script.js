// API Configuration
const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000';

// Global State
let currentTopic = '';
let currentKnowledge = null;
let currentStoryboard = null;
let currentTaskId = null;
let wsConnection = null;

// DOM Elements
const topicSelectView = document.getElementById('topicSelectView');
const storyboardView = document.getElementById('storyboardView');
const videoProgressView = document.getElementById('videoProgressView');

const trendsGrid = document.getElementById('trendsGrid');
const trendsLoading = document.getElementById('trendsLoading');
const errorMessage = document.getElementById('errorMessage');

const customTopicInput = document.getElementById('customTopicInput');
const submitCustomTopicBtn = document.getElementById('submitCustomTopicBtn');

const backToTopicBtn = document.getElementById('backToTopicBtn');
const storyBackgroundDiv = document.getElementById('storyBackground');
const knowledgeSourcesDiv = document.getElementById('knowledgeSources');
const storyboardGrid = document.getElementById('storyboardGrid');
const regenerateStoryboardBtn = document.getElementById('regenerateStoryboardBtn');
const generateVideoBtn = document.getElementById('generateVideoBtn');

const backToStoryboardBtn = document.getElementById('backToStoryboardBtn');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const scenePreviews = document.getElementById('scenePreviews');
const finalVideoSection = document.getElementById('finalVideoSection');
const finalVideo = document.getElementById('finalVideo');
const downloadLink = document.getElementById('downloadLink');
const newVideoBtn = document.getElementById('newVideoBtn');

// ============ Utility Functions ============
function showView(viewName) {
    topicSelectView.classList.add('hidden');
    storyboardView.classList.add('hidden');
    videoProgressView.classList.add('hidden');
    
    if (viewName === 'topic') {
        topicSelectView.classList.remove('hidden');
    } else if (viewName === 'storyboard') {
        storyboardView.classList.remove('hidden');
    } else if (viewName === 'video') {
        videoProgressView.classList.remove('hidden');
    }
}

function showError(msg) {
    errorMessage.textContent = msg;
    errorMessage.classList.remove('hidden');
    setTimeout(() => {
        errorMessage.classList.add('hidden');
    }, 5000);
}

function hideError() {
    errorMessage.classList.add('hidden');
}

function setLoading(el, isLoading) {
    if (isLoading) {
        el.classList.remove('hidden');
    } else {
        el.classList.add('hidden');
    }
}

// ============ F2: Topic Selection ============
async function loadTrends() {
    setLoading(trendsLoading, true);
    hideError();
    
    try {
        const response = await fetch(`${API_BASE}/api/trends`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const trends = await response.json();
        renderTrends(trends);
    } catch (err) {
        console.error('Failed to load trends:', err);
        showError('Failed to load trends. Please make sure the backend is running.');
        trendsGrid.innerHTML = '<div class="error-message">Unable to load trends. Is the backend running?</div>';
    } finally {
        setLoading(trendsLoading, false);
    }
}

function renderTrends(trends) {
    if (!trends || trends.length === 0) {
        trendsGrid.innerHTML = '<div class="error-message">No trends available.</div>';
        return;
    }
    
    trendsGrid.innerHTML = trends.map(trend => `
        <div class="trend-card" data-topic="${escapeHtml(trend.title)}">
            <div class="trend-title">${escapeHtml(trend.title)}</div>
            <div class="trend-platform">${escapeHtml(trend.platform || 'Unknown')}</div>
            ${trend.hot_value ? `<div class="trend-hot">🔥 ${escapeHtml(trend.hot_value)}</div>` : ''}
        </div>
    `).join('');
    
    // Add click handlers to trend cards
    document.querySelectorAll('.trend-card').forEach(card => {
        card.addEventListener('click', () => {
            const topic = card.dataset.topic;
            if (topic) {
                fetchKnowledge(topic);
            }
        });
    });
}

async function fetchKnowledge(topic) {
    currentTopic = topic;
    showView('storyboard');
    storyBackgroundDiv.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><span>Loading background knowledge...</span></div>';
    knowledgeSourcesDiv.innerHTML = '';
    storyboardGrid.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><span>Generating storyboard...</span></div>';
    
    try {
        // Step 1: POST /api/knowledge
        const knowledgeResponse = await fetch(`${API_BASE}/api/knowledge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic })
        });
        
        if (!knowledgeResponse.ok) {
            throw new Error(`Knowledge API error: ${knowledgeResponse.status}`);
        }
        
        currentKnowledge = await knowledgeResponse.json();
        renderKnowledge(currentKnowledge);
        
        // Step 2: POST /api/storyboard
        const storyboardResponse = await fetch(`${API_BASE}/api/storyboard`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                topic: topic, 
                knowledge: currentKnowledge.sources || [] 
            })
        });
        
        if (!storyboardResponse.ok) {
            throw new Error(`Storyboard API error: ${storyboardResponse.status}`);
        }
        
        currentStoryboard = await storyboardResponse.json();
        renderStoryboard(currentStoryboard);
        
    } catch (err) {
        console.error('Failed to fetch knowledge/storyboard:', err);
        showError(`Failed to generate storyboard: ${err.message}`);
        showView('topic');
    }
}

function renderKnowledge(knowledge) {
    // Render story background
    const background = knowledge.story_background || 
        `Based on "${knowledge.topic}", here is the collected background knowledge:`;
    storyBackgroundDiv.innerHTML = `<p>${escapeHtml(background)}</p>`;
    
    // Render knowledge sources
    if (knowledge.sources && knowledge.sources.length > 0) {
        knowledgeSourcesDiv.innerHTML = '<h3>📚 Sources</h3>' + knowledge.sources.map(source => `
            <div class="source-card">
                <div class="source-title">📄 ${escapeHtml(source.platform)}: ${escapeHtml(source.title)}</div>
                <div class="source-summary">${escapeHtml(source.summary)}</div>
                ${source.url ? `<a href="${escapeHtml(source.url)}" target="_blank" class="source-url">View Source →</a>` : ''}
            </div>
        `).join('');
    } else {
        knowledgeSourcesDiv.innerHTML = '<p class="source-card">No additional sources found.</p>';
    }
}

function renderStoryboard(storyboard) {
    const scenes = storyboard.scenes || [];
    const title = storyboard.title || currentTopic;
    
    if (scenes.length === 0) {
        storyboardGrid.innerHTML = '<div class="error-message">No storyboard scenes generated.</div>';
        return;
    }
    
    storyboardGrid.innerHTML = scenes.map((scene, idx) => `
        <div class="scene-card" data-scene-index="${idx}">
            <div class="scene-number">Scene ${idx + 1} / ${scenes.length}</div>
            <div class="scene-description" id="sceneDesc_${idx}">${escapeHtml(scene.description || scene.visual_prompt || scene.prompt || 'No description')}</div>
            <textarea class="scene-edit" data-scene="${idx}" rows="3">${escapeHtml(scene.description || scene.visual_prompt || scene.prompt || '')}</textarea>
        </div>
    `).join('');
    
    // Add edit handlers
    document.querySelectorAll('.scene-edit').forEach(textarea => {
        textarea.addEventListener('change', (e) => {
            const sceneIdx = parseInt(e.target.dataset.scene);
            if (currentStoryboard && currentStoryboard.scenes && currentStoryboard.scenes[sceneIdx]) {
                currentStoryboard.scenes[sceneIdx].description = e.target.value;
            }
        });
    });
}

// ============ F3: Storyboard Actions ============
async function regenerateStoryboard() {
    if (!currentTopic || !currentKnowledge) {
        showError('Missing topic or knowledge data');
        return;
    }
    
    storyboardGrid.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><span>Regenerating storyboard...</span></div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/storyboard`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                topic: currentTopic, 
                knowledge: currentKnowledge.sources || [] 
            })
        });
        
        if (!response.ok) throw new Error(`Storyboard API error: ${response.status}`);
        
        currentStoryboard = await response.json();
        renderStoryboard(currentStoryboard);
    } catch (err) {
        console.error('Failed to regenerate storyboard:', err);
        showError(`Failed to regenerate: ${err.message}`);
    }
}

async function startVideoGeneration() {
    if (!currentStoryboard || !currentStoryboard.scenes) {
        showError('No storyboard available');
        return;
    }
    
    showView('video');
    resetVideoProgress();
    
    try {
        const response = await fetch(`${API_BASE}/api/video/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ storyboard: currentStoryboard })
        });
        
        if (!response.ok) throw new Error(`Video API error: ${response.status}`);
        
        const data = await response.json();
        currentTaskId = data.task_id;
        
        // Connect WebSocket for progress updates
        connectWebSocket(currentTaskId);
        
    } catch (err) {
        console.error('Failed to start video generation:', err);
        showError(`Failed to start video generation: ${err.message}`);
        showView('storyboard');
    }
}

// ============ F4: Video Generation Progress ============
function resetVideoProgress() {
    progressBar.style.width = '0%';
    progressText.textContent = 'Preparing...';
    scenePreviews.innerHTML = '';
    finalVideoSection.classList.add('hidden');
    if (wsConnection) {
        wsConnection.close();
        wsConnection = null;
    }
}

function connectWebSocket(taskId) {
    const wsUrl = `${WS_BASE}/ws/video/${taskId}`;
    wsConnection = new WebSocket(wsUrl);
    
    wsConnection.onopen = () => {
        console.log('WebSocket connected');
    };
    
    wsConnection.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
        }
    };
    
    wsConnection.onerror = (err) => {
        console.error('WebSocket error:', err);
        progressText.textContent = 'Connection error. Please check if backend is running.';
    };
    
    wsConnection.onclose = () => {
        console.log('WebSocket closed');
    };
}

function handleWebSocketMessage(data) {
    switch (data.event) {
        case 'scene_start':
            const total = data.total || currentStoryboard?.scenes?.length || 1;
            const progress = ((data.scene - 1) / total) * 100;
            progressBar.style.width = `${progress}%`;
            progressText.textContent = `Generating scene ${data.scene} of ${total}...`;
            break;
            
        case 'scene_done':
            // Add preview card for completed scene
            const previewCard = document.createElement('div');
            previewCard.className = 'scene-preview-card';
            previewCard.innerHTML = `
                <video class="scene-preview-video" controls>
                    <source src="${data.preview_url}" type="video/mp4">
                    Your browser does not support video playback.
                </video>
                <div class="scene-preview-label">Scene ${data.scene} Complete</div>
            `;
            scenePreviews.appendChild(previewCard);
            
            // Update progress
            const newProgress = (data.scene / data.total) * 100;
            progressBar.style.width = `${newProgress}%`;
            progressText.textContent = `Scene ${data.scene} of ${data.total} complete`;
            break;
            
        case 'complete':
            progressBar.style.width = '100%';
            progressText.textContent = 'Video generation complete!';
            
            // Show final video
            finalVideoSection.classList.remove('hidden');
            finalVideo.src = data.video_url;
            downloadLink.href = data.video_url;
            
            if (wsConnection) {
                wsConnection.close();
                wsConnection = null;
            }
            break;
            
        case 'error':
            progressText.textContent = `Error: ${data.message}`;
            showError(data.message);
            break;
            
        default:
            console.log('Unknown event:', data);
    }
}

// ============ Navigation ============
function backToTopic() {
    showView('topic');
    currentTopic = '';
    currentKnowledge = null;
    currentStoryboard = null;
}

function backToStoryboard() {
    showView('storyboard');
    if (wsConnection) {
        wsConnection.close();
        wsConnection = null;
    }
}

function newVideo() {
    showView('topic');
    currentTopic = '';
    currentKnowledge = null;
    currentStoryboard = null;
    currentTaskId = null;
    if (wsConnection) {
        wsConnection.close();
        wsConnection = null;
    }
}

// ============ Helper: Escape HTML ============
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ============ Event Listeners ============
submitCustomTopicBtn.addEventListener('click', () => {
    const topic = customTopicInput.value.trim();
    if (topic) {
        fetchKnowledge(topic);
    } else {
        showError('Please enter a topic');
    }
});

customTopicInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const topic = customTopicInput.value.trim();
        if (topic) {
            fetchKnowledge(topic);
        }
    }
});

backToTopicBtn.addEventListener('click', backToTopic);
backToStoryboardBtn.addEventListener('click', backToStoryboard);
regenerateStoryboardBtn.addEventListener('click', regenerateStoryboard);
generateVideoBtn.addEventListener('click', startVideoGeneration);
newVideoBtn.addEventListener('click', newVideo);

// ============ Initialize ============
loadTrends();