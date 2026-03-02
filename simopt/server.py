import uuid
import threading
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import inspect
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from simopt import experiment_base as eb
import seaborn as sns

from simopt.directory import (
    problem_unabbreviated_directory,
    solver_unabbreviated_directory,
    problem_directory,
    solver_directory,
)
from simopt.experiment_base import ProblemsSolvers, PlotProgressCurvesConfig, PlotTerminalProgressCurvesConfig, PlotSolvabilityCDFConfig, PlotTerminalScatterplotsConfig, PlotSolvabilityProfilesConfig, PlotAreaScatterplotsConfig


class ProblemRequest(BaseModel):
    name: str
    rename: Optional[str] = None
    fixed_factors: Dict[str, Any]
    model_fixed_factors: Dict[str, Any] = {}


class SolverRequest(BaseModel):
    name: str
    rename: Optional[str] = None
    fixed_factors: Dict[str, Any]


class PlotRequest(BaseModel):
    plot_type: str
    params: Dict[str, Any] = {}


class ExperimentParams(BaseModel):
    num_macroreps: int
    num_postreps: int
    num_postnorms: int


class ExperimentRequest(BaseModel):
    experiment_params: ExperimentParams
    problems: List[ProblemRequest]
    solvers: List[SolverRequest]
    plots: List[PlotRequest]


app = FastAPI(title="SimOpt API")
Path("results").mkdir(exist_ok=True)
app.mount("/results", StaticFiles(directory="results"), name="results")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from simopt.experiment_base import POST_REPLICATE_DEFAULTS, POST_NORMALIZE_DEFAULTS
except Exception:
    POST_REPLICATE_DEFAULTS = {}
    POST_NORMALIZE_DEFAULTS = {}


def create_name_mappings():
    """Create bidirectional mappings between abbreviated and full names."""
    solver_abbr_to_full = {}
    solver_full_to_abbr = {}
    
    for abbr_name in solver_directory.keys():
        solver_cls = solver_directory[abbr_name]
        full_name = getattr(solver_cls, 'class_name', abbr_name)
        display_name = f"{abbr_name} ({full_name})" if full_name != abbr_name else abbr_name
        solver_abbr_to_full[abbr_name] = display_name
        solver_full_to_abbr[display_name] = abbr_name
    
    problem_abbr_to_full = {}
    problem_full_to_abbr = {}
    
    for abbr_name in problem_directory.keys():
        problem_cls = problem_directory[abbr_name]
        full_name = getattr(problem_cls, 'class_name', abbr_name)
        display_name = f"{abbr_name} ({full_name})" if full_name != abbr_name else abbr_name
        problem_abbr_to_full[abbr_name] = display_name
        problem_full_to_abbr[display_name] = abbr_name
    
    return solver_abbr_to_full, solver_full_to_abbr, problem_abbr_to_full, problem_full_to_abbr


SOLVER_ABBR_TO_FULL, SOLVER_FULL_TO_ABBR, PROBLEM_ABBR_TO_FULL, PROBLEM_FULL_TO_ABBR = create_name_mappings()


@app.get("/postreplicate_schema")
def postreplicate_schema() -> Dict[str, Any]:
    """Returns a simple schema for the post-replicate form."""
    d = {
        "num_post_reps": 100,
        "crn_diff_times": True,
        "crn_diff_macroreps": True,
    }
    d.update(POST_REPLICATE_DEFAULTS or {})
    return {
        "params": [
            {
                "name": "num_post_reps",
                "label": "Number of post-replications",
                "type": "int",
                "default": d["num_post_reps"],
            },
            {
                "name": "crn_diff_times",
                "label": "Use CRN on post-replications for solutions recommended at different times?",
                "type": "bool",
                "default": d["crn_diff_times"],
            },
            {
                "name": "crn_diff_macroreps",
                "label": "Use CRN on post-replications for solutions recommended on different macro-replications?",
                "type": "bool",
                "default": d["crn_diff_macroreps"],
            },
        ]
    }


