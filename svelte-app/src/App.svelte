<script>
  import { onMount } from 'svelte';

  let currentPage = "Simulator";
  let allSolvers = [];
  let allProblems = [];
  let solvers = [];
  let problems = [];
  let showPostProcess = false;
  let showPostNormalize = false;

  function navigate(page) {
    currentPage = page;
  }

  function abbrev(name) {
    if (!name) return "";
    const clean = String(name).replace(/[^A-Za-z0-9]/g, ""); // strip spaces/punct
    return clean.slice(-4).toUpperCase();                     // last 4, uppercased
  }

  async function fetchSolverParams(name) {
    const res = await fetch(`http://localhost:8000/solver_params/${encodeURIComponent(name)}`);
    const data = await res.json();
    return data.parameters || [];
  }

  async function fetchProblemParams(name) {
    const res = await fetch(`http://localhost:8000/problem_params/${encodeURIComponent(name)}`);
    const data = await res.json();
    return data.parameters || [];
  }

  async function addSolver() {
    if (allSolvers.length > 0) {
      const name = allSolvers[0];
      const params = await fetchSolverParams(name);
      solvers = [...solvers, { id: solvers.length, name, params }];
    }
  }

  async function addProblem() {
    if (allProblems.length > 0) {
      const name = allProblems[0];
      const params = await fetchProblemParams(name);
      problems = [...problems, { id: problems.length, name, params }];
    }
  }

  async function updateSolverParams(i, name) {
    const params = await fetchSolverParams(name);
    solvers[i].params = params;
    solvers = [...solvers];
  }

  async function updateProblemParams(i, name) {
    const params = await fetchProblemParams(name);
    problems[i].params = params;
    problems = [...problems];
  }

  function removeSolver(index) {
    solvers = solvers.filter((_, i) => i !== index);
  }

  function removeProblem(index) {
    problems = problems.filter((_, i) => i !== index);
  }

  onMount(async () => {
    try {
      const solversRes = await fetch('http://localhost:8000/solvers');
      allSolvers = (await solversRes.json()).solvers;
      if (allSolvers.length > 0) {
        const params = await fetchSolverParams(allSolvers[0]);
        solvers = [{ id: 0, name: allSolvers[0], params }];
      }
    } catch (err) {
      console.error("Error fetching solvers:", err);
    }

    try {
      const problemsRes = await fetch('http://localhost:8000/problems');
      allProblems = (await problemsRes.json()).problems;
      if (allProblems.length > 0) {
        const params = await fetchProblemParams(allProblems[0]);
        problems = [{ id: 0, name: allProblems[0], params }];
      }
    } catch (err) {
      console.error("Error fetching problems:", err);
    }
  });

  let compatibility = {}; // stores compatibility matrix

  async function checkCompatibility() {
    if (solvers.length === 0 || problems.length === 0) {
      compatibility = {};
      return;
    }

    const payload = {
      solvers: solvers.map((s) => s.name),
      problems: problems.map((p) => p.name)
    };

    try {
      const res = await fetch("http://localhost:8000/check_compatibility", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      compatibility = data.compatibility || {};
    } catch (err) {
      console.error("Error checking compatibility:", err);
    }
  }

  // Re-run check when solvers/problems change
  $: checkCompatibility(solvers, problems);
</script>

<nav>
  <div class="nav-left">
    <span class="title">SimOpt Web Interface</span>
  </div>
  <div class="nav-right">
    <ul>
      <li class={currentPage === "Simulator" ? "active" : ""} on:click={() => navigate("Simulator")}>Simulator</li>
      <li class={currentPage === "User Guide" ? "active" : ""} on:click={() => navigate("User Guide")}>User Guide</li>
      <li class={currentPage === "About Us" ? "active" : ""} on:click={() => navigate("About Us")}>About Us</li>
    </ul>
  </div>
</nav>

<main>
  {#if currentPage === "Simulator"}
    <div class="row-3col">
      <!-- === Left: Choose Solver === -->
      <div class="card column">
        <h2>Choose Solver</h2>
        {#each solvers as solver, i}
          <div class="solver-block">
            <div class="block-header">
              <select bind:value={solver.name} on:change={(e) => updateSolverParams(i, e.target.value)}>
                {#each allSolvers as option}
                  <option>{option}</option>
                {/each}
              </select>
              {#if i > 0}
                <button class="remove-btn" on:click={() => removeSolver(i)}>×</button>
              {/if}
            </div>

            <div class="param-box">
              <p class="param-title">Solver Parameters</p>
              {#each solver.params as param}
                <label>
                  <div style="display:flex;align-items:center;gap:0.4rem;">
                    <span>{param.name}</span>
                    {#if param.description}
                      <span class="info-wrapper" aria-hidden="true">
                        <span class="info-icon">ℹ</span>
                        <div class="tooltip">{param.description}</div>
                      </span>
                    {/if}
                  </div>
                  <input type="text" value={param.default ?? ""} />
                </label>
              {/each}
            </div>
          </div>
        {/each}
        <button class="secondary-outline" on:click={addSolver}>+ Add Solver</button>
      </div>

      <!-- === Middle: Choose Problem === -->
      <div class="card column">
        <h2>Choose Problem</h2>
        {#each problems as problem, i}
          <div class="problem-block">
            <div class="block-header">
              <select bind:value={problem.name} on:change={(e) => updateProblemParams(i, e.target.value)}>
                {#each allProblems as option}
                  <option>{option}</option>
                {/each}
              </select>
              {#if i > 0}
                <button class="remove-btn" on:click={() => removeProblem(i)}>×</button>
              {/if}
            </div>

            <div class="param-box">
              <p class="param-title">Problem Parameters</p>
              {#each problem.params as param}
                <label>
                  <div style="display:flex;align-items:center;gap:0.4rem;">
                    <span>{param.name}</span>
                    {#if param.description}
                      <span class="info-wrapper" aria-hidden="true">
                        <span class="info-icon">ℹ</span>
                        <div class="tooltip">{param.description}</div>
                      </span>
                    {/if}
                  </div>
                  <input type="text" value={param.default ?? ""} />
                </label>
              {/each}
            </div>
          </div>
        {/each}
        <button class="secondary-outline" on:click={addProblem}>+ Add Problem</button>
      </div>

      <!-- === Right Column: Summary + Compatibility === -->
      <div class="right-column">
        <div class="summary card">
          <h3>Summary</h3>

          <!-- Solvers -->
          <div class="summary-section">
            <p><strong>Solvers:</strong></p>
            {#each solvers as solver}
              <div class="summary-item">
                <button
                  class="summary-toggle"
                  on:click={() => {
                    solver.expanded = !solver.expanded;
                    solvers = [...solvers];
                  }}
                >
                  {solver.expanded ? "▼" : "▶"} {solver.name}
                </button>
                {#if solver.expanded}
                  <ul class="param-list">
                    {#each solver.params as param}
                      <li><strong>{param.name}:</strong> {param.default ?? ""}</li>
                    {/each}
                  </ul>
                {/if}
              </div>
            {/each}
          </div>

          <!-- Problems -->
          <div class="summary-section">
            <p><strong>Problems:</strong></p>
            {#each problems as problem}
              <div class="summary-item">
                <button
                  class="summary-toggle"
                  on:click={() => {
                    problem.expanded = !problem.expanded;
                    problems = [...problems];
                  }}
                >
                  {problem.expanded ? "▼" : "▶"} {problem.name}
                </button>
                {#if problem.expanded}
                  <ul class="param-list">
                    {#each problem.params as param}
                      <li><strong>{param.name}:</strong> {param.default ?? ""}</li>
                    {/each}
                  </ul>
                {/if}
              </div>
            {/each}
          </div>
        </div>

        {#if Object.keys(compatibility).length > 0}
          <div class="card compatibility-section compact">
            <h3>Compatibility</h3>
            <table class="compatibility-table compact" aria-label="Solver–Problem compatibility matrix">
              <thead>
                <tr>
                  <th scope="col">S \ P</th>
                  {#each problems as p}
                    <th scope="col" title={p.name}>{abbrev(p.name)}</th>
                  {/each}
                </tr>
              </thead>
              <tbody>
                {#each solvers as s}
                  <tr>
                    <th class="solver-name" scope="row" title={s.name}>{abbrev(s.name)}</th>
                    {#each problems as p}
                      <td
                        class={
                          compatibility[s.name]?.[p.name]
                            ? (compatibility[s.name][p.name].compatible ? 'compat-cell ok' : 'compat-cell bad')
                            : 'compat-cell neutral'
                        }
                        title={
                          compatibility[s.name]?.[p.name] && !compatibility[s.name][p.name].compatible && compatibility[s.name][p.name].message
                            ? `${s.name} × ${p.name}: ${compatibility[s.name][p.name].message}`
                            : ''
                        }
                      >
                        &nbsp;
                      </td>
                    {/each}
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    </div>

    <!-- === Controls under grid === -->
    <div class="card section">
      <label>Number of Macroreplications</label><br />
      <input type="number" value="10" />
    </div>

    <div class="row dropdown-row">
      <div class="dropdown-container">
        <button class="dropdown" on:click={() => (showPostProcess = !showPostProcess)}>
          {showPostProcess ? "▼" : "▶"} Post-Process
        </button>
        {#if showPostProcess}
          <div class="dropdown-content"><p>Post-process options will go here...</p></div>
        {/if}
      </div>

      <div class="dropdown-container">
        <button class="dropdown" on:click={() => (showPostNormalize = !showPostNormalize)}>
          {showPostNormalize ? "▼" : "▶"} Post-Normalize
        </button>
        {#if showPostNormalize}
          <div class="dropdown-content"><p>Post-normalize options will go here...</p></div>
        {/if}
      </div>
    </div>

    <div class="card section">
      <label><input type="checkbox" /> Save outputs to pickle file</label>
    </div>

    <div class="button-row">
      <button class="cta">Run Experiment</button>
    </div>
  {/if}
</main>


<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  body, main, input, button, select, label {
    font-family: 'Inter', sans-serif;
    font-size: 15px;
  }

  /* === NAVBAR === */
  nav {
    background: #e5e7eb;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.5rem;
    width: 100%;
    box-sizing: border-box;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .nav-left { flex-shrink: 0; }

  .title {
    font-size: 2rem;
    font-weight: 700;
    color: #0f172a;
    white-space: nowrap;
  }

  .nav-right ul {
    display: flex;
    gap: 1.25rem;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .nav-right li {
    cursor: pointer;
    font-weight: 500;
    color: #374151;
    white-space: nowrap;
  }

  .nav-right li.active {
    color: #0f172a;
    border-bottom: 2px solid #14b8a6;
  }

  /* === MAIN LAYOUT === */
  main {
    font-family: 'Inter', sans-serif;
    margin: 100px 20px 20px;
  }

  h2 {
    color: #2563eb;
    margin-top: 0;
    margin-bottom: 0.75rem;
    font-size: 1.2em;
    font-weight: 600;
  }

  /* Three-column layout: solvers | problems | right column (summary+compat) */
  .row-3col {
    display: grid;
    grid-template-columns: 0.7fr 0.7fr 0.45fr;
    gap: 1.75rem;
    margin-bottom: 1.5rem;
    align-items: start;
  }

  .row-3col > .card { align-self: start; min-width: 0; }

  /* Right column stacks Summary + Compatibility */
  .right-column {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    min-width: 0;
  }

  /* === SUMMARY PANEL === */
  .summary {
    max-height: 75vh;
    overflow-y: auto;
    overflow-x: hidden;
    white-space: normal;
    word-wrap: break-word;
    background: #fafafa;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1rem;
  }

  .summary h3 {
    margin-top: 0;
    color: #0f172a;
    font-size: 1.1em;
  }

  .summary ul { padding-left: 1rem; margin: 0.25rem 0 1rem; }

  .summary li {
    font-size: 14px;
    color: #374151;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* Spacing between summary items */
  .summary-section { margin-bottom: 1rem; }
  .summary-item + .summary-item { margin-top: 0.75rem; }

  /* Outlined toggle buttons inside summary */
  .summary-toggle {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.65rem 0.9rem;
    background: #ffffff;              /* white fill */
    color: #1e3a8a;                   /* blue-ish text */
    border: 1.5px solid #2563eb;      /* blue outline */
    border-radius: 10px;
    font-weight: 600;
    line-height: 1.2;
    cursor: pointer;
    transition: background-color .15s ease, box-shadow .15s ease, border-color .15s ease;
  }
  .summary-toggle:hover {
    background: #eff6ff;              /* light blue hover */
    box-shadow: 0 1px 4px rgba(37, 99, 235, 0.15);
  }
  .summary-toggle:active { background: #dbeafe; }
  .summary-toggle:focus-visible {
    outline: 3px solid rgba(37, 99, 235, .35);
    outline-offset: 2px;
  }

  /* === CARDS === */
  .card {
    background: #ffffff;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    margin-bottom: 1.5rem;
  }

  .solver-block, .problem-block { margin-bottom: 1rem; width: 100%; overflow-x: hidden; }

  .block-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .remove-btn {
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
    line-height: 1;
    color: #6b7280;
  }
  .remove-btn:hover { color: #111827; }

  /* === INPUTS & SELECTS === */
  select,
  input[type="number"],
  input[type="text"] {
    margin: 0.5rem 0;
    padding: 0.5rem;
    width: 100%;
    max-width: 300px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 15px;
    box-sizing: border-box;
  }

  /* === PARAMETER BOX === */
  .param-box {
    border: 1px solid #93c5fd;
    background: #eff6ff;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    margin-top: 0.5rem;
    position: relative;
    overflow: visible !important; /* tooltips shouldn't be clipped */
  }

  .param-title {
    margin: 0 0 0.5rem;
    font-weight: 600;
    color: #1d4ed8;
  }

  /* Label row layout */
  .param-box label {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 0.5rem; /* tight gap between name and input */
    margin-bottom: 0.4rem;
  }

  /* Label text column */
  .param-box label span {
    flex: 0 0 140px; /* tidy left column */
    text-align: left;
  }

  /* Input */
  .param-box input[type="text"],
  .param-box input[type="number"] {
    flex: 1;
    max-width: 200px;   /* longer inputs but still align right edge */
    text-align: right;
    margin-left: 8px;   /* small space from label */
  }

  /* === BUTTONS === */
  button {
    font-size: 15px;
    font-weight: 500;
    border-radius: 6px;
    cursor: pointer;
  }

  .cta {
    background-color: #2563eb;
    color: white;
    font-weight: 600;
    padding: 0.75rem 2rem;
    border: none;
    font-size: 16px;
  }
  .cta:hover { background-color: #1e40af; }

  .secondary-outline {
    background: white;
    border: 1px solid #2563eb;
    color: #2563eb;
    padding: 0.4rem 0.8rem;
    margin-top: 0.5rem;
  }
  .secondary-outline:hover { background: #eff6ff; }

  .button-row { display: flex; justify-content: flex-start; margin: 1rem 0; }

  /* === DROPDOWN SECTIONS === */
  .dropdown-row { margin-top: 2rem; display: flex; gap: 1.5rem; }
  .dropdown-container { flex: 1; }

  .dropdown {
    background: #d0e2ff;
    color: #1e3a8a;
    padding: 0.6rem 1rem;
    border-radius: 6px;
    border: 1px solid #a6c8ff;
    width: 100%;
    font-weight: 500;
    cursor: pointer;
    text-align: left;
  }
  .dropdown:hover { background: #a6c8ff; }

  .dropdown-content {
    border: 1px solid #c7d2fe;
    background: #f9fafb;
    padding: 0.75rem;
    margin-top: 0.5rem;
    border-radius: 6px;
  }

  /* === INFO ICON + TOOLTIP === */
  .info-wrapper {
    position: relative;
    display: inline-block;
    margin-left: 4px;
    vertical-align: text-top;
    z-index: 1000;
  }

  .info-icon {
    font-size: 0.8rem;
    color: #2563eb;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 15px;
    height: 15px;
    background-color: #e0f2fe;
    border: 1px solid #93c5fd;
    cursor: help;
    transform: translateY(-2px);
  }

  .tooltip {
    position: absolute;
    bottom: 130%;
    left: 0;
    transform: translateX(-10%);
    background-color: #111827;
    color: #f9fafb;
    text-align: left;
    border-radius: 6px;
    padding: 0.4rem 0.6rem;
    white-space: normal;
    width: max-content;
    max-width: 280px;
    font-size: 0.8rem;
    line-height: 1.3;
    z-index: 3000;
    visibility: hidden;
    opacity: 0;
    transition: opacity 0.2s ease;
    overflow-wrap: break-word;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  }

  .tooltip::after {
    content: "";
    position: absolute;
    top: 100%;
    left: 12px;
    border-width: 5px;
    border-style: solid;
    border-color: #111827 transparent transparent transparent;
  }

  .info-wrapper:hover .tooltip { visibility: visible; opacity: 1; }

  /* === COMPATIBILITY MATRIX (colored cells) === */
  .compatibility-section { padding: 1rem; border: 1px solid #e5e7eb; border-radius: 8px; background: #fafafa; }
  .compatibility-section.compact { padding: 0.75rem; }

  .compatibility-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 0.75rem;
    text-align: center;
    table-layout: fixed;
  }
  .compatibility-table.compact { font-size: 12px; }

  .compatibility-table th,
  .compatibility-table td {
    border: 1px solid #d1d5db;
    padding: 0.55rem;
    font-size: 0.95rem;
  }
  .compatibility-table.compact th,
  .compatibility-table.compact td { padding: 0.35rem; }

  .compatibility-table thead th {
    background: #dbeafe;
    color: #1e3a8a;
    font-weight: 600;
  }

  .solver-name {
    font-weight: 600;
    background: #eff6ff;
    text-align: left;
    padding-left: 0.5rem;
    width: auto; /* shrink to acronym */
  }

  .compat-cell {
    transition: background-color 0.15s ease, color 0.15s ease;
    font-weight: 600;
    min-width: 28px;
    height: 24px;
    line-height: 1;
  }

  .compat-cell.ok   { background: #dcfce7; color: #166534; }
  .compat-cell.bad  { background: #fee2e2; color: #991b1b; }
  .compat-cell.neutral { background: #f3f4f6; color: #6b7280; }
</style>


