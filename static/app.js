
        // Quick class shortcuts: pure keybindings, no server counterpart.
        const QUICK_KEYS = { q: '9', w: '0', e: '-' };

        // =====================================================================
        // STATE
        // =====================================================================
        let state = {
            uploadComplete: false,
            currentImage: null,
            remainingCount: 0,
            historyCount: 0,
            redoCount: 0,
            sortedCounts: {},
            totalSorted: 0,
            lastTime: 0,
            avgTime: 0,
            totalTime: 0
        };

        // Session-scoped run stats (reset on new dataset / reset).
        let sessionStart = null;   // ms epoch when the first image was shown
        let halfwayActive = false; // halfway overlay currently up
        let halfwayShown = false;  // only fire the halfway milestone once
        let endActive = false;     // end summary overlay currently up
        let endShown = false;      // don't re-pop the summary after Close
        let timerHidden = false;   // user toggled the timer off

        function resetRunStats() {
            sessionStart = null;
            halfwayActive = halfwayShown = endActive = endShown = false;
            timeAccum = {};
            document.getElementById('halfway-overlay').classList.add('hidden');
            document.getElementById('end-overlay').classList.add('hidden');
        }

        // The selection flow lives entirely here: 'class' -> 'alt' -> 'status',
        // then one POST /classify with the finished triple.
        let sel = { first: null, second: null, step: 'class' };

        function resetSelection() {
            sel = { first: null, second: null, step: 'class' };
        }

        let zoom = CFG.defaultZoom;
        let sidebarWidth = 320;

        // =====================================================================
        // PER-IMAGE TIMER
        // ponytail: caps at 5 min — past that we assume the user stepped away,
        // so the timer freezes instead of skewing the average. Not idle-detection.
        // =====================================================================
        const TIMER_CAP_MS = 5 * 60 * 1000;
        let timerImage = null;       // which image the running timer belongs to
        let timerStart = 0;          // Date.now() when the current sitting began
        let timerInterval = null;
        // Per-image seconds accrued across visits. Undo brings an image back to the
        // front; resuming from its accrued time (instead of 0) is why the timer no
        // longer resets when you go back to an image.
        let timeAccum = {};

        function fmtTime(sec) {
            sec = Math.max(0, Math.round(sec));
            return Math.floor(sec / 60) + ':' + String(sec % 60).padStart(2, '0');
        }

        // Total time on the timed image: prior accrued + this sitting (sitting capped
        // at 5 min so a walk-away doesn't skew the average).
        function elapsedSeconds() {
            const sitting = Math.min(Date.now() - timerStart, TIMER_CAP_MS) / 1000;
            return (timeAccum[timerImage] || 0) + sitting;
        }

        function tickTimer() {
            if (Date.now() - timerStart >= TIMER_CAP_MS) {
                clearInterval(timerInterval);   // pause: likely stepped away
                timerInterval = null;
            }
            document.getElementById('time-current').textContent = fmtTime(elapsedSeconds());
        }

        function startImageTimer(imageName) {
            // Bank the outgoing image's time so a later revisit resumes from it.
            if (timerImage && timerImage !== imageName) timeAccum[timerImage] = elapsedSeconds();
            if (timerInterval) clearInterval(timerInterval);
            if (sessionStart === null) sessionStart = Date.now();   // sorting began
            timerImage = imageName;
            timerStart = Date.now();
            document.getElementById('time-current').textContent = fmtTime(timeAccum[imageName] || 0);
            timerInterval = setInterval(tickTimer, 1000);
            timerPaused = false;
            armIdle();
        }

        function stopImageTimer() {
            if (timerImage) timeAccum[timerImage] = elapsedSeconds();
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = null;
            timerImage = null;
            timerPaused = false;
            clearTimeout(idleTimer);
            document.getElementById('time-current').textContent = '0:00';
        }

        // IDLE / FOCUS AUTO-PAUSE
        // The timer freezes when you switch tabs/desktops or stop interacting, and
        // resumes on the next mouse move or key press — so a walk-away doesn't count.
        const IDLE_MS = 25000;   // ponytail: pause after 15s idle; tune if too eager/lax
        let timerPaused = false;
        let idleTimer = null;

        function armIdle() {
            clearTimeout(idleTimer);
            idleTimer = setTimeout(pauseTimer, IDLE_MS);
        }

        function pauseTimer() {
            if (timerPaused || timerImage === null) return;
            timeAccum[timerImage] = elapsedSeconds();   // bank the sitting so far
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = null;
            timerPaused = true;
        }

        function resumeTimer() {
            if (!timerPaused || timerImage === null) return;
            timerPaused = false;
            timerStart = Date.now();
            timerInterval = setInterval(tickTimer, 1000);
            tickTimer();
        }

        function markActivity() {
            if (document.hidden) return;   // tab/desktop switch: stay paused
            resumeTimer();
            armIdle();
        }

        ['mousemove', 'mousedown', 'keydown', 'wheel', 'touchstart'].forEach(ev =>
            document.addEventListener(ev, markActivity, { passive: true }));
        document.addEventListener('visibilitychange', () => {
            document.hidden ? pauseTimer() : markActivity();
        });
        window.addEventListener('blur', pauseTimer);
        window.addEventListener('focus', markActivity);

        // =====================================================================
        // UI HELPERS
        // =====================================================================
        function hasUnsavedChanges() {
            return state.uploadComplete && state.remainingCount > 0 && state.totalSorted > 0;
        }

        window.addEventListener('beforeunload', (e) => {
            if (hasUnsavedChanges()) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return e.returnValue;
            }
        });

        function showToast(message, isError = false) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = isError ? 'toast error visible' : 'toast visible';
            setTimeout(() => toast.className = 'toast', 2500);
        }

        function updateUI() {
            const hasImage = state.currentImage !== null;
            const hasSorted = state.totalSorted > 0;

            // Header visibility
            document.getElementById('header-actions').classList.toggle('hidden', !state.uploadComplete);
            document.getElementById('progress-display').classList.toggle('hidden', !state.uploadComplete);
            document.getElementById('time-display').classList.toggle('hidden', !state.uploadComplete || timerHidden);

            // Per-image timer: restart on a new image, stop when none left. Held while
            // a milestone/summary overlay is up so that screen's time isn't counted.
            document.getElementById('time-last').textContent = fmtTime(state.lastTime);
            document.getElementById('time-avg').textContent = fmtTime(state.avgTime);
            const overlayUp = halfwayActive || endActive;
            if (state.uploadComplete && hasImage && !overlayUp) {
                if (state.currentImage !== timerImage) startImageTimer(state.currentImage);
            } else if (timerImage !== null && !overlayUp) {
                stopImageTimer();
            }

            // Button states
            document.getElementById('undo-btn').disabled = state.historyCount === 0;
            document.getElementById('redo-btn').disabled = state.redoCount === 0;
            document.getElementById('flag-btn').disabled = !(state.uploadComplete && hasImage);
            document.getElementById('inspect-btn').disabled = !(state.uploadComplete && hasImage);
            document.getElementById('save-btn').disabled = !hasSorted;
            document.getElementById('load-btn').disabled = !state.uploadComplete;

            // Progress stats
            document.getElementById('remaining-count').textContent = state.remainingCount;
            document.getElementById('sorted-count').textContent = state.totalSorted;

            const total = state.remainingCount + state.totalSorted;
            const pct = total > 0 ? Math.round((state.totalSorted / total) * 100) : 0;
            document.getElementById('progress-fill').style.width = pct + '%';

            updateCountBadges();
            updateImageViewer(hasImage);

            document.getElementById('classification-bar').classList.toggle('hidden', !state.uploadComplete || !hasImage || halfwayActive);
            document.getElementById('status-panel').classList.toggle('hidden', !hasImage || sel.step !== 'status');

            updateButtonStates();
            updateWorkflowStage();
        }

        function updateImageViewer(hasImage) {
            const placeholder = document.getElementById('placeholder');
            const showImage = state.uploadComplete && hasImage;

            // Inspect only makes sense with an image up; drop out of it otherwise.
            if (!showImage && inspecting) toggleInspect();
            const gridOn = showImage && inspecting;

            placeholder.style.display = showImage ? 'none' : 'block';
            document.getElementById('image-container').style.display = showImage && !gridOn ? 'flex' : 'none';
            document.getElementById('inspect-grid').classList.toggle('hidden', !gridOn);
            document.getElementById('zoom-controls').style.display = showImage ? 'flex' : 'none';
            document.getElementById('image-info').style.display = showImage ? 'block' : 'none';

            if (showImage) {
                document.getElementById('current-image').src =
                    `/serve_image/${encodeURIComponent(state.currentImage)}?t=${Date.now()}`;
                // Show the real name, not the internal ~flag~ alias.
                const shown = state.currentImage.replace(/^~flag~\d+~/, '');
                document.getElementById('filename-display').textContent =
                    shown === state.currentImage ? shown : '🚩 ' + shown;
            } else if (state.uploadComplete) {
                placeholder.innerHTML = `
                    <div class="placeholder-icon">🎉</div>
                    <div class="placeholder-text">
                        All done!<br>
                        <small>Click Download to get results</small>
                    </div>
                `;
            }
        }

        function updateCountBadges() {
            for (const key of Object.keys(CFG.classMap)) {
                const count = state.sortedCounts[CFG.classMap[key]] || 0;
                const badge = document.getElementById('count-' + key);
                if (!badge) continue;

                // Count plus its share of all classified images (rounded to a whole %).
                const pct = state.totalSorted > 0 ? Math.round(count / state.totalSorted * 100) : 0;
                badge.innerHTML = count + '<span class="pct-badge">' + pct + '%</span>';
                badge.classList.toggle('has-items', count > 0);
            }
        }

        function updateWorkflowStage() {
            const stageEl = document.getElementById('workflow-stage');
            const altPanel = document.getElementById('alternative-panel');

            if (!state.currentImage) {
                stageEl.classList.add('hidden');
                altPanel.classList.add('hidden');
                return;
            }

            stageEl.classList.remove('hidden');
            altPanel.classList.toggle('hidden', sel.step !== 'alt');

            const labels = {
                'class': 'Step 1: Select a class',
                'alt': 'Step 2: Select alternative or confirm',
                'status': 'Step 3: Select image quality (ULU)'
            };
            document.getElementById('stage-label').textContent = labels[sel.step];

            if (sel.step === 'alt') updateAlternativeButtons();
        }

        function updateAlternativeButtons() {
            const container = document.getElementById('adjacent-buttons');
            container.innerHTML = '';
            if (!sel.first) return;

            const adjacent = CFG.adjacency[sel.first] || [];

            Object.keys(CFG.classMap)
                .filter(k => k !== sel.first && !CFG.notOfferedAsAlternative.includes(k))
                .forEach(key => {
                    const btn = document.createElement('button');
                    btn.className = 'alternative-btn' + (adjacent.includes(key) ? ' adjacent-option' : '');
                    btn.innerHTML = `${CFG.classMap[key]}<span class="key-hint">${key}</span>`;
                    btn.onclick = () => selectAlternative(key);
                    container.appendChild(btn);
                });
        }

        function updateButtonStates() {
            // Class buttons are live only during step 1.
            document.querySelectorAll('.class-btn').forEach(btn => {
                btn.classList.toggle('selected', sel.first === btn.dataset.key);
                btn.disabled = !state.currentImage || sel.step !== 'class';
            });

            ['status-usable', 'status-limited', 'status-unusable'].forEach(id => {
                document.getElementById(id).disabled = sel.step !== 'status';
            });

            // Selection indicator
            const indicator = document.getElementById('selection-indicator');
            indicator.classList.toggle('hidden', !sel.first);
            if (!sel.first) return;

            document.getElementById('first-label-tag').textContent = CFG.classMap[sel.first];

            const secondTag = document.getElementById('second-label-tag');
            const warning = document.getElementById('adjacency-warning');
            const isAdjacent = (CFG.adjacency[sel.first] || []).includes(sel.second);

            secondTag.style.display = sel.second ? 'inline-flex' : 'none';
            warning.style.display = sel.second && !isAdjacent ? 'inline' : 'none';

            if (sel.second) {
                secondTag.textContent = CFG.classMap[sel.second];
                secondTag.classList.toggle('non-adjacent', !isAdjacent);
            }
        }

        // =====================================================================
        // TIMER TOGGLE + MILESTONE / SUMMARY OVERLAYS
        // =====================================================================
        function toggleTimer() {
            timerHidden = !timerHidden;
            document.getElementById('timer-toggle').style.opacity = timerHidden ? '0.4' : '';
            updateUI();
        }

        function fmtClock(ms) {
            return new Date(ms).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        }

        // Per-class counts (non-empty only) as stat rows.
        function classCountRows() {
            return Object.values(CFG.classMap)
                .map(name => [name, state.sortedCounts[name] || 0])
                .filter(([, c]) => c > 0)
                .map(([name, c]) =>
                    `<div class="stat-row"><span>${name}</span>` +
                    `<span>${c} · ${Math.round(c / state.totalSorted * 100)}%</span></div>`)
                .join('');
        }

        // Fire the milestone / summary overlays. Called after every state change;
        // the *Shown flags keep each to a single appearance per run.
        function checkMilestones() {
            const total = state.remainingCount + state.totalSorted;

            if (!halfwayShown && total > 1 && state.remainingCount > 0
                && state.totalSorted >= Math.floor(total / 2)) {
                showHalfway(total);
            } else if (!endShown && state.uploadComplete && state.remainingCount === 0
                && state.totalSorted > 0) {
                showEnd();
            }
        }

        function showHalfway(total) {
            halfwayShown = true;
            halfwayActive = true;
            stopImageTimer();   // pause: halfway-screen time is not counted
            document.getElementById('halfway-sub').textContent =
                `${state.totalSorted} of ${total} sorted — ${state.remainingCount} to go`;
            document.getElementById('halfway-stats').innerHTML =
                `<div class="stat-row"><span>Active time so far</span><span>${fmtTime(state.totalTime)}</span></div>` +
                `<div class="stat-row"><span>Average / image</span><span>${fmtTime(state.avgTime)}</span></div>` +
                `<div class="stat-divider"></div>` + classCountRows();
            document.getElementById('halfway-overlay').classList.remove('hidden');
            updateUI();   // hide the classification bar behind the screen
        }

        function dismissHalfway() {
            if (!halfwayActive) return;
            halfwayActive = false;
            delete timeAccum[state.currentImage];   // next image starts at 0:00
            document.getElementById('halfway-overlay').classList.add('hidden');
            updateUI();   // resumes the timer on the next image
        }

        function showEnd() {
            endShown = true;
            endActive = true;
            stopImageTimer();
            document.getElementById('end-stats').innerHTML =
                `<div class="stat-row"><span>Total sorted</span><span>${state.totalSorted}</span></div>` +
                `<div class="stat-row"><span>Started</span><span>${sessionStart ? fmtClock(sessionStart) : '—'}</span></div>` +
                `<div class="stat-row"><span>Ended</span><span>${fmtClock(Date.now())}</span></div>` +
                `<div class="stat-row"><span>Total active time</span><span>${fmtTime(state.totalTime)}</span></div>` +
                `<div class="stat-row"><span>Average / image</span><span>${fmtTime(state.avgTime)}</span></div>` +
                `<div class="stat-divider"></div>` + classCountRows();
            document.getElementById('end-overlay').classList.remove('hidden');
        }

        function hideEnd() {
            endActive = false;
            document.getElementById('end-overlay').classList.add('hidden');
        }

        // =====================================================================
        // ZOOM
        // =====================================================================
        function setZoom(newZoom) {
            zoom = Math.max(0.25, Math.min(4, newZoom));
            // Scale the image within the fixed white card; in inspect mode the four
            // panels scale together off the same zoom value.
            const t = `scale(${zoom})`;
            const img = document.getElementById('current-image');
            if (img) img.style.transform = t;
            document.querySelectorAll('#inspect-grid canvas').forEach(c => c.style.transform = t);
            document.getElementById('zoom-label').textContent = Math.round(zoom * 100) + '%';
        }

        function zoomIn() { setZoom(zoom + 0.25); }
        function zoomOut() { setZoom(zoom - 0.25); }
        function resetZoom() { setZoom(CFG.defaultZoom); }

        // =====================================================================
        // INSPECT — 2x2 channel split of the current image. Pure view: drawn
        // client-side from #current-image (same-origin, so the canvas isn't
        // tainted). No server calls, no timer/selection changes.
        // =====================================================================
        let inspecting = false;

        function toggleInspect() {
            inspecting = !inspecting;
            document.getElementById('inspect-btn').classList.toggle('active', inspecting);
            if (inspecting) drawInspect();
            updateImageViewer(state.currentImage !== null);
        }

        // Paint one panel: chan null = original, else 0/1/2 = R/G/B as grayscale
        // (that channel's value copied into all three, so it reads as intensity).
        function paintChannel(canvasId, base, chan) {
            const c = document.getElementById(canvasId);
            c.width = base.width;
            c.height = base.height;
            const ctx = c.getContext('2d');
            if (chan === null) { ctx.putImageData(base, 0, 0); return; }
            const out = ctx.createImageData(base.width, base.height);
            const s = base.data, d = out.data;
            for (let i = 0; i < s.length; i += 4) {
                d[i] = d[i + 1] = d[i + 2] = s[i + chan];
                d[i + 3] = s[i + 3];
            }
            ctx.putImageData(out, 0, 0);
        }

        function drawInspect() {
            const img = document.getElementById('current-image');
            if (!img.complete || !img.naturalWidth) return;   // load event will retry
            const w = img.naturalWidth, h = img.naturalHeight;
            const src = document.createElement('canvas');
            src.width = w; src.height = h;
            src.getContext('2d').drawImage(img, 0, 0);
            const base = src.getContext('2d').getImageData(0, 0, w, h);
            paintChannel('ins-orig', base, null);
            paintChannel('ins-r', base, 0);
            paintChannel('ins-g', base, 1);
            paintChannel('ins-b', base, 2);
            setZoom(zoom);   // apply current zoom to the freshly-sized canvases
        }

        // Keep the grid in sync when the image swaps (sort/undo) while inspecting.
        document.getElementById('current-image').addEventListener('load', () => {
            if (inspecting) drawInspect();
        });

        // =====================================================================
        // SIDEBAR
        // =====================================================================
        // Single source of truth for sidebar width. Collapsing CLEARS the inline
        // width so the .collapsed rule (width:0) actually wins — otherwise an inline
        // width left over from a drag overrides it and the sidebar never collapses.
        function applySidebarWidth(w) {
            const sidebar = document.getElementById('sidebar');
            const toggle = document.getElementById('sidebar-toggle');
            const icon = document.getElementById('toggle-icon');

            if (w <= 40) {
                sidebar.classList.add('collapsed');
                sidebar.style.width = '';
                toggle.style.left = '0';
                icon.textContent = '›';
            } else {
                sidebar.classList.remove('collapsed');
                sidebar.style.width = w + 'px';
                toggle.style.left = w + 'px';
                icon.textContent = '‹';
                sidebarWidth = w;   // remember last expanded width for reopen
            }
        }

        function toggleSidebar() {
            const collapsed = document.getElementById('sidebar').classList.contains('collapsed');
            applySidebarWidth(collapsed ? (sidebarWidth || 320) : 0);
        }

        (function initSidebarResize() {
            const sidebar = document.getElementById('sidebar');
            let isResizing = false;

            document.getElementById('sidebar-resize').addEventListener('mousedown', (e) => {
                isResizing = true;
                sidebar.style.transition = 'none';   // no easing lag while dragging
                document.body.style.cursor = 'ew-resize';
                document.body.style.userSelect = 'none';
                e.preventDefault();
            });

            document.addEventListener('mousemove', (e) => {
                if (isResizing) applySidebarWidth(Math.max(0, Math.min(450, e.clientX)));
            });

            document.addEventListener('mouseup', () => {
                if (!isResizing) return;
                isResizing = false;
                sidebar.style.transition = '';
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            });
        })();

        // =====================================================================
        // SELECTION FLOW (client-side; the server only sees the finished triple)
        // =====================================================================
        function selectLabel(key) {
            if (!state.currentImage || sel.step !== 'class' || !(key in CFG.classMap)) return;

            // Uninfected goes straight through without ever entering a selection state,
            // so a failed request leaves nothing half-selected behind.
            if (CFG.autoAdvance.includes(key)) {
                classify(key, null, 'Usable');
                return;
            }

            sel = { first: key, second: null, step: CFG.skipAlternative.includes(key) ? 'status' : 'alt' };
            updateUI();
        }

        function selectAlternative(key) {
            if (sel.step !== 'alt') return;
            sel.second = key === 'none' ? null : key;
            sel.step = 'status';
            updateUI();
        }

        function finalizeWithStatus(status) {
            if (sel.step !== 'status') {
                showToast('Select a class first', true);
                return;
            }
            classify(sel.first, sel.second, status);
        }

        function clearSelection() {
            resetSelection();
            updateUI();
        }

        // Backspace steps back through the current selection before touching the
        // previous image: status -> alternative -> class -> (nothing) -> undo.
        function stepBack() {
            if (sel.step === 'status' && !CFG.skipAlternative.includes(sel.first)) {
                sel.second = null;
                sel.step = 'alt';
                updateUI();
            } else if (sel.first) {
                clearSelection();
            } else {
                executeUndo();
            }
        }

        // =====================================================================
        // API CALLS
        // =====================================================================
        function applyState(data) {
            state.currentImage = data.current_image;
            state.remainingCount = data.remaining_count;
            state.historyCount = data.history_count;
            state.redoCount = data.redo_count;
            state.sortedCounts = data.sorted_counts;
            state.totalSorted = data.total_sorted;
            state.lastTime = data.last_time;
            state.avgTime = data.avg_time;
            state.totalTime = data.total_time;
            resetSelection();   // the queue moved; any half-made selection is stale
        }

        // Every queue-changing endpoint returns the same state payload, so they
        // all land here.
        async function post(url, body) {
            try {
                const res = await fetch(url, body ? {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                } : { method: 'POST' });

                const data = await res.json();
                if (!data.success) {
                    showToast(data.message, true);
                    return;
                }

                showToast(data.message);
                applyState(data);
                updateUI();
                checkMilestones();
            } catch (e) {
                showToast('Request failed', true);
            }
        }

        function classify(first, second, status) {
            post('/classify', { first, second, status, time_spent: elapsedSeconds() });
        }

        const executeUndo = () => post('/undo');
        const executeRedo = () => post('/redo');
        const flagImage = () => { if (state.currentImage) post('/flag'); };

        async function fetchState() {
            try {
                const data = await (await fetch('/state')).json();
                state.uploadComplete = data.upload_complete;
                applyState(data);
                updateUI();
                checkMilestones();
            } catch (e) {
                console.error('Failed to fetch state:', e);
            }
        }

        // Download via an <a download> click, not location.href, so the browser
        // treats it as a file download and never fires the beforeunload prompt.
        function triggerDownload(url) {
            const a = document.createElement('a');
            a.href = url;
            a.download = '';
            document.body.appendChild(a);
            a.click();
            a.remove();
        }

        function saveProgress() {
            if (state.totalSorted > 0) triggerDownload('/save_progress');
        }

        async function resetSession() {
            const message = hasUnsavedChanges()
                ? `Reset all data? ${state.remainingCount} images are still unsorted and your `
                  + `${state.totalSorted} classifications will be lost. Save first if you want to keep them.`
                : 'Reset all data? This cannot be undone.';

            if (!confirm(message)) return;

            try {
                const data = await (await fetch('/reset', { method: 'POST' })).json();
                if (data.success) {
                    resetRunStats();
                    showToast('Session reset');
                    await fetchState();
                }
            } catch (e) {
                showToast('Error resetting', true);
            }
        }

        // =====================================================================
        // FILE UPLOADS
        // =====================================================================
        async function uploadFile(url, field, file) {
            const formData = new FormData();
            formData.append(field, file);

            try {
                const data = await (await fetch(url, { method: 'POST', body: formData })).json();
                showToast(data.message, !data.success);
                if (data.success) await fetchState();
            } catch (e) {
                showToast('Upload failed', true);
            }
        }

        document.getElementById('dataset-input').addEventListener('change', async (e) => {
            if (!e.target.files[0]) return;
            resetRunStats();   // fresh dataset, fresh run
            showToast('Uploading...');
            await uploadFile('/upload_dataset', 'dataset_zip', e.target.files[0]);
            e.target.value = '';
        });

        document.getElementById('progress-input').addEventListener('change', async (e) => {
            if (!e.target.files[0]) return;
            await uploadFile('/upload_progress', 'progress_csv', e.target.files[0]);
            e.target.value = '';
        });

        // =====================================================================
        // KEYBOARD SHORTCUTS
        // =====================================================================
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            // Overlays swallow shortcuts: any key continues past the halfway screen;
            // the end summary ignores them until Close.
            if (halfwayActive) { e.preventDefault(); dismissHalfway(); return; }
            if (endActive) { e.preventDefault(); return; }

            const key = e.key;

            // Q/W/E = quick class shortcuts for Platelet / Uninfected / Cannot Determine,
            // mapped to their digits and dispatched exactly like the number keys so
            // pressing the same quick key again during Step 2 means "No Alternative".
            const digit = QUICK_KEYS[key.toLowerCase()] !== undefined
                ? QUICK_KEYS[key.toLowerCase()] : key;

            // Number keys 0-9 and minus for classification
            if (/^[0-9]$/.test(digit) || digit === '-') {
                e.preventDefault();

                if (sel.step === 'status') {
                    // 1/2/3 = Usable/Limited/Unusable.
                    const status = { '1': 'Usable', '2': 'Limited', '3': 'Unusable' }[digit];
                    if (status) finalizeWithStatus(status);
                } else if (sel.step === 'alt') {
                    // Pressing the first label's own key again means "No Alternative";
                    // any other class key is the alternative.
                    if (digit === sel.first) selectAlternative('none');
                    else if (!CFG.notOfferedAsAlternative.includes(digit)) selectAlternative(digit);
                } else {
                    selectLabel(digit);
                }
                return;
            }

            const actions = {
                'Enter': () => sel.step === 'status' ? finalizeWithStatus('Usable')
                             : sel.step === 'alt' ? selectAlternative('none') : null,
                "'": () => finalizeWithStatus('Limited'),
                'Shift': () => finalizeWithStatus('Unusable'),
                'z': stepBack,
                'Backspace': stepBack,
                'y': executeRedo,
                'f': flagImage,
                '+': zoomIn,
                '=': zoomIn,
                '_': zoomOut,
                'Escape': clearSelection
            };

            // Apostrophe and Shift only mean anything during status selection.
            if ((key === "'" || key === 'Shift') && sel.step !== 'status') return;

            const action = actions[key] || actions[key.toLowerCase()];
            if (action) {
                e.preventDefault();
                action();
            }
        });

        // Zoom with mouse wheel
        document.addEventListener('wheel', (e) => {
            const container = document.getElementById('image-container');
            if (!container.contains(e.target)) return;

            if (e.ctrlKey || e.metaKey || e.shiftKey) {
                e.preventDefault();
                if (e.deltaY < 0) zoomIn();
                else zoomOut();
            }
        }, { passive: false });

        // =====================================================================
        // INIT
        // =====================================================================
        window.onload = function() {
            fetchState();
            setZoom(CFG.defaultZoom);
        };