@app.get("/postnormalize_schema")
def postnormalize_schema() -> Dict[str, Any]:
    """Returns a simple schema for the post-normalize form."""
    d = {
        "num_post_reps_init_opt": 100,
        "crn_init_opt": True,
    }
    d.update(POST_NORMALIZE_DEFAULTS or {})
    return {
        "params": [
            {
                "name": "num_post_reps_init_opt",
                "label": "Number of post-replications at initial and optimal solutions",
                "type": "int",
                "default": d["num_post_reps_init_opt"],
            },
            {
                "name": "crn_init_opt",
                "label": "Use CRN on post-replications for initial and optimal solution?",
                "type": "bool",
                "default": d["crn_init_opt"],
            },
        ]
    }


@app.get("/plots")
def list_plots():
    """Returns a flat list of plot names derived from experiment_base.PlotType."""
    if not hasattr(eb, "PlotType"):
        return {"plots": [], "source": "missing PlotType"}

    PlotType = getattr(eb, "PlotType")

    plots = []
    try:
        plots = [member.name for member in PlotType]
        source = "enum"
    except TypeError:
        plots = [n for n in dir(PlotType) if n.isupper()]
        source = "class-attrs"

    return {"plots": plots, "source": source}


def extract_params_from_config(config_cls):
    """Extract parameter info (name, default, description) from a Pydantic BaseModel config."""
    params = []
    if config_cls and hasattr(config_cls, "model_fields"):
        for name, field in config_cls.model_fields.items():
            default = None
            if field.default_factory is not None:
                try:
                    default = field.default_factory()
                except Exception:
                    default = "<factory>"
            else:
                default = field.default

            params.append(
                {
                    "name": name,
                    "default": default,
                    "description": field.description or "",
                }
            )
    return params


@app.get("/solvers")
def get_solvers():
    """Return all available solvers with display names."""
    return {"solvers": list(SOLVER_ABBR_TO_FULL.values())}


@app.get("/problems")
def get_problems():
    """Return all available problems with display names."""
    return {"problems": list(PROBLEM_ABBR_TO_FULL.values())}


@app.get("/solver_params/{solver_name}")
def get_solver_params(solver_name: str):
    """Return parameters for a solver (accepts display name)."""
    # Convert display name to abbreviated name
    abbr_name = SOLVER_FULL_TO_ABBR.get(solver_name, solver_name)
    solver_cls = solver_directory.get(abbr_name)
    if solver_cls is None:
        return {"parameters": []}

    params = []
    config_cls = getattr(solver_cls, "config_class", None)
    params += extract_params_from_config(config_cls)

    return {"parameters": params}


@app.get("/problem_params/{problem_name}")
def get_problem_params(problem_name: str):
    """Return parameters for both the problem and its model config (accepts display name)."""
    # Convert display name to abbreviated name
    abbr_name = PROBLEM_FULL_TO_ABBR.get(problem_name, problem_name)
    problem_cls = problem_directory.get(abbr_name)
    if problem_cls is None:
        return {"parameters": []}

    params = []
    config_cls = getattr(problem_cls, "config_class", None)
    params += extract_params_from_config(config_cls)

    model_cls = getattr(problem_cls, "model_class", None)
    if model_cls is not None:
        model_config_cls = getattr(model_cls, "config_class", None)
        params += extract_params_from_config(model_config_cls)
    else:
        try:
            sig = inspect.signature(problem_cls)
            if "model" in sig.parameters:
                model_default = sig.parameters["model"].default
                model_config_cls = getattr(model_default.__class__, "config_class", None)
                params += extract_params_from_config(model_config_cls)
        except Exception:
            pass

    return {"parameters": params}


