from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from simopt.directory import problem_unabbreviated_directory, solver_unabbreviated_directory

app = FastAPI(title="SimOpt API")

# Configure CORS so Svelte frontend can access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev, you can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

    if config_cls is not None and hasattr(config_cls, "model_fields"):
        # Pydantic v2: model_fields is a dict of name -> FieldInfo
        for name, field in config_cls.model_fields.items():
            params.append({
                "name": name,
                "default": field.default,
                "description": field.description or ""
            })
    else:
        try:
            instance = solver_cls()
            if hasattr(instance, "params"):
                for name, meta in instance.params.items():
                    params.append({
                        "name": name,
                        "default": meta.get("default") if isinstance(meta, dict) else None,
                        "description": meta.get("description") if isinstance(meta, dict) else ""
                    })
        except Exception:
            pass

    return {"parameters": params}


@app.get("/problem_params/{problem_name}")
def get_problem_params(problem_name: str):
    problem_cls = problem_unabbreviated_directory.get(problem_name)
    if problem_cls is None:
        return {"parameters": []}

    params = []
    config_cls = getattr(problem_cls, "config_class", None)

    if config_cls is not None and hasattr(config_cls, "model_fields"):
        for name, field in config_cls.model_fields.items():
            params.append({
                "name": name,
                "default": field.default,
                "description": field.description or ""
            })
    else:
        try:
            instance = problem_cls()
            if hasattr(instance, "params"):
                for name, meta in instance.params.items():
                    params.append({
                        "name": name,
                        "default": meta.get("default") if isinstance(meta, dict) else None,
                        "description": meta.get("description") if isinstance(meta, dict) else ""
                    })
        except Exception:
            pass

    return {"parameters": params}

