from BaseSolver import BaseSolver
from scipy.optimize import shgo



class Solver(BaseSolver):
    def __init__(self, data_set):
        print(data_set)
        super().__init__(data_set)
        self.scanned_books = set()
        self.sorted_libraries = []

    def sort_libraries(self):
        self.sorted_libraries = sorted(self.data.libraries, key=lambda library: library.get_total_book_score())

    def sort_books_in_libraries(self, libraries):
        for library in libraries:
            library.books.sort(key=lambda book: book.score)


    def build_solution(self):
        self.solution = [library.id for library in self.data.libraries]

    def solve(self):
        #self.sort_libraries()
        self.sort_books_in_libraries(self.sorted_libraries)
        #self.solution = self.sorted_libraries

    def save(self):
        with open(self.get_output_path(), "w") as file:
            file.write("{}\n".format(len(self.solution)))
            for library in self.solution:
                file.write("{} {}\n".format(library.id, len(library.books)))
                file.write(f"{' '.join(map(str, [book.id for book in library.books]))}\n")

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
    
    return -score

def sort_libraries_by_ranks(ranks, data, evalFuncs):

    def applyFuncs(lib):
        total_score = 0
        for i, f in enumerate(evalFuncs):
            total_score += (ranks[i]*f(lib, data))
        return total_score
        
    sorted_libraries = sorted(data.libraries, key=applyFuncs)

    return sorted_libraries



def f(ranks, data, evalFuncs):


    return evaluate(sort_libraries_by_ranks(ranks, data, evalFuncs), data)


if __name__ == '__main__':
    data_sets = ["a_example", "b_read_on", "c_incunabula", "d_tough_choices", "e_so_many_books",
                 "f_libraries_of_the_world"]
    for data_set in data_sets:
        solver = Solver(data_set)

        solver.solve()

        def totalBooks(library, data):
            return (data.D - library.signup_days) * library.throughput
        
        def averageBookScore(library, data):
            if library.avg_book_score == None:
                library.avg_book_score = sum([book.score for book in library.books])/len(library.books)
            return library.avg_book_score
        
        def signup(library, data):
            return library.signup_days

        
        def uniqueness_factor(library, data):
            
                
            if library.uniqueness_factor == None:
                allBooks = set()

                for l in solver.data.libraries:
                    if l == library:
                        continue 
                    allBooks.update(l.books)

                library.uniqueness_factor = len(set(library.books) - allBooks)
            return library.uniqueness_factor
        
    

        evalFuncs = []
        evalFuncs.append(totalBooks)
        evalFuncs.append(averageBookScore)
        evalFuncs.append(signup)
        evalFuncs.append(uniqueness_factor)

        sol = shgo(f, [(0.0, 1.0)] * len(evalFuncs), args = (solver.data, evalFuncs, ), iters = 1)
        print(sol)

        solver.solution = sort_libraries_by_ranks(sol.x, solver.data, evalFuncs)


        #print(solver.evaluate(solver.solution))
        solver.save()