@app.get("/plot_params/{plot_name}")
def get_plot_params(plot_name: str):
    """Return parameter specs for plots that need them."""
    name = plot_name.strip().upper()
    if name in ["ALL", "MEAN", "QUANTILE"]:
        return {"parameters": extract_params_from_config(PlotProgressCurvesConfig)}
    elif name in ["VIOLIN", "BOX"]:
        return {"parameters": extract_params_from_config(PlotTerminalProgressCurvesConfig)}
    elif name in ["CDF_SOLVABILITY", "QUANTILE_SOLVABILITY", "DIFFERENCE_OF_CDF_SOLVABILITY", "DIFFERENCE_OF_QUANTILE_SOLVABILITY"]:
        return {"parameters": extract_params_from_config(PlotSolvabilityProfilesConfig)}
    elif name in ["AREA", "AREA_MEAN", "AREA_STD_DEV"]:
        return {"parameters": extract_params_from_config(PlotAreaScatterplotsConfig)}
    elif name == "SOLVE_TIME_CDF":
        return {"parameters": extract_params_from_config(PlotSolvabilityCDFConfig)}
    elif name == "TERMINAL_SCATTER":
        return {"parameters": extract_params_from_config(PlotTerminalScatterplotsConfig)}
    return {"parameters": []}


@app.post("/check_compatibility")
def check_compatibility(payload: dict):
    """Check compatibility between solvers and problems."""
    solvers = payload.get("solvers", [])
    problems = payload.get("problems", [])

    compatibility = {}

    for display_name in solvers:
        abbr_name = SOLVER_FULL_TO_ABBR.get(display_name, display_name)
        solver_cls = solver_directory.get(abbr_name)
        if not solver_cls:
            continue
        solver = solver_cls()
        compatibility[display_name] = {}

        for prob_display_name in problems:
            prob_abbr_name = PROBLEM_FULL_TO_ABBR.get(prob_display_name, prob_display_name)
            problem_cls = problem_directory.get(prob_abbr_name)
            if not problem_cls:
                continue
            problem = problem_cls()

            try:
                exp = ProblemsSolvers(solvers=[solver], problems=[problem])
                err = exp.check_compatibility()
                if err.strip() == "":
                    compatibility[display_name][prob_display_name] = {"compatible": True, "message": ""}
                else:
                    compatibility[display_name][prob_display_name] = {"compatible": False, "message": err}
            except Exception as e:
                compatibility[display_name][prob_display_name] = {"compatible": False, "message": str(e)}

    return {"compatibility": compatibility}


@app.get("/debug/directories")
def debug_directories():
    """Debug endpoint to see what's in the directories."""
    return {
        "solvers_display": list(SOLVER_ABBR_TO_FULL.values())[:10],
        "problems_display": list(PROBLEM_ABBR_TO_FULL.values())[:10],
        "solver_mapping_sample": dict(list(SOLVER_FULL_TO_ABBR.items())[:3]),
        "problem_mapping_sample": dict(list(PROBLEM_FULL_TO_ABBR.items())[:3]),
    }


