// ============================================
// FAKE INTERNSHIP DETECTOR — Client Script
// ============================================

// --- Global Toast Notification System ---
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Add colour bar depending on type
    let color = '#00d4ff';
    if (type === 'success') color = '#00ff88';
    if (type === 'danger') color = '#ff3366';
    if (type === 'warning') color = '#ffaa00';
    
    toast.style.borderLeft = `4px solid ${color}`;
    toast.innerHTML = `
        <div class="toast-content">${message}</div>
    `;
    
    container.appendChild(toast);
    
    // Trigger slide-in
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after 4s
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// --- Loading indicator helper ---
function setBtnLoading(btnId, isLoading, originalHtml = '') {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    
    if (isLoading) {
        btn.disabled = true;
        btn.setAttribute('data-original-html', btn.innerHTML);
        btn.innerHTML = `<span class="loading-spinner"></span> Scanning...`;
    } else {
        btn.disabled = false;
        btn.innerHTML = originalHtml || btn.getAttribute('data-original-html') || 'SUBMIT';
    }
}

// --- Animated Counter System ---
function animateCounter(elementId, targetValue, duration = 1500, isPercentage = false) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const start = 0;
    const end = parseFloat(targetValue);
    const range = end - start;
    let current = start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / (range || 1)));
    
    const timer = setInterval(() => {
        if (range === 0) {
            element.innerText = isPercentage ? "0%" : "0";
            clearInterval(timer);
            return;
        }
        
        current += (range / 60);
        if ((range > 0 && current >= end) || (range < 0 && current <= end)) {
            element.innerText = isPercentage ? `${end.toFixed(1)}%` : Math.round(end).toLocaleString();
            clearInterval(timer);
        } else {
            element.innerText = isPercentage ? `${current.toFixed(1)}%` : Math.round(current).toLocaleString();
        }
    }, 16); // ~60fps
}

// --- Update Custom Gauge Percentage ---
function updateGauge(gaugeId, val) {
    const gauge = document.getElementById(gaugeId);
    if (!gauge) return;
    
    gauge.style.setProperty('--value', val);
    const txt = gauge.querySelector('.gauge-value');
    if (txt) {
        txt.innerText = `${Math.round(val)}%`;
    }
}

// ─────────────────────────────────────────────────────────────
//  INTERNSHIP ANALYZER
// ─────────────────────────────────────────────────────────────

async function analyzeInternship() {
    const company_el = document.getElementById('company_name');
    const company = company_el.value ? company_el.value.trim() : '';
    const stipend = document.getElementById('stipend').value;
    const description = document.getElementById('description').value;

    if (!description || description.trim() === '') {
        showToast('Please paste a job description first.', 'warning');
        return;
    }

    setBtnLoading('btn-analyze', true);
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: company,
                stipend: stipend,
                description: description
            })
        });

        const data = await response.json();
        
        if (response.status >= 400) {
            showToast(data.error || 'Server error during scan', 'danger');
            setBtnLoading('btn-analyze', false);
            return;
        }

        // Hide placeholder and show results
        document.getElementById('result-placeholder').classList.add('hidden');
        const resultsEl = document.getElementById('analysis-results');
        resultsEl.classList.remove('hidden');
        
        // Update verdict badge styling
        const badge = document.getElementById('verdict-badge');
        badge.innerText = `VERDICT: ${data.result.toUpperCase()}`;
        badge.className = 'verdict-badge';
        
        if (data.result === 'Genuine') {
            badge.classList.add('bg-success');
            showToast('Scan Complete: Offer looks Genuine.', 'success');
        } else if (data.result === 'Suspicious') {
            badge.classList.add('bg-warning');
            showToast('Scan Complete: Suspicious signals detected.', 'warning');
        } else {
            badge.classList.add('bg-danger');
            showToast('Alert: High probability of recruitment scam!', 'danger');
        }

        // Update Gauge and progress bars
        updateGauge('gauge-risk', data.scam_score);
        
        const scoreBar = document.getElementById('scam-score-bar');
        scoreBar.style.width = `${data.scam_score}%`;
        
        // Set bar colour depending on risk
        scoreBar.className = 'progress-bar';
        if (data.scam_score >= 70) scoreBar.classList.add('bg-danger');
        else if (data.scam_score >= 40) scoreBar.classList.add('bg-warning');
        else scoreBar.classList.add('bg-success');

        document.getElementById('scam-score-text').innerText = data.scam_score.toFixed(2);

        // Stipend status
        document.getElementById('stipend-status').innerText = data.stipend_analysis.reason;

        // Highlight text preview
        document.getElementById('highlighted-container').innerHTML = data.highlighted_text;

        // Populate keywords pills
        const pillsContainer = document.getElementById('keyword-pills-container');
        pillsContainer.innerHTML = '';
        if (data.suspicious_keywords.length === 0) {
            pillsContainer.innerHTML = '<span class="text-secondary small">No scam keywords flagged.</span>';
        } else {
            data.suspicious_keywords.forEach(kw => {
                const pill = document.createElement('span');
                pill.className = `badge badge-${kw.severity === 'high' ? 'danger' : (kw.severity === 'medium' ? 'warning' : 'primary')}`;
                pill.innerText = `${kw.keyword} (${kw.severity})`;
                pillsContainer.appendChild(pill);
            });
        }

    } catch (e) {
        console.error(e);
        showToast('Connection failed or endpoint offline.', 'danger');
    } finally {
        setBtnLoading('btn-analyze', false);
    }
}

