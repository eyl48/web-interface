from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from simopt.directory import (
    problem_unabbreviated_directory,
    solver_unabbreviated_directory,
)
from simopt.experiment_base import ProblemsSolvers
from simopt.directory import solver_directory, problem_directory
import inspect

app = FastAPI(title="SimOpt API")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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