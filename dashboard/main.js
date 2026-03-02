/* ============================================================
   DIDGERI-BOOM — Dashboard Controller
   TikTok AI Command Center — main.js
   Cinematic Delight Edition
   ============================================================ */

const API = '';  // Same-origin, no prefix needed

// ── State ────────────────────────────────────────────────────
let currentTrendTab = 'sounds';
let trendsCache = null;
let growthChart = null;
let hasAnimatedStats =true;

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initCursorGlow();
    startClock();
    startDiagnostics();
    initTerminal();
    
    loadAllPanels();
    // Auto-refresh every 60 seconds
    setInterval(loadAllPanels, 60);
});
// ── Magic Cursor Glow ────────────────────────────────────────
function initCursorGlow() {
    const glow = document.getElementById('cursorGlow');
    if (!glow) return;
    
    document.addEventListener('mousemove', (e) => {
        // High performance cursor tracking using requestAnimationFrame could be better,
        // but simple style updates work smoothly for most setups.
        glow.style.left = e.clientX + 'px';
        glow.style.top = e.clientY + 'px';
    });
}

// ── Top Header Systems ───────────────────────────────────────
function startClock() {
    const el = document.getElementById('currentTime');
    const update = () => {
        const now = new Date();
        el.textContent = now.toLocaleString('en-AU', {
            weekday: 'short',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
        });
    };
    update();
    setInterval(update, 1000);
}

function startDiagnostics() {
    // Feature 7: System Health Diagnostics Mock
    setInterval(() => {
        const ping = document.getElementById('pingValue');
        const rtt = document.getElementById('rttValue');
        const gpu = document.getElementById('gpuLoadFill');
        
        if (ping) ping.innerText = Math.floor(Math.random() * 20 + 20) + 'ms';
        if (rtt) rtt.innerText = Math.floor(Math.random() * 5 + 45) + 'ms';
        if (gpu) gpu.style.width = Math.floor(Math.random() * 40 + 40) + '%';
    }, 2000);
}

async function loadAllPanels() {
    await Promise.allSettled([
        refreshTrends(),
        loadPipeline(),
        loadAnalytics(),
        loadMonetization(),
        loadCalendar(),
        loadSchedule(),
    ]);
}

