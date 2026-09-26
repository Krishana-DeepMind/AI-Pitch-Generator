document.addEventListener('DOMContentLoaded', () => {
    const policyChipsContainer = document.getElementById('policy-chips-container');
    const companyInput = document.getElementById('company-name');
    const generateBtn = document.getElementById('generate-btn');
    const pitchForm = document.getElementById('pitch-form');
    
    const heroPanel = document.getElementById('hero-panel');
    const loadingPanel = document.getElementById('loading-panel');
    const errorPanel = document.getElementById('error-panel');
    const resultsSection = document.getElementById('results-section');
    
    const liveStatusText = document.getElementById('live-status-text');
    const retryBtn = document.getElementById('retry-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const generateAnotherBtn = document.getElementById('generate-another-btn');
    const downloadBtn = document.getElementById('download-deck-btn');
    const errorMessage = document.getElementById('error-message');
    
    let activePolicies = new Set();
    let currentAbortController = null;

    // Load policies
    async function loadPolicies() {
        try {
            const res = await fetch('/policies');
            if (!res.ok) throw new Error('Failed to load policies');
            const data = await res.json();
            
            policyChipsContainer.innerHTML = '';
            
            data.forEach(policy => {
                const chip = document.createElement('div');
                chip.className = 'chip selected';
                chip.setAttribute('role', 'checkbox');
                chip.setAttribute('aria-checked', 'true');
                chip.tabIndex = 0;
                
                chip.innerHTML = `
                    <svg class="check-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    ${policy.name}
                `;
                
                activePolicies.add(policy.id);
                
                const toggle = () => {
                    const isSelected = chip.classList.toggle('selected');
                    chip.setAttribute('aria-checked', isSelected);
                    const check = chip.querySelector('.check-icon');
                    if (isSelected) {
                        activePolicies.add(policy.id);
                        check.style.display = 'block';
                    } else {
                        activePolicies.delete(policy.id);
                        check.style.display = 'none';
                    }
                };
                
                chip.addEventListener('click', toggle);
                chip.addEventListener('keydown', (e) => {
                    if (e.key === ' ' || e.key === 'Enter') {
                        e.preventDefault();
                        toggle();
                    }
                });
                
                policyChipsContainer.appendChild(chip);
            });
        } catch (err) {
            policyChipsContainer.innerHTML = '<span class="text-small" style="color: var(--color-status-fail)">Failed to load policies</span>';
        }
    }
    
    loadPolicies();

    // Input validation
    companyInput.addEventListener('input', () => {
        const val = companyInput.value.trim();
        generateBtn.disabled = val.length === 0;
    });

    // Reset UI
    function resetUI() {
        resultsSection.classList.add('hidden');
        errorPanel.classList.add('hidden');
        loadingPanel.classList.add('hidden');
        
        generateBtn.style.display = 'inline-flex';
        generateBtn.disabled = false;
        generateBtn.innerHTML = `
            <span class="btn-text">Generate Pitch</span>
            <svg class="btn-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
            </svg>`;
        companyInput.disabled = false;
        document.querySelectorAll('.chip').forEach(c => c.style.pointerEvents = 'auto');
    }

    retryBtn.addEventListener('click', resetUI);
    cancelBtn.addEventListener('click', () => {
        if (currentAbortController) currentAbortController.abort();
        resetUI();
    });
    generateAnotherBtn.addEventListener('click', () => {
        companyInput.value = '';
        generateBtn.disabled = true;
        resetUI();
    });

    // Form Submit
    pitchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const companyName = companyInput.value.trim();
        if (!companyName) return;

        // UI transitions
        generateBtn.style.display = 'none';
        loadingPanel.classList.remove('hidden');
        errorPanel.classList.add('hidden');
        resultsSection.classList.add('hidden');
        companyInput.disabled = true;
        document.querySelectorAll('.chip').forEach(c => c.style.pointerEvents = 'none');
        
        setStep(1, 'Extracting risk profile from public filings...');
        
        currentAbortController = new AbortController();
        const start = Date.now();
        
        // Sim UX steps for polling behavior effect
        const simInterval = setInterval(() => {
            const elapsed = Date.now() - start;
            if (elapsed > 15000) setStep(2, 'Matching policy documents...');
            if (elapsed > 35000) setStep(3, 'Writing pitch slides...');
            if (elapsed > 60000) setStep(4, 'Auditing claims...');
        }, 1000);

        try {
            const res = await fetch('/generate-pitch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: companyName,
                    include_policies: Array.from(activePolicies)
                }),
                signal: currentAbortController.signal
            });
            
            clearInterval(simInterval);
            
            if (!res.ok) {
                throw new Error(`Server returned ${res.status}`);
            }
            
            const data = await res.json();
            const timeSeconds = Math.round((Date.now() - start) / 1000);
            renderResults(data, timeSeconds);
            
        } catch (err) {
            clearInterval(simInterval);
            if (err.name === 'AbortError') return;
            
            loadingPanel.classList.add('hidden');
            errorPanel.classList.remove('hidden');
            errorMessage.textContent = 'Error generating pitch: ' + err.message;
            generateBtn.style.display = 'inline-flex';
            companyInput.disabled = false;
            document.querySelectorAll('.chip').forEach(c => c.style.pointerEvents = 'auto');
        }
    });
    
    function setStep(stepNum, text) {
        liveStatusText.textContent = text;
        const steps = ['profile', 'retrieve', 'generate', 'audit'];
        
        steps.forEach((step, idx) => {
            const el = document.getElementById(`step-${step}`);
            const line = el.nextElementSibling;
            
            el.classList.remove('completed', 'current');
            if (line && line.classList.contains('step-line')) line.classList.remove('completed');
            
            if (idx + 1 < stepNum) {
                el.classList.add('completed');
                if (line && line.classList.contains('step-line')) line.classList.add('completed');
            } else if (idx + 1 === stepNum) {
                el.classList.add('current');
            }
        });
    }

    function renderResults(data, timeSeconds) {
        loadingPanel.classList.add('hidden');
        resultsSection.classList.remove('hidden');
        
        // Deck Meta
        document.getElementById('deck-meta').textContent = `${data.deck_filename} • ${data.slides_preview.length} slides • Generated in ${timeSeconds}s`;
        downloadBtn.href = `/download/${data.deck_filename}`;
        
        // Audit Overview
        const overallBadge = document.getElementById('overall-badge');
        const overallConfidence = document.getElementById('overall-confidence');
        
        overallConfidence.textContent = `${(data.audit_report.overall_confidence * 100).toFixed(1)}% confidence`;
        
        overallBadge.className = 'badge-pill';
        if (data.audit_report.overall_pass) {
            overallBadge.textContent = 'PASS ✓';
            overallBadge.classList.add('pass');
        } else {
            overallBadge.textContent = 'REVIEW REQUIRED ⚠';
            overallBadge.classList.add('warn');
        }
        
        // Proportional Bar
        const bar = document.getElementById('audit-bar');
        const legend = document.getElementById('audit-legend');
        
        let pass = 0, partial = 0, fail = 0, unknown = 0;
        data.audit_report.slide_audits.forEach(sa => {
            sa.claims.forEach(ca => {
                if (ca.verdict.toUpperCase() === 'SUPPORTED') pass++;
                else if (ca.verdict.toUpperCase() === 'PARTIALLY_SUPPORTED') partial++;
                else if (ca.verdict.toUpperCase() === 'UNSUPPORTED') fail++;
                else unknown++;
            });
        });
        
        const total = pass + partial + fail + unknown;
        const pPass = (pass/total)*100, pPart = (partial/total)*100, pFail = (fail/total)*100, pUnk = (unknown/total)*100;
        
        bar.querySelector('.bar-pass').style.width = `${pPass}%`;
        bar.querySelector('.bar-partial').style.width = `${pPart}%`;
        bar.querySelector('.bar-fail').style.width = `${pFail}%`;
        bar.querySelector('.bar-unknown').style.width = `${pUnk}%`;
        
        legend.innerHTML = `
            <div class="legend-item"><div class="legend-dot" style="background: var(--color-status-pass)"></div>Supported (${pass})</div>
            <div class="legend-item"><div class="legend-dot" style="background: var(--color-status-partial)"></div>Partial (${partial})</div>
            <div class="legend-item"><div class="legend-dot" style="background: var(--color-status-fail)"></div>Unsupported (${fail})</div>
            <div class="legend-item"><div class="legend-dot" style="background: var(--color-status-unknown)"></div>Unknown (${unknown})</div>
        `;
        
        // Claims List
        const claimsList = document.getElementById('audit-claims-list');
        claimsList.innerHTML = '';
        
        data.audit_report.slide_audits.forEach((sa, idx) => {
            const totalC = sa.claims.length;
            const issues = sa.claims.filter(c => c.verdict.toUpperCase() !== 'SUPPORTED').length;
            
            const group = document.createElement('div');
            group.className = 'slide-group';
            
            group.innerHTML = `
                <div class="slide-header" onclick="this.parentElement.classList.toggle('expanded'); const list = this.nextElementSibling; if(list.classList.contains('hidden')){list.classList.remove('hidden')}else{list.classList.add('hidden')}">
                    <div class="slide-title-wrap">
                        <svg class="chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="transition: transform 0.2s ease;">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                        <h3>Slide ${idx + 1}: ${sa.slide_title}</h3>
                    </div>
                    <span class="badge-mono" style="background: ${issues > 0 ? 'var(--color-status-fail-bg)' : ''}; color: ${issues > 0 ? 'var(--color-status-fail)' : 'inherit'}">${totalC} claims / ${issues} issue${issues !== 1 ? 's' : ''}</span>
                </div>
                <div class="slide-claims ${issues === 0 ? 'hidden' : ''}">
                </div>
            `;
            
            const chevron = group.querySelector('.chevron');
            if (issues > 0) chevron.style.transform = 'rotate(180deg)';
            
            group.querySelector('.slide-header').addEventListener('click', function() {
                const isHidden = this.nextElementSibling.classList.contains('hidden');
                if (isHidden) {
                    chevron.style.transform = 'rotate(0deg)';
                } else {
                    chevron.style.transform = 'rotate(180deg)';
                }
            });

            const claimsContainer = group.querySelector('.slide-claims');
            
            sa.claims.forEach(ca => {
                const statusClass = `status-${ca.verdict.toLowerCase().replace('_', '-')}`;
                const upVerdict = ca.verdict.toUpperCase();
                
                let iconSvg = '';
                if (upVerdict === 'SUPPORTED') iconSvg = '<polyline points="20 6 9 17 4 12"></polyline>';
                else if (upVerdict === 'PARTIALLY_SUPPORTED') iconSvg = '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line>';
                else if (upVerdict === 'UNSUPPORTED') iconSvg = '<line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>';
                else iconSvg = '<circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line>';
                
                const row = document.createElement('div');
                row.className = `claim-row ${statusClass}`;
                
                row.innerHTML = `
                    <div class="claim-row-main" onclick="this.parentElement.classList.toggle('expanded'); const d = this.nextElementSibling; if(d.style.maxHeight){d.style.maxHeight=null;}else{d.style.maxHeight=d.scrollHeight+'px';}">
                        <svg class="claim-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            ${iconSvg}
                        </svg>
                        <div class="claim-text">${ca.claim_text}</div>
                        <div class="claim-meta">
                            <span class="badge-mono">${ca.confidence_score.toFixed(2)}</span>
                            <span class="badge-mono" style="text-transform: uppercase">${ca.verification_method}</span>
                            <svg class="chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="6 9 12 15 18 9"></polyline>
                            </svg>
                        </div>
                    </div>
                    <div class="claim-detail">
                        <div class="claim-detail-inner">
                            <div class="detail-label">Source Document:</div>
                            <div class="detail-value">${ca.source_document || 'None found'}</div>
                            
                            <div class="detail-label">Source Clause:</div>
                            <div class="source-quote">${ca.source_clause || 'No supporting text retrieved'}</div>
                            
                            ${ca.notes ? `
                                <div class="detail-label">LLM Rationale:</div>
                                <div class="detail-value">${ca.notes}</div>
                            ` : ''}
                        </div>
                    </div>
                `;
                claimsContainer.appendChild(row);
            });
            
            claimsList.appendChild(group);
        });
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    // Admin upload
    const uploadForm = document.getElementById('upload-form');
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('policy-file');
        const file = fileInput.files[0];
        if (!file) return;
        
        const btn = uploadForm.querySelector('button');
        btn.textContent = 'Uploading...';
        btn.disabled = true;
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const res = await fetch('/admin/add-policy', {
                method: 'POST',
                body: formData
            });
            if (!res.ok) throw new Error('Upload failed');
            alert('Policy uploaded successfully!');
            loadPolicies();
            fileInput.value = '';
        } catch (err) {
            alert(err.message);
        } finally {
            btn.textContent = 'Upload';
            btn.disabled = false;
        }
    });
});
