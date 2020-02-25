import random

from BaseSolver import BaseSolver

from scipy.optimize import rosen, differential_evolution, NonlinearConstraint
import numpy as np


class DiffEvolutionSolver(BaseSolver):
    def __init__(self, data_set):
        print(data_set)
        super().__init__(data_set)
        self.scanned_books = set()
        self.sorted_libraries = []

    def sort_libraries(self):
        self.sorted_libraries = sorted(self.data.libraries,
                                       key=lambda library: sum(book.score for book in library.books))

    def sort_books_in_libraries(self):
        for library in self.sorted_libraries:
            # FIXME: This is changing the set to a list...
            library.books = list(sorted(library.books, key=lambda book: book.score))

    @staticmethod
    def evaluate(solution, data):
        remaining_days = data.D
        score = 0
        all_scanned_books = set()
        for library in solution:
            remaining_days -= library.signup_days
            if remaining_days <= 0:
                break
            n_books_scanned = remaining_days * library.throughput
            books_scanned = set(library.books[:n_books_scanned])
            unique_books_scanned = books_scanned - all_scanned_books
            all_scanned_books.update(unique_books_scanned)
            score += sum([book.score for book in unique_books_scanned])
        return score

    @staticmethod
    def evaluate_individual(library_weights, data):
        solution = DiffEvolutionSolver.weights_to_library_list(library_weights, data)
        score = DiffEvolutionSolver.evaluate(solution, data)
        return -score

    def get_initial_solution(self):
        self.sort_libraries()
        self.sort_books_in_libraries()
        return self.sorted_libraries

    def generate_initial_pop(self, initial_solution, popsize, bound_list, std_list):
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

    @staticmethod
    def library_list_to_weights(library_list, data):
        weights = [0] * data.L
        for i, library in enumerate(library_list):
            weights[library.id_] = 1 - (i / len(library_list))
        return weights

    @staticmethod
    def weights_to_library_list(weights, data):
        weights_and_libraries = zip(weights, [data.libraries[i] for i in range(len(weights))])
        sorted_library_list = sorted(weights_and_libraries, reverse=True, key=lambda tuple_: tuple_[0])
        return [tuple_[1] for tuple_ in sorted_library_list]

    def solve(self):
        dim = self.data.L
        popsize = 50
        bounds = [(0, 1)] * dim

        initial_weights = self.library_list_to_weights(self.get_initial_solution(), self.data)
        initial_pop = self.generate_initial_pop(initial_weights, popsize, bounds, [1] * dim)

        result = differential_evolution(self.evaluate_individual, args=(self.data,), bounds=bounds, workers=1,
                                        mutation=1.2,
                                        recombination=0.8,
                                        disp=True,
                                        popsize=popsize,
                                        polish=False,
                                        init=initial_pop,
                                        maxiter=1000)
        self.solution = self.weights_to_library_list(result.x, self.data)

    def shuffle(self):
        solution = self.get_initial_solution()
        print("Initial score: {}".format(self.evaluate(solution, self.data)))
        max = 0
        best_solution = None
        for i in range(5000):
            random.shuffle(solution)
            score = self.evaluate(solution, self.data)
            if score > max:
                max = score
                best_solution = list(solution)
        self.solution = best_solution
        print("Best: {}".format(max))

    def save(self):
        with open(self.get_output_path(), "w") as file:
            file.write("{}\n".format(len(self.solution)))
            for library in self.solution:
                file.write("{} {}\n".format(library.id_, len(library.books)))
                file.write(f"{' '.join(map(str, [book.id_ for book in library.books]))}\n")


if __name__ == '__main__':
    data_sets = ["a_example", "b_read_on", "c_incunabula", "d_tough_choices", "e_so_many_books",
                 "f_libraries_of_the_world"]
    for data_set in data_sets:
        solver = DiffEvolutionSolver(data_set)
        solver.solve()
        solver.save()