// ─────────────────────────────────────────────────────────────
//  MESSAGE SCANNER
// ─────────────────────────────────────────────────────────────

let activePlatform = 'whatsapp';

function selectPlatform(platform, btn) {
    activePlatform = platform;
    
    // Toggle active classes
    const btns = btn.parentNode.querySelectorAll('.platform-btn');
    btns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    // Modify text placeholder
    const textarea = document.getElementById('message-text');
    const placeholders = {
        'whatsapp':   'Paste the WhatsApp forwarded message here...',
        'telegram':   'Paste the Telegram offer message or channel invite here...',
        'instagram':  'Paste the Instagram DM text here...',
        'sms':        'Paste the SMS text you received here...',
        'email':      'Paste the email body / job offer email content here...',
        'internshala':'Paste the Internshala job/internship description here...',
        'linkedin':   'Paste the LinkedIn job posting or recruiter message here...',
        'other':      'Paste the message or job description text here...',
    };
    textarea.placeholder = placeholders[platform] || 'Paste the message here...';
}

// Auto-detect platform from pasted text
document.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById('message-text');
    if (textarea) {
        textarea.addEventListener('input', function() {
            const text = this.value.toLowerCase();
            let newPlatform = null;
            
            if (text.includes('internshala.com') || text.includes('internshala') || text.includes('internship application on')) {
                newPlatform = 'internshala';
            } else if (text.includes('linkedin.com') || text.includes('linkedin recruiter') || text.includes('linkedin job')) {
                newPlatform = 'linkedin';
            } else if ((text.includes('from:') && text.includes('subject:') && text.includes('@')) || text.includes('forwarded message') && text.includes('@')) {
                newPlatform = 'email';
            } else if (text.includes('t.me/') || text.includes('telegram')) {
                newPlatform = 'telegram';
            } else if (text.includes('instagram.com') || text.includes('dm ') || text.includes(' dm')) {
                newPlatform = 'instagram';
            } else if (text.includes('chat.whatsapp.com') || text.includes('wa.me/')) {
                newPlatform = 'whatsapp';
            }

            if (newPlatform && activePlatform !== newPlatform) {
                const btn = document.getElementById('plat-' + newPlatform);
                if (btn) selectPlatform(newPlatform, btn);
            }
        });
    }
});