def run_experiment_async(run_id: str, payload: dict):
    """Run the experiment in a background thread."""
    folder = Path("svelte-app/results") / run_id
    
    try:
        update_status(folder, "Running experiments...")
        
        exp_params = payload.get("experiment_params", {})
        num_macroreps = exp_params.get("num_macroreps", 10)
        num_postreps = exp_params.get("num_postreps", 100)
        num_postnorms = exp_params.get("num_postnorms", 200)
        
        problems_config = payload.get("problems", [])
        solvers_config = payload.get("solvers", [])
        plots_config = payload.get("plots", [])
        
        # Convert display names to abbreviated names
        for solver_cfg in solvers_config:
            display_name = solver_cfg["name"]
            abbr_name = SOLVER_FULL_TO_ABBR.get(display_name, display_name)
            solver_cfg["name"] = abbr_name
            print(f"Converted solver: '{display_name}' -> '{abbr_name}'")
        
        for prob_cfg in problems_config:
            display_name = prob_cfg["name"]
            abbr_name = PROBLEM_FULL_TO_ABBR.get(display_name, display_name)
            prob_cfg["name"] = abbr_name
            print(f"Converted problem: '{display_name}' -> '{abbr_name}'")
        
        from simopt.experiment_base import ProblemSolver, post_normalize
        
        # Validate solver and problem names
        for solver_cfg in solvers_config:
            if solver_cfg["name"] not in solver_directory:
                raise ValueError(f"Solver '{solver_cfg['name']}' not found in solver directory. Available solvers: {list(solver_directory.keys())[:10]}")
        
        for prob_cfg in problems_config:
            if prob_cfg["name"] not in problem_directory:
                raise ValueError(f"Problem '{prob_cfg['name']}' not found in problem directory. Available problems: {list(problem_directory.keys())[:10]}")
        
        needed_solver_indices = set()
        needed_problem_indices = set()
        
        for plot_cfg in plots_config:
            plot_solvers = plot_cfg.get("solvers")
            plot_problems = plot_cfg.get("problems")
            
            if plot_solvers:
                plot_solver_abbrs = [SOLVER_FULL_TO_ABBR.get(s, s) for s in plot_solvers]
                for i, s in enumerate(solvers_config):
                    if s["name"] in plot_solver_abbrs:
                        needed_solver_indices.add(i)
            else:
                needed_solver_indices.update(range(len(solvers_config)))
            
            if plot_problems:
                plot_problem_abbrs = [PROBLEM_FULL_TO_ABBR.get(p, p) for p in plot_problems]
                for i, p in enumerate(problems_config):
                    if p["name"] in plot_problem_abbrs:
                        needed_problem_indices.add(i)
            else:
                needed_problem_indices.update(range(len(problems_config)))
        
        # Convert to sorted lists
        needed_solver_indices = sorted(list(needed_solver_indices))
        needed_problem_indices = sorted(list(needed_problem_indices))
        
        print(f"Running experiments for {len(needed_solver_indices)} solvers and {len(needed_problem_indices)} problems")

        # Run experiments for each problem
        all_experiments = []
        for prob_idx in needed_problem_indices:
            prob_cfg = problems_config[prob_idx]
            update_status(folder, f"Running problem {prob_idx + 1}: {prob_cfg['name']}...")
            
            experiments_same_problem = []
            
            for solver_idx in needed_solver_indices:
                solver_cfg = solvers_config[solver_idx]
                print(f"Creating ProblemSolver with solver={solver_cfg['name']}, problem={prob_cfg['name']}")
                print(f"  Solver factors: {solver_cfg.get('fixed_factors', {})}")
                print(f"  Problem factors: {prob_cfg.get('fixed_factors', {})}")
                
                experiment = ProblemSolver(
                    solver_name=solver_cfg["name"],
                    solver_rename=solver_cfg.get("rename", solver_cfg["name"]),
                    solver_fixed_factors=solver_cfg.get("fixed_factors", {}),
                    problem_name=prob_cfg["name"],
                    problem_rename=prob_cfg.get("rename", prob_cfg["name"]),
                    problem_fixed_factors=prob_cfg.get("fixed_factors", {}),
                    model_fixed_factors=prob_cfg.get("model_fixed_factors", {}),
                )
                
                print(f"Running experiment with {num_macroreps} macroreps...")
                experiment.run(n_macroreps=num_macroreps)
                print(f"Post-replicating with {num_postreps} postreps...")
                experiment.post_replicate(n_postreps=num_postreps)
                experiments_same_problem.append(experiment)
            
            # Post-normalize
            print(f"Post-normalizing with {num_postnorms} postnorms...")
            post_normalize(
                experiments=experiments_same_problem,
                n_postreps_init_opt=num_postnorms,
            )
            
            all_experiments.append(experiments_same_problem)

        solver_idx_map = {orig_idx: new_idx for new_idx, orig_idx in enumerate(needed_solver_indices)}
        problem_idx_map = {orig_idx: new_idx for new_idx, orig_idx in enumerate(needed_problem_indices)}
        
        # Generate plots
        update_status(folder, "Generating plots...")
        plot_files = []
        
        from simopt.experiment_base import PlotType, plot_progress_curves, plot_terminal_progress, plot_solvability_profiles, plot_solvability_cdfs, plot_terminal_scatterplots, plot_area_scatterplots
        for plot_cfg in plots_config:
            plot_type_name = plot_cfg.get("plot_type", "MEAN").upper()
            plot_params = plot_cfg.get("params", {})
            plot_solvers = plot_cfg.get("solvers")
            plot_problems = plot_cfg.get("problems")
            
            # Map selected indices to experiment array positions
            if plot_solvers:
                plot_solver_abbrs = [SOLVER_FULL_TO_ABBR.get(s, s) for s in plot_solvers]
                orig_solver_indices = [i for i, s in enumerate(solvers_config) if s["name"] in plot_solver_abbrs]
                solver_exp_indices = [solver_idx_map[i] for i in orig_solver_indices]
            else:
                solver_exp_indices = list(range(len(needed_solver_indices)))
            
            if plot_problems:
                plot_problem_abbrs = [PROBLEM_FULL_TO_ABBR.get(p, p) for p in plot_problems]
                orig_problem_indices = [i for i, p in enumerate(problems_config) if p["name"] in plot_problem_abbrs]
                problem_exp_indices = [problem_idx_map[i] for i in orig_problem_indices]
            else:
                problem_exp_indices = list(range(len(needed_problem_indices)))
            
            if not solver_exp_indices or not problem_exp_indices:
                continue
                        
            if plot_type_name in ["ALL", "MEAN", "QUANTILE"]:
                # Generate progress curves for each problem
                for exp_prob_idx in problem_exp_indices:
                    try:
                        plt.figure(figsize=(10, 6))

                        all_in_one = plot_params.get("all_in_one", True)
                        normalize = plot_params.get("normalize", False)

                        plot_type_map = {
                            "ALL": PlotType.ALL,
                            "MEAN": PlotType.MEAN,
                            "QUANTILE": PlotType.QUANTILE,
                        }
                        plot_type_enum = plot_type_map.get(plot_type_name, PlotType.MEAN)

                        plot_progress_curves(
                            [all_experiments[exp_prob_idx][exp_solver_idx] for exp_solver_idx in solver_exp_indices],
                            plot_type=plot_type_enum,
                            all_in_one=all_in_one,
                            normalize=normalize,
                        )
                        actual_prob_idx = needed_problem_indices[exp_prob_idx]
                        filename = f"{plot_type_name.lower()}_progress_curves_problem_{actual_prob_idx+1}.png"
                        plt.savefig(folder / filename, dpi=150, bbox_inches='tight')
                        plt.close()
                        plot_files.append(filename)
                        print(f"  Saved {filename}")
                    except Exception as e:
                        print(f"Error generating {plot_type_name} plot for problem {i+1}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
            
            elif plot_type_name in ["VIOLIN", "BOX"]:
                # Generate terminal progress plots (BOX or VIOLIN) for each problem
                for exp_prob_idx in problem_exp_indices:
                    try:
                        plt.figure(figsize=(10, 6))
                        
                        # Extract parameters with defaults
                        normalize = plot_params.get("normalize", True)
                        all_in_one = plot_params.get("all_in_one", True)
                        
                        # Determine which PlotType to use
                        plot_type_enum = PlotType.VIOLIN if plot_type_name == "VIOLIN" else PlotType.BOX
                        
                        plot_terminal_progress(
                            [all_experiments[exp_prob_idx][exp_solver_idx] for exp_solver_idx in solver_exp_indices],
                            plot_type=plot_type_enum,
                            normalize=normalize,
                            all_in_one=all_in_one,
                        )
                        actual_prob_idx = needed_problem_indices[exp_prob_idx]
                        filename = f"{plot_type_name.lower()}_progress_curves_problem_{actual_prob_idx+1}.png"
                        plt.savefig(folder / filename, dpi=150, bbox_inches='tight')
                        plt.close()
                        plot_files.append(filename)
                        print(f"  Saved {filename}")
                    except Exception as e:
                        print(f"Error generating {plot_type_name} plot for problem {i+1}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue

            elif plot_type_name in ["AREA", "AREA_MEAN", "AREA_STD_DEV"]:
                # Generate area scatterplots for each problem
                if len(problem_exp_indices) < 2:
                    print(f"Warning: {plot_type_name} requires multiple problems. Skipping.")
                    continue
                try:
                    print(f"Generating {plot_type_name} plot...")
                    plt.figure(figsize=(10, 6))
                    # Extract parameters with defaults
                    all_in_one = plot_params.get("all_in_one", True)
                    n_bootstraps = plot_params.get("n_bootstraps", 100)
                    conf_level = plot_params.get("conf_level", 0.95)
                    plot_conf_ints = plot_params.get("plot_conf_ints", True)
                    print_max_hw = plot_params.get("print_max_hw", True)
                    solver_set_name = plot_params.get("solver_set_name", "SOLVER_SET")
                    problem_set_name = plot_params.get("problem_set_name", "PROBLEM_SET")

                    plot_type_map = {
                        "AREA": PlotType.AREA,
                        "AREA_MEAN": PlotType.AREA_MEAN,
                        "AREA_STD_DEV": PlotType.AREA_STD_DEV
                    }
                    plot_type_enum = plot_type_map.get(plot_type_name)

                    filtered_experiments = [
                        [all_experiments[exp_prob_idx][exp_solver_idx] for exp_solver_idx in solver_exp_indices]
                        for exp_prob_idx in problem_exp_indices]   
                                        
                    plot_area_scatterplots(
                        filtered_experiments,
                        all_in_one=all_in_one,
                        n_bootstraps=n_bootstraps,
                        conf_level=conf_level,
                        plot_conf_ints=plot_conf_ints,
                        print_max_hw=print_max_hw,
                        solver_set_name=solver_set_name,
                        problem_set_name=problem_set_name,
                    )
                    filename = f"{plot_type_name.lower()}_area_scatterplot.png"
                    plt.savefig(folder / filename, dpi=150, bbox_inches='tight')
                    plt.close()
                    plot_files.append(filename)
                    print(f"  Saved {filename}")
                except Exception as e:
                    print(f"Error generating {plot_type_name} plot: {e}")
                    import traceback
                    traceback.print_exc()

            elif plot_type_name in ["CDF_SOLVABILITY", "QUANTILE_SOLVABILITY", "DIFFERENCE_OF_CDF_SOLVABILITY", "DIFFERENCE_OF_QUANTILE_SOLVABILITY"]:
                # Solvability profiles require multiple problems
                if len(problem_exp_indices) < 2:
                    print(f"Warning: {plot_type_name} requires multiple problems. Skipping.")
                    continue
                try:
                    print(f"Generating {plot_type_name} plot...")
                    plt.figure(figsize=(10, 6))
                    # Extract parameters with defaults
                    all_in_one = plot_params.get("all_in_one", True)
                    n_bootstraps = plot_params.get("n_bootstraps", 100)
                    conf_level = plot_params.get("conf_level", 0.95)
                    plot_conf_ints = plot_params.get("plot_conf_ints", False)  # Disabled by default
                    print_max_hw = plot_params.get("print_max_hw", False)
                    solve_tol = plot_params.get("solve_tol", 0.1)
                    beta = plot_params.get("beta", 0.5)
                    ref_solver = plot_params.get("ref_solver", None)
                    solver_set_name = plot_params.get("solver_set_name", "SOLVER_SET")
                    problem_set_name = plot_params.get("problem_set_name", "PROBLEM_SET")
                    # Map plot type name to PlotType enum
                    plot_type_map = {
                        "CDF_SOLVABILITY": PlotType.CDF_SOLVABILITY,
                        "QUANTILE_SOLVABILITY": PlotType.QUANTILE_SOLVABILITY,
                        "DIFFERENCE_OF_CDF_SOLVABILITY": PlotType.DIFFERENCE_OF_CDF_SOLVABILITY,
                        "DIFFERENCE_OF_QUANTILE_SOLVABILITY": PlotType.DIFFERENCE_OF_QUANTILE_SOLVABILITY,
                    }
                    plot_type_enum = plot_type_map.get(plot_type_name)

                    filtered_experiments = [
                        [all_experiments[exp_prob_idx][exp_solver_idx] for exp_solver_idx in solver_exp_indices]
                        for exp_prob_idx in problem_exp_indices]   
                                        
                    plot_solvability_profiles(
                        filtered_experiments,
                        plot_type=plot_type_enum,
                        all_in_one=all_in_one,
                        n_bootstraps=n_bootstraps,
                        conf_level=conf_level,
                        plot_conf_ints=plot_conf_ints,
                        print_max_hw=print_max_hw,
                        solve_tol=solve_tol,
                        beta=beta,
                        ref_solver=ref_solver,
                        solver_set_name=solver_set_name,
                        problem_set_name=problem_set_name,
                    )
                    filename = f"{plot_type_name.lower()}_solvability_profile.png"
                    plt.savefig(folder / filename, dpi=150, bbox_inches='tight')
                    plt.close()
                    plot_files.append(filename)
                    print(f"  Saved {filename}")
                except Exception as e:
                    print(f"Error generating {plot_type_name} plot: {e}")
                    import traceback
                    traceback.print_exc()

            elif plot_type_name == "SOLVE_TIME_CDF":
                # Generate solvability CDF plots for each problem
                for exp_prob_idx in problem_exp_indices:
                    try:
                        plt.figure(figsize=(10, 6))
                        
                        # Extract parameters with defaults
                        solve_tol = plot_params.get("solve_tol", 0.1)
                        all_in_one = plot_params.get("all_in_one", True)
                        n_bootstraps = plot_params.get("n_bootstraps", 100)
                        conf_level = plot_params.get("conf_level", 0.95)
                        plot_conf_ints = plot_params.get("plot_conf_ints", False)  # Disabled by default to avoid bootstrap errors
                        print_max_hw = plot_params.get("print_max_hw", False)
                                                
                        plot_solvability_cdfs(
                            [all_experiments[exp_prob_idx][exp_solver_idx] for exp_solver_idx in solver_exp_indices],
                            solve_tol=solve_tol,
                            all_in_one=all_in_one,
                            n_bootstraps=n_bootstraps,
                            conf_level=conf_level,
                            plot_conf_ints=plot_conf_ints,
                            print_max_hw=print_max_hw,
                        )
                        filename = f"solvability_cdf_problem_{i+1}.png"
                        plt.savefig(folder / filename, dpi=150, bbox_inches='tight')
                        plt.close()
                        plot_files.append(filename)
                        print(f"  Saved {filename}")
                    except Exception as e:
                        print(f"Error generating SOLVE_TIME_CDF plot for problem {i+1}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue

            elif plot_type_name == "TERMINAL_SCATTER":
                # Generate terminal scatterplot (requires multiple problems)
                if len(problem_exp_indices) < 2:
                    print("Warning: TERMINAL_SCATTER requires multiple problems. Skipping.")
                    continue
                    
                try:
                    print(f"Generating TERMINAL_SCATTER plot...")
                    plt.figure(figsize=(10, 6))
                    
                    # Extract parameters with defaults
                    all_in_one = plot_params.get("all_in_one", True)
                    solver_set_name = plot_params.get("solver_set_name", "SOLVER_SET")
                    problem_set_name = plot_params.get("problem_set_name", "PROBLEM_SET")

                    filtered_experiments = [
                        [all_experiments[exp_prob_idx][exp_solver_idx] for exp_solver_idx in solver_exp_indices]
                        for exp_prob_idx in problem_exp_indices]   
                            
                    plot_terminal_scatterplots(
                        filtered_experiments,
                        all_in_one=all_in_one,
                        solver_set_name=solver_set_name,
                        problem_set_name=problem_set_name,
                    )
                    filename = f"terminal_scatterplot.png"
                    plt.savefig(folder / filename, dpi=150, bbox_inches='tight')
                    plt.close()
                    plot_files.append(filename)
                    print(f"  Saved {filename}")
                except Exception as e:
                    print(f"Error generating TERMINAL_SCATTER plot: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Create final results page with plots
        update_status(folder, "Complete!", plot_files)
        print(f"Experiment {run_id} completed successfully!")
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        update_status(folder, error_msg)
        print(f"Experiment {run_id} failed: {error_msg}")
        import traceback
        traceback.print_exc()


def update_status(folder: Path, status: str, plot_files: list = None):
    """Update the results page with current status and plots."""
    run_id = folder.name
    
    plots_html = ""
    if plot_files:
        plots_html = '<div id="plots" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 1.5rem; margin-top: 1.5rem;">'
        for plot_file in plot_files:
            plots_html += f'''
            <div class="plot-container">
                <img src="{plot_file}" alt="{plot_file}">
                <p style="text-align: center; margin-top: 0.5rem; color: #6b7280; font-size: 0.9rem;">{plot_file}</p>
            </div>
            '''
        plots_html += '</div>'
    
    status_class = "success" if status == "Complete!" else ("error" if status.startswith("Error:") else "running")
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Experiment Results - {run_id}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', sans-serif; background: #f9fafb; min-height: 100vh; }}
        .header {{ background: #e5e7eb; padding: 1.5rem 2rem; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); margin-bottom: 2rem; }}
        .header h1 {{ color: #0f172a; font-size: 2rem; font-weight: 700; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 0 2rem 2rem; }}
        .card {{ background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); margin-bottom: 1.5rem; }}
        .card h2 {{ color: #2563eb; font-size: 1.2rem; margin-bottom: 1rem; }}
        .status {{ padding: 1rem; border-radius: 6px; margin-bottom: 1rem; }}
        .status.running {{ background: #eff6ff; border: 1px solid #93c5fd; }}
        .status.success {{ background: #dcfce7; border: 1px solid #86efac; }}
        .status.error {{ background: #fee2e2; border: 1px solid #fca5a5; }}
        .status p {{ margin: 0.5rem 0; }}
        .status.running p {{ color: #1e40af; }}
        .status.success p {{ color: #166534; }}
        .status.error p {{ color: #991b1b; }}
        .status strong {{ font-weight: 600; }}
        .plot-container {{ background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }}
        .plot-container img {{ width: 100%; height: auto; border-radius: 4px; display: block; }}
    </style>
    <script>
        // Auto-refresh while running
        if ("{status_class}" === "running") {{
            setTimeout(() => location.reload(), 3000);
        }}
    </script>
</head>
<body>
    <div class="header"><h1>Results</h1></div>
    <div class="container">
        <div class="card">
            <h2>Experiment Details</h2>
            <div class="status {status_class}">
                <p><strong>Experiment ID:</strong> {run_id}</p>
                <p><strong>Status:</strong> {status}</p>
            </div>
        </div>
        {plots_html}
    </div>
</body>
</html>"""
    
    with open(folder / "index.html", "w") as f:
        f.write(html_content)


@app.post("/api/run")
def run_experiment(payload: dict = Body(...)):
    from datetime import datetime
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = Path("svelte-app/results") / run_id
    folder.mkdir(parents=True, exist_ok=True)
    
    # Log the payload for debugging
    print("\n" + "="*60)
    print("RECEIVED EXPERIMENT REQUEST")
    print("="*60)
    print(f"Experiment ID: {run_id}")
    print(f"\nSolvers: {[s['name'] for s in payload.get('solvers', [])]}")
    print(f"Problems: {[p['name'] for p in payload.get('problems', [])]}")
    print("="*60 + "\n")
    
    # Create initial status page
    update_status(folder, "Initializing...")
    
    # Start experiment in background thread
    thread = threading.Thread(target=run_experiment_async, args=(run_id, payload))
    thread.daemon = True
    thread.start()
    
    return {"id": run_id}


@app.get("/api/results/{experiment_id}")
def get_results(experiment_id: str):
    """Get results for an experiment."""
    path = Path(f"svelte-app/results/{experiment_id}")
    images = [f"svelte-app/results/{experiment_id}/{p.name}" for p in path.glob("*.png")]
    return {"images": images}