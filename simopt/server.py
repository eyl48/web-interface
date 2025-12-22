from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from simopt.directory import (
    problem_unabbreviated_directory,
    solver_unabbreviated_directory,
)
from simopt.experiment_base import ProblemsSolvers
from simopt.experiment_base import PlotProgressCurvesConfig, PlotType
import inspect
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from simopt import experiment_base as eb

app = FastAPI(title="SimOpt API")

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

@app.get("/postreplicate_schema")
def postreplicate_schema() -> Dict[str, Any]:
    """
    Returns a simple schema for the post-replicate form.
    We try to pull defaults from experiment_base; otherwise we fall back.
    """
    d = {
        "num_post_reps": 100,
        "crn_diff_times": True,
        "crn_diff_macroreps": True,
    }
    # overlay with experiment_base values if present
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
    """
    Returns a simple schema for the post-normalize form.
    """
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
    """
    Returns a flat list of plot names derived from experiment_base.PlotType.
    """
    if not hasattr(eb, "PlotType"):
        # Keep this graceful so UI can handle it
        return {"plots": [], "source": "missing PlotType"}

    PlotType = getattr(eb, "PlotType")

    # Try normal Enum iteration first
    plots = []
    try:
        plots = [member.name for member in PlotType]  # works if PlotType is an Enum
        source = "enum"
    except TypeError:
        # If PlotType isn't an Enum, fall back to uppercase attributes (constants-style)
        plots = [n for n in dir(PlotType) if n.isupper()]
        source = "class-attrs"

    return {"plots": plots, "source": source}

def extract_params_from_config(config_cls):
    """Extract parameter info (name, default, description) from a Pydantic BaseModel config."""
    params = []
    if config_cls and hasattr(config_cls, "model_fields"):
        for name, field in config_cls.model_fields.items():
            # Handle callable defaults (default_factory)
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


@app.get("/problems")
def get_problems():
    """Return all available problems."""
    return {"problems": list(problem_unabbreviated_directory.keys())}


@app.get("/solvers")
def get_solvers():
    """Return all available solvers."""
    return {"solvers": list(solver_unabbreviated_directory.keys())}


@app.get("/solver_params/{solver_name}")
def get_solver_params(solver_name: str):
    solver_cls = solver_unabbreviated_directory.get(solver_name)
    if solver_cls is None:
        return {"parameters": []}

    params = []
    config_cls = getattr(solver_cls, "config_class", None)
    params += extract_params_from_config(config_cls)

    return {"parameters": params}


@app.get("/problem_params/{problem_name}")
def get_problem_params(problem_name: str):
    """Return parameters for both the problem and its model config."""
    problem_cls = problem_unabbreviated_directory.get(problem_name)
    if problem_cls is None:
        return {"parameters": []}

    params = []
    # Get parameters from problem’s own config class
    config_cls = getattr(problem_cls, "config_class", None)
    params += extract_params_from_config(config_cls)

    # Check if the problem defines a model_class or model attribute
    model_cls = getattr(problem_cls, "model_class", None)
    if model_cls is not None:
        model_config_cls = getattr(model_cls, "config_class", None)
        params += extract_params_from_config(model_config_cls)
    else:
        # Some problems instantiate model directly inside __init__
        # Try to find it dynamically
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
    """
    Return parameter specs for plots that need them.
    For now, only MEAN (progress curves) exposes parameters to the UI.
    """
    name = plot_name.strip().upper()
    if name == "MEAN":
        return {"parameters": extract_params_from_config(PlotProgressCurvesConfig)}
    # No params for other plot types right now
    return {"parameters": []}


@app.post("/check_compatibility")
def check_compatibility(payload: dict):
    solvers = payload.get("solvers", [])
    problems = payload.get("problems", [])

    compatibility = {}

    for solver_name in solvers:
        solver_cls = solver_unabbreviated_directory.get(solver_name)
        if not solver_cls:
            continue
        solver = solver_cls()
        compatibility[solver_name] = {}

        for problem_name in problems:
            problem_cls = problem_unabbreviated_directory.get(problem_name)
            if not problem_cls:
                continue
            problem = problem_cls()

            # --- Create temporary experiment ---
            try:
                exp = ProblemsSolvers(solvers=[solver], problems=[problem])
                err = exp.check_compatibility()
                if err.strip() == "":
                    compatibility[solver_name][problem_name] = {"compatible": True, "message": ""}
                else:
                    compatibility[solver_name][problem_name] = {"compatible": False, "message": err}
            except Exception as e:
                compatibility[solver_name][problem_name] = {"compatible": False, "message": str(e)}

    return {"compatibility": compatibility}