async function scanMessage() {
    const text = document.getElementById('message-text').value;
    if (!text || text.trim() === '') {
        showToast('Please input a message to scan.', 'warning');
        return;
    }

    setBtnLoading('btn-scan', true);
    
    try {
        const res = await fetch('/api/scan-message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                platform: activePlatform
            })
        });

        const data = await res.json();
        
        if (res.status >= 400) {
            showToast(data.error || 'Server error during scan', 'danger');
            setBtnLoading('btn-scan', false);
            return;
        }

        document.getElementById('result-placeholder').classList.add('hidden');
        document.getElementById('message-results').classList.remove('hidden');

        // Verdict Badge
        const badge = document.getElementById('verdict-badge');
        badge.innerText = `VERDICT: ${data.verdict}`;
        badge.className = 'verdict-badge';
        
        if (data.verdict.includes('SCAM')) {
            badge.classList.add('bg-danger');
            showToast('Threat Detected: High risk of scam message.', 'danger');
        } else if (data.verdict.includes('SUSPICIOUS')) {
            badge.classList.add('bg-warning');
            showToast('Warning: Message has suspicious markers.', 'warning');
        } else {
            badge.classList.add('bg-success');
            showToast('Scan Clear: Message appears safe.', 'success');
        }

        // Update Gauge
        updateGauge('gauge-risk', data.scam_score);

        // ML Probability bar
        document.getElementById('ml-genuine-pct').innerText = `${Math.round(data.ml_prediction.real_probability)}%`;
        document.getElementById('ml-fake-pct').innerText = `${Math.round(data.ml_prediction.fake_probability)}%`;
        document.getElementById('ml-genuine-bar').style.width = `${data.ml_prediction.real_probability}%`;
        document.getElementById('ml-fake-bar').style.width = `${data.ml_prediction.fake_probability}%`;

        // Preview Bubble class change
        const bubble = document.getElementById('platform-bubble');
        bubble.className = `message-bubble message-${activePlatform}`;
        document.getElementById('highlighted-message').innerHTML = data.highlighted_message;

        // Indicators
        const indicatorsList = document.getElementById('indicators-list');
        indicatorsList.innerHTML = '';
        if (data.indicators.length === 0) {
            indicatorsList.innerHTML = '<li class="text-secondary small">No distinct threat indicators flagged.</li>';
        } else {
            data.indicators.forEach(ind => {
                const li = document.createElement('li');
                li.className = 'indicator-item';
                li.innerHTML = `
                    <span class="indicator-bullet-danger">🚩</span>
                    <span class="indicator-text">${ind.detail}</span>
                `;
                indicatorsList.appendChild(li);
            });
        }

        // Safety Tips
        const tipsList = document.getElementById('safety-tips-list');
        tipsList.innerHTML = '';
        data.safety_tips.forEach(tip => {
            const li = document.createElement('li');
            li.className = 'tip-item';
            li.innerHTML = `
                <span class="tip-bullet">✓</span>
                <span class="tip-text">${tip}</span>
            `;
            tipsList.appendChild(li);
        });

    } catch (e) {
        console.error(e);
        showToast('Connection failed or endpoint offline.', 'danger');
    } finally {
        setBtnLoading('btn-scan', false);
    }
}

// ─────────────────────────────────────────────────────────────
//  COMPANY VERIFIER
// ─────────────────────────────────────────────────────────────

