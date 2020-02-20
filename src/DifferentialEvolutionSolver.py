from BaseSolver import BaseSolver

from scipy.optimize import rosen, differential_evolution, NonlinearConstraint
import numpy as np


def dummy_evaluation(array):
    return sum(1 - x for x in array)


def generate_initial_pop(initial_solution, popsize, bound_list, std_list):
    def bound(value, bounds):
        return max(bounds[0], min(bounds[1], value))

    def deviate(n, bounds, std):
        return bound(np.random.normal(n, std), bounds)

    pop = [initial_solution]
    for i in range(popsize):
        solution = [deviate(value, bounds, std) for value, bounds, std in
                    zip(initial_solution, bound_list, std_list)]
        pop.append(solution)
    return pop


class DifferentialEvolutionSolver(BaseSolver):
    def __init__(self, data_set):
        super().__init__(data_set)

    def solve(self):
        dim = 3
        popsize = 15
        bounds = [(0, 2)] * dim
        # Sum of the first 2 numbers < 0.5
        constraint1 = NonlinearConstraint(lambda solution: sum(solution[0:2]), -np.inf, 0.5)
        constraint2 = NonlinearConstraint(lambda solution: solution[2], 1.2, 1.2)

        initial_solution = [0.1, 0.2, 0.3]
        initial_pop = generate_initial_pop(initial_solution, popsize, bounds, [1] * dim)

        result = differential_evolution(dummy_evaluation, bounds, workers=4, disp=True, popsize=popsize,
                                        init=initial_pop, constraints=(constraint1, constraint2))
        print(result)


if __name__ == '__main__':
    solver = DifferentialEvolutionSolver('')
    solver.solve()
