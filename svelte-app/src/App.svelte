<script>
  import { onMount } from 'svelte';

  let currentPage = "Simulator";

  // State variables for ALL available options (fetched from backend)
  let allSolvers = [];
  let allProblems = [];

  // State variables for the CURRENTLY selected solvers and problems.
  // These are now empty by default and will be populated on mount.
  let solvers = [];
  let problems = [];

  // Dropdown toggles
  let showPostProcess = false;
  let showPostNormalize = false;

  function navigate(page) {
    currentPage = page;
  }

  // Adds a new solver block to the UI
  function addSolver() {
    if (allSolvers.length > 0) {
      solvers = [...solvers, { id: solvers.length, name: allSolvers[0] }];
    } else {
      console.error('No solvers available to add.');
    }
  }

  // Adds a new problem block to the UI
  function addProblem() {
    if (allProblems.length > 0) {
      problems = [...problems, { id: problems.length, name: allProblems[0] }];
    } else {
      console.error('No problems available to add.');
    }
  }

  function removeSolver(index) {
    solvers = solvers.filter((_, i) => i !== index);
  }

  function removeProblem(index) {
    problems = problems.filter((_, i) => i !== index);
  }

  // Use the onMount lifecycle function to fetch data when the component loads.
  onMount(async () => {
    try {
      // Fetch the list of solvers from your backend API
      const solversResponse = await fetch('http://localhost:8000/solvers');
      const solversData = await solversResponse.json();
      allSolvers = solversData.solvers;

      // Initialize the 'solvers' array with the first fetched item
      if (allSolvers.length > 0) {
        solvers = [{ id: 0, name: allSolvers[0] }];
      }

    } catch (error) {
      console.error('Error fetching solvers:', error);
    }

    try {
      // Fetch the list of problems from your backend API
      const problemsResponse = await fetch('http://localhost:8000/problems');
      const problemsData = await problemsResponse.json();
      allProblems = problemsData.problems;

      // Initialize the 'problems' array with the first fetched item
      if (allProblems.length > 0) {
        problems = [{ id: 0, name: allProblems[0] }];
      }
      
    } catch (error) {
      console.error('Error fetching problems:', error);
    }
  });
</script>

<nav>
  <div class="nav-left">
    <span class="title">SimOpt Web Interface</span>
  </div>
  <div class="nav-right">
    <ul>
      <li class={currentPage === "Simulator" ? "active" : ""} on:click={() => navigate("Simulator")}>
        Simulator
      </li>
      <li class={currentPage === "User Guide" ? "active" : ""} on:click={() => navigate("User Guide")}>
        User Guide
      </li>
      <li class={currentPage === "About Us" ? "active" : ""} on:click={() => navigate("About Us")}>
        About Us
      </li>
    </ul>
  </div>
</nav>

<main>
  {#if currentPage === "Simulator"}
    <div class="row-3col">
      <div class="card column">
        <h2>Choose Solver</h2>
        {#each solvers as solver, i}
          <div class="solver-block">
            <div class="block-header">
              <select bind:value={solver.name}>
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
              <label><input type="checkbox" /> Solver Param 1</label><br />
              <label><input type="checkbox" /> Solver Param 2</label><br />
              <label><input type="checkbox" /> Solver Param 3</label>
            </div>
          </div>
        {/each}
        <button class="secondary-outline" on:click={addSolver}>+ Add Solver</button>
      </div>

      <div class="card column">
        <h2>Choose Problem</h2>
        {#each problems as problem, i}
          <div class="problem-block">
            <div class="block-header">
              <select bind:value={problem.name}>
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
              <label><input type="checkbox" /> Problem Param 1</label><br />
              <label><input type="checkbox" /> Problem Param 2</label><br />
              <label><input type="checkbox" /> Problem Param 3</label>
            </div>
          </div>
        {/each}
        <button class="secondary-outline" on:click={addProblem}>+ Add Problem</button>
      </div>

      <div class="summary card">
        <h3>Summary</h3>
        <p><strong>Solvers:</strong></p>
        <ul>
          {#each solvers as solver}
            <li>{solver.name}</li>
          {/each}
        </ul>
        <p><strong>Problems:</strong></p>
        <ul>
          {#each problems as problem}
            <li>{problem.name}</li>
          {/each}
        </ul>
      </div>
    </div>

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
          <div class="dropdown-content">
            <p>Post-process options will go here...</p>
          </div>
        {/if}
      </div>

      <div class="dropdown-container">
        <button class="dropdown" on:click={() => (showPostNormalize = !showPostNormalize)}>
          {showPostNormalize ? "▼" : "▶"} Post-Normalize
        </button>
        {#if showPostNormalize}
          <div class="dropdown-content">
            <p>Post-normalize options will go here...</p>
          </div>
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
    flex-shrink: 0; /* don't shrink title */
  }

  .title {
    font-size: 2rem;        /* make it bigger again */
    font-weight: 700;
    color: #0f172a;
    white-space: nowrap;    /* prevent wrapping */
  }

  .nav-right ul {
    display: flex;
    gap: 1.25rem; /* tighter spacing */
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
    border-bottom: 2px solid #14b8a6; /* teal accent underline */
  }

  /* CONTENT */
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

  .row-3col {
    display: grid;
    grid-template-columns: 1fr 1fr 0.6fr; /* smaller summary column */
    gap: 2rem;
    margin-bottom: 1.5rem;
    align-items: flex-start;
  }

  .column {
    flex: 1;
  }

  /* Card Styling */
  .card {
    background: #ffffff;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    margin-bottom: 1.5rem;
  }

  .solver-block,
  .problem-block {
    margin-bottom: 1rem;
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
  input[type="number"] {
    margin: 0.5rem 0;
    padding: 0.5rem;
    width: 100%;
    max-width: 300px;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 15px;
  }

  .param-box {
    border: 1px solid #93c5fd;
    background: #eff6ff;
    padding: 0.6rem;
    border-radius: 6px;
    margin-top: 0.5rem;
  }

  .param-title {
    margin: 0 0 0.5rem;
    font-weight: 600;
    color: #1d4ed8;
  }

  /* Buttons */
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

  /* Dropdowns */
  .dropdown-row {
    margin-top: 2rem;
    display: flex;
    gap: 1.5rem;
  }

  .dropdown-container {
    flex: 1;
  }

.dropdown {
  background: #d0e2ff;    /* your chosen color */
  color: #1e3a8a;          /* dark blue text */
  padding: 0.6rem 1rem;
  border-radius: 6px;
  border: 1px solid #a6c8ff; /* subtle border */
  width: 100%;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
}

.dropdown:hover {
  background: #a6c8ff;  /* darker hover version */
}

  .dropdown-content {
    border: 1px solid #c7d2fe;
    background: #f9fafb;
    padding: 0.75rem;
    margin-top: 0.5rem;
    border-radius: 6px;
  }

  /* Summary */
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
  }
</style>