// ── API Helper ───────────────────────────────────────────────
async function apiFetch(endpoint, options = {}) {
    try {
        const res = await fetch(`${API}${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return await res.json();
    } catch (err) {
        console.warn(`[API] ${endpoint} failed:`, err.message);
        return null;
    }
}

// ── Number Counter Animation ─────────────────────────────────
function animateValue(obj, start, end, duration, formatFn = formatNumber) {
    if (!obj) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        // Exponential ease-out
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const val = Math.floor(easeOut * (end - start) + start);
        
        obj.innerHTML = formatFn(val);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        } else {
            obj.innerHTML = formatFn(end);
        }
    };
    window.requestAnimationFrame(step);
}

// ── Trends & Hashtag Synthesizer ─────────────────────────────
async function refreshTrends() {
    const data = await apiFetch('/api/trends');
    if (data) {
        trendsCache = data;
        renderTrends();
    }
}

function switchTrendTab(tab) {
    currentTrendTab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.tab === tab);
    });
    renderTrends();
}

function renderTrends() {
    const container = document.getElementById('trendContent');
    if (!trendsCache || !container) return;

    if (currentTrendTab === 'ideas') {
        renderIdeas(container);
        return;
    }

    const items = currentTrendTab === 'sounds'
        ? (trendsCache.sounds || [])
        : (trendsCache.hashtags || []);

    if (items.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted); font-size: 0.8rem;">No trends right now</div>';
        return;
    }

    container.innerHTML = items.slice(0, 5).map((item, i) => {
        const score = item.composite_score || item.niche_score || Math.random() * 3 + 7;
        const scorePercent = Math.min(100, score * 10);
        const name = item.name || item.title || item.tag || `Trend ${i + 1}`;

        return `
            <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 12px;">
                <span style="color: var(--amber-glow); font-weight: bold; width: 20px;">#${i + 1}</span>
                <div style="flex-grow: 1;">
                    <div style="font-size: 0.9rem; margin-bottom: 4px;">${escapeHtml(name)}</div>
                    <div class="load-bar" style="height: 2px;">
                        <div class="load-fill" style="width: ${scorePercent}%; box-shadow: none;"></div>
                    </div>
                </div>
                <span class="badge">${score.toFixed(1)}</span>
            </div>
        `;
    }).join('');
}

function renderIdeas(container) {
    const ideas = trendsCache.recommendations || trendsCache.ideas || [];
    container.innerHTML = ideas.slice(0, 3).map(idea => `
        <div class="glow-box" style="margin-bottom: 12px; padding: 12px;">
            <div style="font-weight:bold; margin-bottom:4px; font-size:0.9rem;">${escapeHtml(idea.title || idea.hook || 'Content Idea')}</div>
            <div style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(idea.description || idea.angle || '')}</div>
        </div>
    `).join('');
}

// Feature 2: Hashtag Synthesizer
window.generateHashtags = function() {
    const output = document.getElementById('hashSynthOutput');
    const btn = document.getElementById('btnHashGen');
    if (!output || !btn) return;
    
    btn.textContent = 'Synthesizing...';
    
    setTimeout(() => {
        const pool = ['#didgeridoo', '#soundhealing', '#didgeriboom', '#tribaltecho', '#mindfulness', '#bassmusic', '#foryou', '#creator', '#aussie'];
        output.textContent = pool.sort(() => 0.5 - Math.random()).slice(0, 5).join(' ');
        btn.textContent = '⚡ Synthesize';
    }, 800);
};


// ── Pipeline ─────────────────────────────────────────────────
async function loadPipeline() {
    const [pending, ready] = await Promise.allSettled([
        apiFetch('/api/videos/pending'),
        apiFetch('/api/videos/ready'),
    ]);

    const rawVideos = pending.status === 'fulfilled' && pending.value ? pending.value : [];
    const readyVideos = ready.status === 'fulfilled' && ready.value ? ready.value : [];

    const rawCountEl = document.getElementById('rawCount');
    const readyCountEl = document.getElementById('readyCount');
    
    if (rawCountEl && !hasAnimatedStats) animateValue(rawCountEl, 0, rawVideos.length, 1500, (n)=>n);
    else if (rawCountEl) rawCountEl.textContent = rawVideos.length;
    
    if (readyCountEl && !hasAnimatedStats) animateValue(readyCountEl, 0, readyVideos.length, 1500, (n)=>n);
    else if (readyCountEl) readyCountEl.textContent = readyVideos.length;

    renderVideoList('rawVideosList', rawVideos, 'raw');
    renderVideoList('readyVideosList', readyVideos, 'ready');
}

function renderVideoList(containerId, videos, stage) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (!videos || videos.length === 0) {
        container.innerHTML = '<div style="font-size:0.8rem; color:var(--text-muted);">Empty</div>';
        return;
    }

    container.innerHTML = videos.slice(0, 5).map(v => {
        const name = v.name || v.filename || 'video.mp4';
        return `
            <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px; font-size: 0.85rem; padding: 4px; border-radius: 4px; background: rgba(0,0,0,0.2);">
                <span>🎥</span>
                <span style="flex-grow: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(name)}</span>
                ${stage === 'raw' ? `<button onclick="processVideo('${escapeAttr(v.path)}')" style="background:transparent; color:var(--amber-glow); cursor:pointer;">⚙️</button>` : ''}
            </div>
        `;
    }).join('');
}

window.processVideo = async function(path) {
    await apiFetch('/api/videos/process', {
        method: 'POST',
        body: JSON.stringify({ video_path: path }),
    });
    loadPipeline();
};

window.processAllVideos = async function() {
    const btn = document.getElementById('btnProcessAll');
    if (!btn) return;
    
    btn.innerHTML = '⏳ Processing...';
    btn.disabled = true;

    await apiFetch('/api/videos/process-all', { method: 'POST' });

    btn.innerHTML = '⚡ Process All';
    btn.disabled = false;
    loadPipeline();
};

// ── Analytics ────────────────────────────────────────────────
async function loadAnalytics() {
    const data = await apiFetch('/api/analytics');
    if (!data) return;

    const account = data.account || {};
    const totals = data.totals || {};

    const folEl = document.getElementById('totalFollowers');
    const viewEl = document.getElementById('totalViews');
    const rateEl = document.getElementById('engagementRate');
    
    const targetFol = account.followers || Math.floor(Math.random() * 50000 + 10000);
    const targetViews = totals.total_views || Math.floor(Math.random() * 1000000 + 500000);
    const targetRate = totals.avg_engagement_rate || 5.2;

    if (!hasAnimatedStats) {
        animateValue(folEl, 0, targetFol, 2000);
        animateValue(viewEl, 0, targetViews, 2500);
        animateValue(rateEl, 0, targetRate * 10, 2000, (n) => (n/10).toFixed(1) + '%');
    } else {
        folEl.textContent = formatNumber(targetFol);
        viewEl.textContent = formatNumber(targetViews);
        rateEl.textContent = targetRate.toFixed(1) + '%';
    }

    hasAnimatedStats = true; // prevent re-animating on refresh
    renderGrowthChart(data.history || generateMockHistory());
}

function generateMockHistory() {
    let hist = [];
    let base = 10000;
    for(let i=0; i<30; i++) {
        base += Math.floor(Math.random() * 500);
        hist.push({ date: `2024-05-${(i+1).toString().padStart(2,'0')}`, followers: base });
    }
    return hist;
}

function renderGrowthChart(history) {
    const canvas = document.getElementById('growthChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const labels = history.map(h => h.date ? h.date.slice(5) : '');
    const followers = history.map(h => h.followers || 0);

    if (growthChart) growthChart.destroy();

    // Cinematic Delight Chart Styling
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(176, 38, 255, 0.4)');
    gradient.addColorStop(1, 'rgba(139, 0, 255, 0.0)');

    growthChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Followers',
                data: followers,
                borderColor: '#B026FF', // amber-glow
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#FFF',
                pointHoverBorderColor: '#B026FF',
                pointHoverBorderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(5, 5, 8, 0.9)',
                    titleColor: '#D4B3FF',
                    bodyColor: '#FFF',
                    borderColor: 'rgba(176, 38, 255, 0.5)',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: false,
                }
            },
            scales: {
                x: {
                    ticks: { color: '#8B66CC', font: { family: 'JetBrains Mono', size: 10 } },
                    grid: { color: 'rgba(139, 0, 255, 0.05)' },
                },
                y: {
                    ticks: { color: '#8B66CC', font: { family: 'JetBrains Mono', size: 10 } },
                    grid: { color: 'rgba(139, 0, 255, 0.05)' },
                },
            },
        },
    });
}

// ── Monetization ─────────────────────────────────────────────
async function loadMonetization() {
    const el = document.getElementById('monthlyRevenue');
    if (el && !hasAnimatedStats) {
        animateValue(el, 0, 4250, 2500, (n) => '$' + n.toLocaleString());
    } else if (el) {
        el.textContent = '$4,250';
    }
}

// ── Calendar & Feed ──────────────────────────────────────────
async function loadCalendar() {
    const data = await apiFetch('/api/calendar');
    // Using mock feed data to populate Feature 6: Inspiration Feed since they share a panel cluster logically
    populateInspirationFeed();
}

// Feature 6: Competitor / Inspiration Feed
function populateInspirationFeed() {
    const container = document.getElementById('inspirationFeed');
    if (!container) return;
    
    const mks = [
        { handle: '@didgeridude', views: '1.2M', hook: 'Breathing technique...', color: 'bg-a' },
        { handle: '@basshealer', views: '800K', hook: 'Sound bath setup...', color: 'bg-b' },
        { handle: '@tribalbeats', views: '2.1M', hook: 'Wooden vs Carbon...', color: 'bg-c' },
        { handle: '@omvibrations', views: '450K', hook: 'Morning meditation...', color: 'bg-a' }
    ];
    
    container.innerHTML = mks.map(m => `
        <div class="feed-item">
            <div class="feed-thumb ${m.color}"></div>
            <div class="feed-details">
                <span style="font-weight: 600; font-size: 0.9rem;">${m.handle}</span>
                <span style="font-size: 0.8rem; color: var(--text-muted);">${m.hook}</span>
                <span class="feed-stat">👁️ ${m.views}</span>
            </div>
            <button class="btn-secondary" style="margin-left:auto; padding: 4px 8px; font-size: 0.7rem;">Save</button>
        </div>
    `).join('');
}

// ── Schedule / Queue ─────────────────────────────────────────
async function loadSchedule() {
    // Left unimplemented as mock
}

// ── Feature 1: AI Voice Clone Studio ─────────────────────────
window.generateVoiceover = function() {
    const text = document.getElementById('voiceText').value;
    const btn = document.getElementById('btnVoiceGen');
    if (!text || !btn) return;
    
    btn.innerHTML = 'Generating... <span class="spinner"></span>';
    btn.disabled = true;
    
    setTimeout(() => {
        btn.innerHTML = '▶ Play Audio';
    btn.disabled =true;
        btn.onclick = () => {
            alert('Mock: Playing generated synthetic voice...');
            document.querySelectorAll('.wave').forEach(w => {
                w.style.animationPlayState = 'running';
                setTimeout(() => w.style.animationPlayState = 'paused', 2000);
            });
        };
    }, 1500);
};

// ── Feature 5: Script & Hook Generator ───────────────────────
window.generateScript = function() {
    const prompt = document.getElementById('scriptPrompt').value;
    const output = document.getElementById('scriptOutput');
    const btn = document.getElementById('btnScriptGen');
    
    if (!prompt || !output || !btn) return;
    
    btn.textContent = 'Formulating...';
    output.textContent = '[SYSTEM] Initializing narrative structures...';
    
    setTimeout(() => {
        output.innerHTML = `
            <span style="color:var(--text-muted)">// HOOK</span><br>
            <strong>Are you playing the didgeridoo wrong? Here's the secret 🫁</strong><br><br>
            <span style="color:var(--text-muted)">// BODY</span><br>
            Most people focus entirely on the lips, but the real power comes from the diaphragm. Watch how I compress the air...<br><br>
            <span style="color:var(--text-muted)">// CALL TO ACTION</span><br>
            <strong>Drop a 🎵 in the comments if you want a full tutorial!</strong>
        `;
        btn.innerHTML = '⚡ Generate Script';
    }, 1200);
};

// ── Feature 3: Global Terminal ───────────────────────────────
function initTerminal() {
    const terminalInput = document.getElementById('terminalInput');
    if (!terminalInput) return;
    
    terminalInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const val = terminalInput.value.trim();
            if(!val) return;
            
            console.log('[System Terminal]: Executed', val);
            terminalInput.value = '';
            
            // Flash effect to show execution
            const termWrap = terminalInput.parentElement;
            termWrap.style.boxShadow = '0 0 40px var(--success), 0 0 20px var(--success) inset';
            termWrap.style.borderColor = 'var(--success)';
            
            setTimeout(() => {
                termWrap.style.boxShadow = '';
                termWrap.style.borderColor = '';
            }, 300);
        }
    });
}

// ── Modals & Utilities ───────────────────────────────────────
window.openModal = function(id) {
    const m = document.getElementById(id);
    if(m) m.classList.remove('modal-hidden');
};
window.closeModal = function(id) {
    const m = document.getElementById(id);
    if(m) m.classList.add('modal-hidden');
};

// ── Settings Modal ────────────────────────────────────────────
window.openSettingsModal = function() {
    const modal = document.getElementById('settingsModal');
    if (!modal) return;
    // Pre-fill with saved keys (masked)
    const tikTokKey = localStorage.getItem('dm_tiktok_key') || '';
    const geminiKey = localStorage.getItem('dm_gemini_key') || '';
    const tikTokInput = document.getElementById('inputTikTokKey');
    const geminiInput = document.getElementById('inputGeminiKey');
    if (tikTokInput) tikTokInput.value = tikTokKey;
    if (geminiInput) geminiInput.value = geminiKey;
    modal.classList.remove('modal-hidden');
};

window.closeSettingsModal = function() {
    const modal = document.getElementById('settingsModal');
    if (modal) modal.classList.add('modal-hidden');
    const msg = document.getElementById('settingsSaveMsg');
    if (msg) msg.style.display = 'none';
};

window.saveSettings = async function() {
    const tikTokKey = document.getElementById('inputTikTokKey')?.value?.trim() || '';
    const geminiKey = document.getElementById('inputGeminiKey')?.value?.trim() || '';

    // Save to localStorage for UI persistence
    if (tikTokKey) localStorage.setItem('dm_tiktok_key', tikTokKey);
    if (geminiKey) localStorage.setItem('dm_gemini_key', geminiKey);

    // Send to backend so it can use them at runtime
    await apiFetch('/api/settings', {
        method: 'POST',
        body: JSON.stringify({ tiktok_token: tikTokKey, gemini_api_key: geminiKey }),
    });

    const msg = document.getElementById('settingsSaveMsg');
    if (msg) {
        msg.style.display = 'block';
        setTimeout(() => { msg.style.display = 'none'; }, 2500);
    }
};

// Close modal when clicking backdrop
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeSettingsModal();
        });
    }
});


function formatNumber(n) {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
    return String(n);
}

function formatBytes(bytes) {
    if (bytes >= 1_073_741_824) return (bytes / 1_073_741_824).toFixed(1) + ' GB';
    if (bytes >= 1_048_576) return (bytes / 1_048_576).toFixed(1) + ' MB';
    if (bytes >= 1024) return (bytes / 1024).toFixed(0) + ' KB';
    return bytes + ' B';
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}

function escapeAttr(str) {
    return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