async function checkCompany() {
    const name = document.getElementById('company-name').value;
    if (!name || name.trim() === '') {
        showToast('Please enter a company name.', 'warning');
        return;
    }

    setBtnLoading('btn-verify', true);
    
    try {
        const res = await fetch('/api/check-company', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_name: name })
        });

        const data = await res.json();
        
        if (res.status >= 400) {
            showToast(data.error || 'Server error', 'danger');
            setBtnLoading('btn-verify', false);
            return;
        }

        document.getElementById('result-placeholder').classList.add('hidden');
        document.getElementById('company-results').classList.remove('hidden');

        // Verdict Badge
        const badge = document.getElementById('verdict-badge');
        badge.innerText = `VERDICT: ${data.verdict.toUpperCase()}`;
        badge.className = 'verdict-badge';
        
        if (data.trust_score >= 70) {
            badge.classList.add('bg-success');
            showToast('Verification Successful: Reputable company.', 'success');
        } else if (data.trust_score >= 40) {
            badge.classList.add('bg-warning');
            showToast('Partial Verification: Proceed carefully.', 'warning');
        } else {
            badge.classList.add('bg-danger');
            showToast('High Risk: Unable to verify company existence.', 'danger');
        }

        // Update Trust Gauge
        updateGauge('gauge-risk', data.trust_score);

        // Checklist Updates
        const updateChecklistItem = (id, exists) => {
            const el = document.getElementById(id);
            if (!el) return;
            const status = el.querySelector('.chk-status');
            el.className = `checklist-item ${exists ? 'checked' : 'failed'}`;
            status.innerText = exists ? '✓' : '✗';
        };

        updateChecklistItem('chk-website', data.website_exists);
        updateChecklistItem('chk-linkedin', data.linkedin_exists);
        
        // Age check: score contains domain age signals if >= 10 points
        updateChecklistItem('chk-domain', data.details.includes('established') || data.details.includes('relatively new'));
        updateChecklistItem('chk-name', data.details.includes('name appears professional'));

        // Details text
        document.getElementById('company-details-text').innerText = data.details.split(' | ').join('\n');

    } catch (e) {
        console.error(e);
        showToast('Background query failed.', 'danger');
    } finally {
        setBtnLoading('btn-verify', false);
    }
}

// ─────────────────────────────────────────────────────────────
//  URL SCANNER
// ─────────────────────────────────────────────────────────────

