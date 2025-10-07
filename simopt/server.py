from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from simopt.directory import problem_unabbreviated_directory, solver_unabbreviated_directory
import inspect
import json

app = FastAPI(title="SimOpt API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_default(value):
    """Convert lists, tuples, numpy arrays, etc. to JSON-safe strings."""
    try:
        if callable(value):
            value = value()
        if isinstance(value, (list, tuple, dict)):
            return json.loads(json.dumps(value))  # clean JSON object
        return value
    except Exception:
        return str(value)


def extract_pydantic_fields(cls):
    """Extract Pydantic model fields from any class."""
    params = []
    for name, field in cls.model_fields.items():
        default_val = (
            field.default
            if field.default is not None
            else (field.default_factory() if field.default_factory is not None else None)
        )
        params.append({
            "name": name,
            "default": serialize_default(default_val),
            "description": field.description or "",
        })
    return params


@app.get("/problems")
def get_problems():
    return {"problems": list(problem_unabbreviated_directory.keys())}


@app.get("/solvers")
def get_solvers():
    return {"solvers": list(solver_unabbreviated_directory.keys())}


@app.get("/solver_params/{solver_name}")
def get_solver_params(solver_name: str):
    solver_cls = solver_unabbreviated_directory.get(solver_name)
    if not solver_cls:
        return {"parameters": []}

    params = []
    config_cls = getattr(solver_cls, "config_class", None)

    if config_cls and hasattr(config_cls, "model_fields"):
        params.extend(extract_pydantic_fields(config_cls))
    else:
        try:
            instance = solver_cls()
            if hasattr(instance, "params"):
                for name, meta in instance.params.items():
                    params.append({
                        "name": name,
                        "default": meta.get("default") if isinstance(meta, dict) else None,
                        "description": meta.get("description") if isinstance(meta, dict) else "",
                    })
        except Exception:
            pass

    return {"parameters": params}


@app.get("/problem_params/{problem_name}")
def get_problem_params(problem_name: str):
    problem_cls = problem_unabbreviated_directory.get(problem_name)
    if not problem_cls:
        return {"parameters": []}

    params = []

    config_cls = getattr(problem_cls, "config_class", None)
    if config_cls and hasattr(config_cls, "model_fields"):
        params.extend(extract_pydantic_fields(config_cls))
        return {"parameters": params}

    for _, obj in inspect.getmembers(problem_cls):
        if inspect.isclass(obj) and hasattr(obj, "model_fields"):
            params.extend(extract_pydantic_fields(obj))
            return {"parameters": params}

    try:
        instance = problem_cls()
        if hasattr(instance, "params"):
            for name, meta in instance.params.items():
                params.append({
                    "name": name,
                    "default": meta.get("default") if isinstance(meta, dict) else None,
                    "description": meta.get("description") if isinstance(meta, dict) else "",
                })
    except Exception:
        pass

    return {"parameters": params}
