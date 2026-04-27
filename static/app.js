const API = "";
var hasReloadedAfterCompletion = false;
var lastCompletionDetected = false;

// ── State ──
let state = {
    currentPage: "Simulator",
    allSolvers: [],
    allProblems: [],
    allPlots: [],
    selectedSolverName: "",
    selectedProblemName: "",
    selectedPlotName: "",
    solverParams: [],
    problemParams: [],
    plotParams: [],
    summarySolvers: [],
    summaryProblems: [],
    summaryPlots: [],
    selectedPlotSolvers: [],
    selectedPlotProblems: [],
    editMode: null,
    macroreps: 10,
    showPostProcess: false,
    showPostNormalize: false,
    prValues: {},
    pnValues: {},
    prSchema: { params: [] },
    pnSchema: { params: [] },
    compatibility: {},
    showCompatModal: false,
    showConfirm: false,
    confirmKind: null,
    confirmIndex: null,
    lastRunId: null,
};

// ── Helpers ──
function toDisplayString(val) {
    if (val === null || val === undefined) return "";
    if (typeof val === "string") return val;
    try { return JSON.stringify(val); } catch { return String(val); }
}

function parseValue(val) {
    if (val === null || val === undefined || val === "") return null;
    if (typeof val !== "string") return val;
    try { return JSON.parse(val); } catch { return val; }
}

function deepCopyParams(arr) {
    return (arr || []).map(p => ({ ...p }));
}

function abbrev(name) {
    if (!name) return "";
    return String(name).replace(/[^A-Za-z0-9]/g, "").slice(-4).toUpperCase();
}

// ── API calls ──
async function fetchSolverParams(name) {
    if (!name) return [];
    const res = await fetch(`${API}/solver_params/${encodeURIComponent(name)}`);
    const data = await res.json();
    return (data.parameters || []).map(p => ({
        name: p.name, description: p.description || "",
        default: p.default, value: toDisplayString(p.default)
    }));
}

async function fetchProblemParams(name) {
    if (!name) return [];
    const res = await fetch(`${API}/problem_params/${encodeURIComponent(name)}`);
    const data = await res.json();
    return (data.parameters || []).map(p => ({
        name: p.name, description: p.description || "",
        default: p.default, value: toDisplayString(p.default)
    }));
}

async function fetchPlotParams(name) {
    if (!name) return [];
    const res = await fetch(`${API}/plot_params/${encodeURIComponent(name)}`);
    const data = await res.json();
    return (data.parameters || []).map(p => ({
        name: p.name, description: p.description || "",
        default: p.default, value: toDisplayString(p.default)
    }));
}

async function checkCompatibility() {
    if (!state.summarySolvers.length || !state.summaryProblems.length) {
        state.compatibility = {};
        render();
        return;
    }
    const res = await fetch(`${API}/check_compatibility`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            solvers: state.summarySolvers.map(s => s.name),
            problems: state.summaryProblems.map(p => p.name)
        })
    });
    const data = await res.json();
    state.compatibility = data.compatibility || {};
    render();
}

