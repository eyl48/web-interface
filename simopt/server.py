from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from simopt.directory import problem_unabbreviated_directory, solver_unabbreviated_directory

# The FastAPI instance.
app = FastAPI(title="SimOpt API")

# Configure CORS (Cross-Origin Resource Sharing)
# This allows your Svelte frontend (running on a different port)
# to make requests to this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/problems")
def get_problems():
    """Returns a list of all available problem names."""
    return {"problems": list(problem_unabbreviated_directory.keys())}

@app.get("/solvers")
def get_solvers():
    """Returns a list of all available solver names."""
    return {"solvers": list(solver_unabbreviated_directory.keys())}