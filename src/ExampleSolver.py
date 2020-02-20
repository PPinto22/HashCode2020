from BaseSolver import BaseSolver


class ExampleSolver(BaseSolver):
    def __init__(self, data_set):
        super().__init__(data_set)

    def solve(self):
        self.solution = [[0, 1, 2], [3, 4, 5]]

    def save(self):
        with open(self.get_output_path(), "w") as file:
            for row in self.solution:
                file.write(f"{' '.join(map(str, row))}\n")


if __name__ == '__main__':
    solver = ExampleSolver("a_example.in")
    solver.solve()
    solver.save()
    #solver.opt()
    #solver.save()