async function runExperiment() {
    if (!state.summarySolvers.length) { alert("Please add at least one solver."); return; }
    if (!state.summaryProblems.length) { alert("Please add at least one problem."); return; }

    const payload = {
        last_run_id: state.lastRunId,
        experiment_params: {
            num_macroreps: state.macroreps,
            num_postreps: state.prValues.num_post_reps || 100,
            num_postnorms: state.pnValues.num_post_reps_init_opt || 100,
        },
        problems: state.summaryProblems.map(p => ({
            name: p.name, rename: p.name,
            fixed_factors: p.params.reduce((acc, param) => {
                const v = parseValue(param.value);
                if (v !== null) acc[param.name] = v;
                return acc;
            }, {}),
            model_fixed_factors: {}
        })),
        solvers: state.summarySolvers.map(s => ({
            name: s.name, rename: s.name,
            fixed_factors: s.params.reduce((acc, param) => {
                const v = parseValue(param.value);
                if (v !== null) acc[param.name] = v;
                return acc;
            }, {})
        })),
        plots: state.summaryPlots.map(pl => ({
            plot_type: pl.name,
            params: pl.params.reduce((acc, param) => {
                const v = parseValue(param.value);
                if (v !== null) acc[param.name] = v;
                return acc;
            }, {}),
            solvers: pl.solvers?.length > 0 ? pl.solvers : null,
            problems: pl.problems?.length > 0 ? pl.problems : null,
        }))
    };

    const res = await fetch(`${API}/api/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    state.lastRunId = data.id;
    window.open(`/results/${data.id}/index.html`, "_blank");
}

// ── Summary actions ──
async function addSolverToSummary() {
    if (!state.selectedSolverName) return;
    const entry = { name: state.selectedSolverName, params: deepCopyParams(state.solverParams), expanded: false };
    if (state.editMode?.kind === "solver") {
        state.summarySolvers[state.editMode.index] = entry;
    } else {
        state.summarySolvers.push(entry);
    }
    state.selectedSolverName = ""; state.solverParams = []; state.editMode = null;
    await checkCompatibility();
    render();
}

async function addProblemToSummary() {
    if (!state.selectedProblemName) return;
    const entry = { name: state.selectedProblemName, params: deepCopyParams(state.problemParams), expanded: false };
    if (state.editMode?.kind === "problem") {
        state.summaryProblems[state.editMode.index] = entry;
    } else {
        state.summaryProblems.push(entry);
    }
    state.selectedProblemName = ""; state.problemParams = []; state.editMode = null;
    await checkCompatibility();
    render();
}

function addPlotToSummary() {
    if (!state.selectedPlotName) return;
    const entry = {
        name: state.selectedPlotName,
        params: deepCopyParams(state.plotParams),
        solvers: [...state.selectedPlotSolvers],
        problems: [...state.selectedPlotProblems],
        expanded: false
    };
    if (state.editMode?.kind === "plot") {
        state.summaryPlots[state.editMode.index] = entry;
    } else {
        state.summaryPlots.push(entry);
    }
    state.selectedPlotName = ""; state.plotParams = [];
    state.selectedPlotSolvers = []; state.selectedPlotProblems = [];
    state.editMode = null;
    render();
}

async function startEdit(kind, index) {
    if (kind === "solver") {
        const s = state.summarySolvers[index];
        state.selectedSolverName = s.name;
        state.solverParams = deepCopyParams(s.params);
        state.editMode = { kind: "solver", index };
    } else if (kind === "problem") {
        const p = state.summaryProblems[index];
        state.selectedProblemName = p.name;
        state.problemParams = deepCopyParams(p.params);
        state.editMode = { kind: "problem", index };
    } else if (kind === "plot") {
        const pl = state.summaryPlots[index];
        state.selectedPlotName = pl.name;
        state.plotParams = await fetchPlotParams(pl.name);
        state.plotParams = state.plotParams.map((p, i) => ({
            ...p, value: pl.params[i]?.value ?? p.value
        }));
        state.selectedPlotSolvers = [...(pl.solvers || [])];
        state.selectedPlotProblems = [...(pl.problems || [])];
        state.editMode = { kind: "plot", index };
    }
    render();
}

function requestEdit(kind, index) {
    const occupied = (kind === "solver" && state.selectedSolverName) ||
                     (kind === "problem" && state.selectedProblemName) ||
                     (kind === "plot" && state.selectedPlotName);
    if (occupied) {
        state.showConfirm = true;
        state.confirmKind = kind;
        state.confirmIndex = index;
        render();
    } else {
        startEdit(kind, index);
    }
}

// ── Render ──
function navigate(page) {
    state.currentPage = page;
    render();
}

function render() {
    document.getElementById("app").innerHTML = buildUI();
    attachEventListeners();
}

function paramInput(param, idx, arrayName) {
    if (param.name === "ref_solver") {
        const options = state.summarySolvers.map(s =>
            `<option value="${s.name}" ${param.value === s.name ? "selected" : ""}>${s.name}</option>`
        ).join("");
        return `<select onchange="updateParam('${arrayName}', ${idx}, this.value)">
            <option value="">— None —</option>${options}</select>`;
    } else if (typeof param.default === "boolean") {
        return `<select onchange="updateParam('${arrayName}', ${idx}, this.value)">
            <option value="true" ${param.value === "true" ? "selected" : ""}>True</option>
            <option value="false" ${param.value !== "true" ? "selected" : ""}>False</option>
        </select>`;
    } else {
        return `<input type="text" value="${param.value ?? ""}" 
            oninput="updateParam('${arrayName}', ${idx}, this.value)">`;
    }
}

window.updateParam = function(arrayName, idx, value) {
    state[arrayName][idx].value = value;
};

window.navigate = navigate;
window.addSolverToSummary = addSolverToSummary;
window.addProblemToSummary = addProblemToSummary;
window.addPlotToSummary = addPlotToSummary;
window.requestEdit = requestEdit;
window.runExperiment = runExperiment;

window.removeSolver = function(i) {
    state.summarySolvers.splice(i, 1);
    checkCompatibility();
    render();
};
window.removeProblem = function(i) {
    state.summaryProblems.splice(i, 1);
    checkCompatibility();
    render();
};
window.removePlot = function(i) {
    state.summaryPlots.splice(i, 1);
    render();
};
window.toggleExpand = function(kind, i) {
    if (kind === "solver") state.summarySolvers[i].expanded = !state.summarySolvers[i].expanded;
    else if (kind === "problem") state.summaryProblems[i].expanded = !state.summaryProblems[i].expanded;
    else if (kind === "plot") state.summaryPlots[i].expanded = !state.summaryPlots[i].expanded;
    render();
};
window.closeConfirm = function() {
    state.showConfirm = false; state.confirmKind = null; state.confirmIndex = null;
    render();
};
window.confirmProceed = function() {
    const kind = state.confirmKind, index = state.confirmIndex;
    state.showConfirm = false; state.confirmKind = null; state.confirmIndex = null;
    startEdit(kind, index);
};
window.openCompatModal = function() {
    if (state.summarySolvers.length && state.summaryProblems.length) {
        state.showCompatModal = true; render();
    }
};
window.closeCompatModal = function() { state.showCompatModal = false; render(); };
window.togglePostProcess = function() { state.showPostProcess = !state.showPostProcess; render(); };
window.togglePostNormalize = function() { state.showPostNormalize = !state.showPostNormalize; render(); };

function buildUI() {
    if (state.currentPage !== "Simulator") {
        return `<div class="card" style="margin-top:2rem;"><h2>${state.currentPage}</h2><p>Coming soon.</p></div>`;
    }

    // Solver params
    const solverParamsHtml = state.selectedSolverName ? `
        <div class="param-box">
            <p class="param-title">Solver Parameters</p>
            ${state.solverParams.map((p, idx) => `
                <label>
                    <div style="display:flex;align-items:center;gap:0.4rem;">
                        <span>${p.name}</span>
                        ${p.description ? `<span class="info-wrapper"><span class="info-icon">ℹ</span><div class="tooltip">${p.description}</div></span>` : ""}
                    </div>
                    ${paramInput(p, idx, "solverParams")}
                </label>`).join("")}
        </div>` : "";

    // Problem params
    const problemParamsHtml = state.selectedProblemName ? `
        <div class="param-box">
            <p class="param-title">Problem Parameters</p>
            ${state.problemParams.map((p, idx) => `
                <label>
                    <div style="display:flex;align-items:center;gap:0.4rem;">
                        <span>${p.name}</span>
                        ${p.description ? `<span class="info-wrapper"><span class="info-icon">ℹ</span><div class="tooltip">${p.description}</div></span>` : ""}
                    </div>
                    ${paramInput(p, idx, "problemParams")}
                </label>`).join("")}
        </div>` : "";

    // Plot params
    const plotParamsHtml = state.plotParams.length ? `
        <div class="param-box" style="margin-top:.5rem;">
            <p class="param-title">Plot Parameters (${state.selectedPlotName})</p>
            ${state.plotParams.map((p, i) => `
                <label>
                    <div style="display:flex;align-items:center;gap:0.4rem;">
                        <span>${p.name}</span>
                        ${p.description ? `<span class="info-wrapper"><span class="info-icon">ℹ</span><div class="tooltip">${p.description}</div></span>` : ""}
                    </div>
                    ${paramInput(p, i, "plotParams")}
                </label>`).join("")}
        </div>` : "";

    // Solver/problem checkboxes for plot
    const plotSolverChecks = state.selectedPlotName ? `
        <div class="param-box" style="margin-top:.5rem;">
            <p class="param-title">Select Solvers (leave empty for all)</p>
            ${state.summarySolvers.length === 0 ? '<p style="color:#6b7280;font-size:0.9rem;">No solvers added yet</p>' :
            state.summarySolvers.map(s => `
                <label style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.25rem;">
                    <input type="checkbox" value="${s.name}" 
                        ${state.selectedPlotSolvers.includes(s.name) ? "checked" : ""}
                        onchange="togglePlotSolver('${s.name}', this.checked)">
                    <span>${s.name}</span>
                </label>`).join("")}
        </div>
        <div class="param-box" style="margin-top:.5rem;">
            <p class="param-title">Select Problems (leave empty for all)</p>
            ${state.summaryProblems.length === 0 ? '<p style="color:#6b7280;font-size:0.9rem;">No problems added yet</p>' :
            state.summaryProblems.map(p => `
                <label style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.25rem;">
                    <input type="checkbox" value="${p.name}"
                        ${state.selectedPlotProblems.includes(p.name) ? "checked" : ""}
                        onchange="togglePlotProblem('${p.name}', this.checked)">
                    <span>${p.name}</span>
                </label>`).join("")}
        </div>` : "";

    // Summary solvers
    const summarySolversHtml = state.summarySolvers.length === 0 ? '<p style="color:#6b7280;">No solvers added.</p>' :
        state.summarySolvers.map((s, i) => `
            <div class="summary-item">
                <button class="summary-toggle pill" onclick="toggleExpand('solver', ${i})" title="${s.name}">
                    <span class="pill-text">${s.name}</span>
                    <span class="pill-right">
                        <span class="pill-chevron">${s.expanded ? "▼" : "▶"}</span>
                        <span class="pill-close" onclick="event.stopPropagation(); removeSolver(${i})">×</span>
                    </span>
                </button>
                ${s.expanded ? `
                    <ul class="param-list" style="margin:.5rem 0;">
                        ${s.params.map(p => `<li><strong>${p.name}:</strong> ${p.value ?? p.default ?? ""}</li>`).join("")}
                    </ul>
                    <button class="secondary-outline" onclick="requestEdit('solver', ${i})">Edit</button>` : ""}
            </div>`).join("");

    // Summary problems
    const summaryProblemsHtml = state.summaryProblems.length === 0 ? '<p style="color:#6b7280;">No problems added.</p>' :
        state.summaryProblems.map((p, i) => `
            <div class="summary-item">
                <button class="summary-toggle pill" onclick="toggleExpand('problem', ${i})" title="${p.name}">
                    <span class="pill-text">${p.name}</span>
                    <span class="pill-right">
                        <span class="pill-chevron">${p.expanded ? "▼" : "▶"}</span>
                        <span class="pill-close" onclick="event.stopPropagation(); removeProblem(${i})">×</span>
                    </span>
                </button>
                ${p.expanded ? `
                    <ul class="param-list" style="margin:.5rem 0;">
                        ${p.params.map(q => `<li><strong>${q.name}:</strong> ${q.value ?? q.default ?? ""}</li>`).join("")}
                    </ul>
                    <button class="secondary-outline" onclick="requestEdit('problem', ${i})">Edit</button>` : ""}
            </div>`).join("");

    // Summary plots
    const summaryPlotsHtml = state.summaryPlots.length === 0 ? '<p style="color:#6b7280;">No plots added.</p>' :
        state.summaryPlots.map((pl, i) => `
            <div class="summary-item">
                <button class="summary-toggle pill" onclick="toggleExpand('plot', ${i})" title="${pl.name}">
                    <span class="pill-text">${pl.name}</span>
                    <span class="pill-right">
                        <span class="pill-chevron">${pl.expanded ? "▼" : "▶"}</span>
                        <span class="pill-close" onclick="event.stopPropagation(); removePlot(${i})">×</span>
                    </span>
                </button>
                ${pl.expanded ? `
                    ${pl.params?.length ? `
                        <ul class="param-list" style="margin:.5rem 0;">
                            ${pl.params.map(p => `<li><strong>${p.name}:</strong> ${p.value ?? p.default ?? ""}</li>`).join("")}
                        </ul>` : '<p style="margin:.5rem 0;color:#6b7280;">No parameters.</p>'}
                    <button class="secondary-outline" onclick="requestEdit('plot', ${i})">Edit</button>` : ""}
            </div>`).join("");

    // Compatibility
    const compatHtml = state.summarySolvers.length && state.summaryProblems.length ? buildCompatSection() : "";

    // Post replicate
    const prHtml = state.showPostProcess ? `
        <div class="dropdown-content">
            <div class="param-box">
                <p class="param-title">Options for Post-replication</p>
                ${state.prSchema.params.map(p => `
                    <label><span>${p.label}</span>
                        ${p.type === "bool"
                            ? `<select onchange="state.prValues['${p.name}'] = this.value === 'true'">
                                <option value="true" ${state.prValues[p.name] ? "selected" : ""}>Yes</option>
                                <option value="false" ${!state.prValues[p.name] ? "selected" : ""}>No</option>
                               </select>`
                            : `<input type="number" value="${state.prValues[p.name] ?? ""}" 
                                oninput="state.prValues['${p.name}'] = +this.value">`}
                    </label>`).join("")}
            </div>
        </div>` : "";

    // Post normalize
    const pnHtml = state.showPostNormalize ? `
        <div class="dropdown-content">
            <div class="param-box">
                <p class="param-title">Options for Post-normalize</p>
                ${state.pnSchema.params.map(p => `
                    <label><span>${p.label}</span>
                        ${p.type === "bool"
                            ? `<select onchange="state.pnValues['${p.name}'] = this.value === 'true'">
                                <option value="true" ${state.pnValues[p.name] ? "selected" : ""}>Yes</option>
                                <option value="false" ${!state.pnValues[p.name] ? "selected" : ""}>No</option>
                               </select>`
                            : `<input type="number" value="${state.pnValues[p.name] ?? ""}"
                                oninput="state.pnValues['${p.name}'] = +this.value">`}
                    </label>`).join("")}
            </div>
        </div>` : "";

    const confirmModal = state.showConfirm ? `
        <div class="modal-backdrop" onclick="closeConfirm()">
            <div class="modal" onclick="event.stopPropagation()">
                <h3>Replace current editor?</h3>
                <p>You already have a ${state.confirmKind} open. Unsaved changes will be lost.</p>
                <div class="modal-actions">
                    <button class="btn" onclick="closeConfirm()">Cancel</button>
                    <button class="btn btn-primary" onclick="confirmProceed()">Replace</button>
                </div>
            </div>
        </div>` : "";

    const compatModal = state.showCompatModal ? buildCompatModal() : "";

    return `
    <div class="row-3col">
        <div class="col-stack">
            <div class="card column">
                <h2>Choose Solver</h2>
                ${state.selectedSolverName ? `<button class="secondary-outline" style="margin-bottom:0.75rem;" onclick="addSolverToSummary()">
                    ${state.editMode?.kind === "solver" ? "Apply Changes" : "+ Add Solver"}</button>` : ""}
                <div class="block-header">
                    <select id="solver-select" onchange="onSolverChange(this.value)">
                        <option value="">— Select a Solver —</option>
                        ${state.allSolvers.map(s => `<option value="${s}" ${state.selectedSolverName === s ? "selected" : ""}>${s}</option>`).join("")}
                    </select>
                </div>
                ${solverParamsHtml}
            </div>

            <div class="card">
                <button class="dropdown" onclick="togglePostProcess()">
                    ${state.showPostProcess ? "▼" : "▶"} Post-replicate
                </button>
                ${prHtml}
            </div>

            <div class="card column">
                <h2>Choose Plot</h2>
                ${state.selectedPlotName ? `<button class="secondary-outline" style="margin-bottom:0.75rem;" onclick="addPlotToSummary()">
                    ${state.editMode?.kind === "plot" ? "Apply Changes" : "+ Add Plot"}</button>` : ""}
                <div class="block-header">
                    <select id="plot-select" onchange="onPlotChange(this.value)">
                        <option value="">— Select a Plot —</option>
                        ${state.allPlots.map(p => `<option value="${p}" ${state.selectedPlotName === p ? "selected" : ""}>${p}</option>`).join("")}
                    </select>
                </div>
                ${plotParamsHtml}
                ${plotSolverChecks}
            </div>
        </div>

        <div class="col-stack">
            <div class="card column">
                <h2>Choose Problem</h2>
                ${state.selectedProblemName ? `<button class="secondary-outline" style="margin-bottom:0.75rem;" onclick="addProblemToSummary()">
                    ${state.editMode?.kind === "problem" ? "Apply Changes" : "+ Add Problem"}</button>` : ""}
                <div class="block-header">
                    <select id="problem-select" onchange="onProblemChange(this.value)">
                        <option value="">— Select a Problem —</option>
                        ${state.allProblems.map(p => `<option value="${p}" ${state.selectedProblemName === p ? "selected" : ""}>${p}</option>`).join("")}
                    </select>
                </div>
                ${problemParamsHtml}
            </div>

            <div class="card">
                <button class="dropdown" onclick="togglePostNormalize()">
                    ${state.showPostNormalize ? "▼" : "▶"} Post-normalize
                </button>
                ${pnHtml}
            </div>
        </div>

        <div class="right-column">
            <div class="summary card">
                <h3>Summary</h3>
                <div class="summary-section">
                    <p><strong>Solvers</strong></p>
                    ${summarySolversHtml}
                </div>
                <div class="summary-section" style="margin-top:1rem;">
                    <p><strong>Problems</strong></p>
                    ${summaryProblemsHtml}
                </div>
                <div class="summary-section" style="margin-top:1rem;">
                    <p><strong>Plots</strong></p>
                    ${summaryPlotsHtml}
                </div>
            </div>
            ${compatHtml}
        </div>
    </div>

    <div class="button-row">
        <button class="primary" onclick="runExperiment()">Run Experiment</button>
    </div>

    ${confirmModal}
    ${compatModal}`;
}

function buildCompatSection() {
    let g = 0, r = 0;
    for (const s of state.summarySolvers) {
        for (const p of state.summaryProblems) {
            const cell = state.compatibility?.[s.name]?.[p.name];
            if (cell && typeof cell.compatible === "boolean") {
                if (cell.compatible) g++; else r++;
            }
        }
    }
    const total = g + r;
    const greenPct = total > 0 ? Math.round((g * 1000) / total) / 10 : 0;
    const redPct = total > 0 ? Math.round((r * 1000) / total) / 10 : 0;
    const hasIncompat = r > 0;

    return `
    <div class="card compatibility-section compact">
        <div class="compat-header">
            <h3>Compatibility</h3>
            ${total > 0 ? `<span class="compat-header-pct">${greenPct}% compatible</span>` : ""}
        </div>
        ${total > 0 ? `
            <div class="compat-progress">
                <div class="compat-bar">
                    <div class="bar-green" style="width:${greenPct}%"></div>
                    <div class="bar-red" style="width:${redPct}%"></div>
                </div>
            </div>` : '<p class="compat-progress-empty">Add at least one solver and problem.</p>'}
        <button class="compat-trigger ${hasIncompat ? "red-btn" : "green-btn"}" 
            onclick="openCompatModal()" style="display:block;width:100%;margin-top:.75rem;">
            Open matrix
        </button>
    </div>`;
}

function buildCompatModal() {
    const rows = state.summarySolvers.map(s => `
        <tr>
            <th class="solver-name" title="${s.name}">${abbrev(s.name)}</th>
            ${state.summaryProblems.map(p => {
                const cell = state.compatibility?.[s.name]?.[p.name];
                const cls = cell ? (cell.compatible ? "ok" : "bad") : "neutral";
                return `<td class="compat-cell ${cls}">&nbsp;</td>`;
            }).join("")}
        </tr>`).join("");

    return `
    <div class="modal-backdrop" onclick="closeCompatModal()">
        <div class="modal" onclick="event.stopPropagation()">
            <h3 style="margin-top:0">Solver–Problem Compatibility</h3>
            <table class="compatibility-table compact">
                <thead>
                    <tr>
                        <th>S \\ P</th>
                        ${state.summaryProblems.map(p => `<th title="${p.name}">${abbrev(p.name)}</th>`).join("")}
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
            <div class="modal-actions" style="margin-top:0.75rem;">
                <button class="btn" onclick="closeCompatModal()">Close</button>
            </div>
        </div>
    </div>`;
}

function attachEventListeners() {
    // nothing needed since we use inline handlers
}

// ── Global event handlers ──
window.onSolverChange = async function(name) {
    state.selectedSolverName = name;
    state.solverParams = name ? await fetchSolverParams(name) : [];
    render();
};

window.onProblemChange = async function(name) {
    state.selectedProblemName = name;
    state.problemParams = name ? await fetchProblemParams(name) : [];
    render();
};

window.onPlotChange = async function(name) {
    state.selectedPlotName = name;
    state.editMode = null;
    state.plotParams = name ? await fetchPlotParams(name) : [];
    state.selectedPlotSolvers = [];
    state.selectedPlotProblems = [];
    render();
};

window.togglePlotSolver = function(name, checked) {
    if (checked) state.selectedPlotSolvers.push(name);
    else state.selectedPlotSolvers = state.selectedPlotSolvers.filter(s => s !== name);
};

window.togglePlotProblem = function(name, checked) {
    if (checked) state.selectedPlotProblems.push(name);
    else state.selectedPlotProblems = state.selectedPlotProblems.filter(p => p !== name);
};

// ── Init ──
async function init() {
    try {
        const [sRes, pRes, plRes, prRes, pnRes] = await Promise.all([
            fetch(`${API}/solvers`),
            fetch(`${API}/problems`),
            fetch(`${API}/plots`),
            fetch(`${API}/postreplicate_schema`),
            fetch(`${API}/postnormalize_schema`),
        ]);
        state.allSolvers = (await sRes.json()).solvers || [];
        state.allProblems = (await pRes.json()).problems || [];
        state.allPlots = (await plRes.json()).plots || [];
        state.prSchema = await prRes.json();
        state.pnSchema = await pnRes.json();
        state.prValues = Object.fromEntries(state.prSchema.params.map(p => [p.name, p.default]));
        state.pnValues = Object.fromEntries(state.pnSchema.params.map(p => [p.name, p.default]));
    } catch(e) {
        console.error("Init failed:", e);
    }
    render();
}

init();