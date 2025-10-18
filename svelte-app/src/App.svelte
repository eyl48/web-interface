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
      <!-- === Choose Solver Section === -->
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

      <!-- === Choose Problem Section === -->
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

      <!-- === Summary Section === -->
      <div class="summary card">
        <h3>Summary</h3>

        <!-- Solvers -->
        <div class="summary-section">
          <p><strong>Solvers:</strong></p>
          {#each solvers as solver, si}
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
                    <li>
                      <strong>{param.name}:</strong> {param.default ?? ""}
                      {#if param.description}
                        <span class="info-wrapper summary-info" aria-hidden="true">
                          <span class="info-icon">ℹ</span>
                          <div class="tooltip">{param.description}</div>
                        </span>
                      {/if}
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>
          {/each}
        </div>

        <!-- Problems -->
        <div class="summary-section">
          <p><strong>Problems:</strong></p>
          {#each problems as problem, pi}
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
                    <li>
                      <strong>{param.name}:</strong> {param.default ?? ""}
                      {#if param.description}
                        <span class="info-wrapper summary-info" aria-hidden="true">
                          <span class="info-icon">ℹ</span>
                          <div class="tooltip">{param.description}</div>
                        </span>
                      {/if}
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    </div>

    <!-- === Additional Controls === -->
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

  /* NAVBAR */
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

  .nav-left {
    flex-shrink: 0;
  }

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

  /* === Layout Fix === */
  .row-3col {
    display: grid;
    grid-template-columns: 0.7fr 0.7fr 0.45fr; /* slightly narrower solver/problem */
    gap: 1.75rem; /* slightly reduced gap for balance */
    margin-bottom: 1.5rem;
    align-items: start;
  } 

  /* Prevent cards from stretching the grid */
  .row-3col > .card {
    align-self: start;
    min-width: 0;
  }

  /* Summary Panel */
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

  .summary ul {
    padding-left: 1rem;
    margin: 0.25rem 0 1rem;
  }

  .summary li {
    font-size: 14px;
    color: #374151;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .card {
    background: #ffffff;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    margin-bottom: 1.5rem;
  }

  .summary-item {
    margin-bottom: 0.6rem;
  }

  .summary-toggle {
    background: none;
    border: none;
    color: #1d4ed8;
    font-weight: 600;
    cursor: pointer;
    text-align: left;
    width: 100%;
    padding: 0.25rem 0;
    transition: color 0.2s ease;
  }

  .summary-toggle:hover {
    color: #1e40af;
  }

  .param-list {
    list-style: none;
    padding-left: 1.2rem;
    margin: 0.25rem 0 0.5rem;
    color: #374151;
    font-size: 14px;
  }

  .param-list li {
    margin-bottom: 0.2rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .solver-block,
  .problem-block {
    margin-bottom: 1rem;
    width: 100%;
    overflow-x: hidden;
  }

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

  .remove-btn:hover {
    color: #111827;
  }

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

  .param-box {
    border: 1px solid #93c5fd;
    background: #eff6ff;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    margin-top: 0.5rem;
  }

  /* Make each parameter row flex and neatly aligned */
  .param-box .param-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.4rem;
  }

  .param-title {
    margin: 0 0 0.5rem;
    font-weight: 600;
    color: #1d4ed8;
  }

  .param-box label {
    display: flex;
    align-items: center;
    margin-bottom: 0.4rem;
  }

  .param-box label span {
    width: 150px; /* fixed label width — keeps right edges aligned */
    flex-shrink: 0;
    text-align: left;
  }

  .param-box input[type="text"],
  .param-box input[type="number"] {
    flex: 1;
    max-width: 180px; /* adjust as needed */
    text-align: right;
    margin-left: 0.75rem; /* small gap between label and input */
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 0.35rem 0.5rem;
    font-size: 14px;
    box-sizing: border-box;
  }

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

  .cta:hover {
    background-color: #1e40af;
  }

  .secondary-outline {
    background: white;
    border: 1px solid #2563eb;
    color: #2563eb;
    padding: 0.4rem 0.8rem;
    margin-top: 0.5rem;
  }

  .secondary-outline:hover {
    background: #eff6ff;
  }

  .button-row {
    display: flex;
    justify-content: flex-start;
    margin: 1rem 0;
  }

  .dropdown-row {
    margin-top: 2rem;
    display: flex;
    gap: 1.5rem;
  }

  .dropdown-container {
    flex: 1;
  }

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

  .dropdown:hover {
    background: #a6c8ff;
  }

  .dropdown-content {
    border: 1px solid #c7d2fe;
    background: #f9fafb;
    padding: 0.75rem;
    margin-top: 0.5rem;
    border-radius: 6px;
  }

    /* === Tooltip Styling === */
  .info-wrapper {
    position: relative;
    display: inline-block;
    cursor: help;
  }

  .info-icon {
    font-size: 0.9rem;
    color: #2563eb;
    border-radius: 50%;
    padding: 0 4px;
  }

  .tooltip {
    visibility: hidden;
    opacity: 0;
    transition: opacity 0.2s ease;
    position: absolute;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    background-color: #111827;
    color: #f9fafb;
    text-align: left;
    border-radius: 4px;
    padding: 0.4rem 0.6rem;
    white-space: normal;
    width: max-content;
    max-width: 250px;
    font-size: 0.8rem;
    line-height: 1.2;
    z-index: 1000;
  }

  /* Show tooltip on hover */
  .info-wrapper:hover .tooltip {
    visibility: visible;
    opacity: 1;
  }

  /* Tooltip arrow */
  .tooltip::after {
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border-width: 5px;
    border-style: solid;
    border-color: #111827 transparent transparent transparent;
  }
</style>
