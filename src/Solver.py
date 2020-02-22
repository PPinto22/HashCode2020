from BaseSolver import BaseSolver


class Solver(BaseSolver):
    def __init__(self, data_set):
        super().__init__(data_set)
        self.scanned_books = set()
        self.sorted_libraries = []

    def sort_libraries(self):
        self.sorted_libraries = sorted(self.data.libraries, key=lambda library: library.get_total_book_score())

    def sort_books_in_libraries(self, libraries):
        for library in libraries:
            library.books.sort(key=lambda book: book.score)

    def evaluate(self, solution):
        remaining_days = self.data.D
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

    def build_solution(self):
        self.solution = [library.id for library in self.data.libraries]

    def solve(self):
        self.sort_libraries()
        self.sort_books_in_libraries(self.sorted_libraries)
        self.solution = self.sorted_libraries

    def save(self):
        with open(self.get_output_path(), "w") as file:
            file.write("{}\n".format(len(self.solution)))
            for library in self.solution:
                file.write("{} {}\n".format(library.id, len(library.books)))
                file.write(f"{' '.join(map(str, [book.id for book in library.books]))}\n")


if __name__ == '__main__':
    data_sets = ["a_example", "b_read_on", "c_incunabula", "d_tough_choices", "e_so_many_books",
                 "f_libraries_of_the_world"]
    for data_set in [data_sets[0]]:
        solver = Solver(data_set)
        print(solver.data_set)
        solver.solve()
        print(solver.evaluate(solver.solution))
        solver.save()