async function scanURL() {
    const url = document.getElementById('scan-url').value;
    if (!url || url.trim() === '') {
        showToast('Please enter a URL to scan.', 'warning');
        return;
    }

    setBtnLoading('btn-scan', true);
    
    try {
        const res = await fetch('/api/scan-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        const data = await res.json();
        
        if (res.status >= 400) {
            showToast(data.error || 'Server error', 'danger');
            setBtnLoading('btn-scan', false);
            return;
        }

        document.getElementById('result-placeholder').classList.add('hidden');
        document.getElementById('url-results').classList.remove('hidden');

        // Verdict banner styling
        const banner = document.getElementById('url-verdict-banner');
        const badge = document.getElementById('url-verdict-badge');
        const title = document.getElementById('url-verdict-title');
        
        title.innerText = `VERDICT: ${data.verdict.toUpperCase()}`;
        badge.innerText = data.is_suspicious ? 'SUSPICIOUS' : 'SAFE';
        
        banner.className = 'verdict-banner-container flex-between align-center p-3 border-radius-sm mb-3';
        badge.className = 'badge';
        
        if (data.is_suspicious) {
            banner.style.borderLeft = '4px solid #ff3366';
            banner.style.backgroundColor = 'rgba(255, 51, 102, 0.1)';
            badge.classList.add('badge-danger');
            showToast('Warning: Suspicious redirect or SSL issues.', 'danger');
        } else {
            banner.style.borderLeft = '4px solid #00ff88';
            banner.style.backgroundColor = 'rgba(0, 255, 136, 0.1)';
            badge.classList.add('badge-success');
            showToast('Link looks secure.', 'success');
        }

        // Checklist Updates
        const updateChecklistItem = (id, success) => {
            const el = document.getElementById(id);
            if (!el) return;
            const status = el.querySelector('.chk-status');
            el.className = `checklist-item ${success ? 'checked' : 'failed'}`;
            status.innerText = success ? '✓' : '✗';
        };

        updateChecklistItem('chk-ssl', data.is_ssl);
        updateChecklistItem('chk-ip', !data.risk_factors.includes('ip_address'));
        updateChecklistItem('chk-tld', !data.risk_factors.includes('suspicious_tld'));
        updateChecklistItem('chk-subdomain', !data.risk_factors.includes('excessive_subdomains'));
        updateChecklistItem('chk-length', !data.risk_factors.includes('very_long_url'));

        // Details
        document.getElementById('url-details-text').innerText = data.details.split(' | ').join('\n');

    } catch (e) {
        console.error(e);
        showToast('Web socket query failed.', 'danger');
    } finally {
        setBtnLoading('btn-scan', false);
    }
}

// ─────────────────────────────────────────────────────────────
//  DASHBOARD ANALYTICS
// ─────────────────────────────────────────────────────────────

let trendChart = null;
let distChart = null;
let keywordChart = null;
let platformChart = null;

async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard-data');
        const data = await res.json();

        // Populate counters
        animateCounter('dash-total', data.total_checks || 0);
        animateCounter('dash-scams', data.scams_detected || 0);
        animateCounter('dash-genuine', data.genuine_detected || 0);
        animateCounter('dash-percent', data.scam_percentage || 0, 1500, true);

        // Chart.js global defaults — clean dark theme
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.borderColor = 'rgba(108, 99, 255, 0.08)';
        Chart.defaults.font.family = "'Inter', sans-serif";

        // 1. Line Chart: Scores Trend
        const trendCtx = document.getElementById('trend-chart');
        if (trendCtx) {
            if (trendChart) trendChart.destroy();
            trendChart = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: data.trend_data.labels.length ? data.trend_data.labels : ['Scan 1', 'Scan 2', 'Scan 3', 'Scan 4'],
                    datasets: [{
                        label: 'Composite Risk Score',
                        data: data.trend_data.scores.length ? data.trend_data.scores : [10, 45, 80, 20],
                        borderColor: '#6c63ff',
                        backgroundColor: 'rgba(108, 99, 255, 0.1)',
                        pointBackgroundColor: '#6c63ff',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { min: 0, max: 100,
                            grid: { color: 'rgba(108,99,255,0.08)' }
                        },
                        x: { grid: { color: 'rgba(108,99,255,0.08)' } }
                    }
                }
            });
        }

        // 2. Doughnut Chart: Distribution
        const distCtx = document.getElementById('distribution-chart');
        if (distCtx) {
            if (distChart) distChart.destroy();
            distChart = new Chart(distCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Genuine', 'Scam / Fake', 'Suspicious'],
                    datasets: [{
                        data: [data.genuine_detected || 1, data.scams_detected || 0, 0],
                        backgroundColor: ['#34d399', '#f87171', '#fbbf24'],
                        borderWidth: 2,
                        borderColor: '#1a1d2e'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } },
                    cutout: '65%'
                }
            });
        }

        // (Keyword chart removed as requested)

        // (Platform stats chart removed as requested)

        // Populate recent checks table
        const recentRes = await fetch('/api/recent-checks');
        const recentData = await recentRes.json();
        
        const tbody = document.getElementById('recent-checks-tbody');
        if (tbody) {
            tbody.innerHTML = '';
            if (recentData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-secondary">No scans recorded in security logs.</td></tr>';
            } else {
                recentData.forEach(row => {
                    const tr = document.createElement('tr');
                    
                    // Risk class
                    let statusClass = 'badge-primary';
                    let statusText = row.result;
                    if (row.result.includes('Fake') || row.result.includes('SCAM')) {
                        statusClass = 'badge-danger';
                    } else if (row.result.includes('Suspicious')) {
                        statusClass = 'badge-warning';
                    } else {
                        statusClass = 'badge-success';
                    }

                    tr.innerHTML = `
                        <td class="font-mono">${row.date_checked}</td>
                        <td>${row.type}</td>
                        <td class="font-mono">${row.source}</td>
                        <td><span class="badge ${statusClass}">${statusText}</span></td>
                        <td class="font-mono">${row.confidence != null ? row.confidence.toFixed(1) + '%' : 'N/A'}</td>
                        <td class="font-mono">${row.score != null ? row.score.toFixed(1) : 'N/A'}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }

    } catch (e) {
        console.error("Failed to load dashboard data", e);
        showToast('Failed to contact analytics API.', 'danger');
    }
}

// --- Toggle mobile menu sidebar ---
document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('mobile-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
        
        // Hide sidebar when click occurs outside on mobile
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target) && sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
            }
        });
    }
});
