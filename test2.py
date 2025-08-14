from simopt.directory import load_solvers
from simopt.experiment_base import (
    PlotType,
    ProblemSolver,
    plot_progress_curves,
    post_normalize,
)


def main():
    solvers = load_solvers()

    for solver in solvers:
        experiment = ProblemSolver(solver, "MM1-1")
        experiment.run(n_macroreps=10)
        experiment.post_replicate(n_postreps=10)
        post_normalize(experiments=[experiment], n_postreps_init_opt=10)

        experiment.log_experiment_results()
        plot_progress_curves(
            experiments=[experiment],
            plot_type=PlotType.MEAN,
            normalize=False,
        )


if __name__ == "__main__":
    main()
