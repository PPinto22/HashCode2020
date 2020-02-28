import numpy as np
from collections import deque
from queue import Queue
from scipy.stats import norm

from BaseSolver import BaseSolver
from Data import Library
from Solution import Solution


class Solver(BaseSolver):
    def __init__(self, data_set):
        super().__init__(data_set)
        self.book_occurrences = self.get_book_occurrences()  # Sets IDs of libraries in which each book exists
        self.book_availability_dist = NormalDistribution([len(libs) for book, libs in self.book_occurrences.items()])
        self.book_score_dist = NormalDistribution([book.score for book in self.data.books])
        self.library_signup_dist = NormalDistribution([library.signup_days for library in self.data.libraries])
        self.library_books_dist = NormalDistribution([len(library.books) for library in self.data.libraries])

    def evaluate(self, solution):
        remaining_days = self.data.D
        score = 0
        all_scanned_books_ids = set()
        for library_id, book_ids in solution:
            library = self.data.libraries[library_id]
            remaining_days -= library.signup_days
            if remaining_days <= 0:
                break
            max_books_scanned = remaining_days * library.throughput
            book_ids_set = set(book_ids[:max_books_scanned])
            unique_book_ids_set = book_ids_set - all_scanned_books_ids
            all_scanned_books_ids.update(unique_book_ids_set)
            score += sum([self.data.books[book_id].score for book_id in unique_book_ids_set])
        return score

    def get_book_occurrences(self):
        book_occurrences = {book.id_: set() for book in self.data.books}
        for library in self.data.libraries:
            for book in library.books:
                book_occurrences[book.id_].add(library.id_)
        return book_occurrences

    def solve(self):
        def add_library(library_id):
            signed_libraries[library_id] = unsigned_libraries[library_id]
            del unsigned_libraries[library_id]
            solution.add_library(library_id)

        def add_book(library_id, book_id):
            # Global book sets
            scanned_books.add(book_id)
            unscanned_books.remove(book_id)
            # Library book sets
            for other_library_id in self.book_occurrences[book_id]:
                library = signed_libraries[other_library_id] if other_library_id in signed_libraries else \
                    unsigned_libraries[other_library_id]
                library.add_book_scan(book_id)
            # Update solution
            solution.add_book(library_id, book_id)

        def evaluate_library(library):
            days_left = self.data.D - day
            days_left_pct = days_left / self.data.D
            max_books = library.get_max_books(days_left)
            total_book_evaluation = library.get_rough_book_evaluation(days_left)

            avg_book_evaluation = total_book_evaluation / max_books if max_books > 0 else 0
            used_days_pct = 1 - (library.get_wasted_days(days_left) / self.data.D)
            max_books_percentile = self.library_books_dist.percentile(max_books)
            signup_speed_percentile = 1 - (self.library_signup_dist.percentile(library.signup_days))

            # The scale evaluation scale doesn't matter; it doesn't have to be between [0, 1]
            return 0.5 * avg_book_evaluation + 0.2 * used_days_pct + \
                   0.2 * max_books_percentile + days_left_pct * signup_speed_percentile

        def evaluate_book(book_id, score_weight=0.5, rarity_weight=0.5):
            if book_id in book_evaluations:  # Return previously calculated evaluation
                return book_evaluations[book_id]
            book = self.data.books[book_id]
            book_occurrences = len(self.book_occurrences[book_id])
            score_percentile = self.book_score_dist.percentile(book.score)
            rarity_percentile = 1 - self.book_availability_dist.percentile(book_occurrences)
            return (score_weight * score_percentile + rarity_weight * rarity_percentile) / 2

        def update_library_queue():
            library_queue.clear()
            for library in sorted(unsigned_libraries.values(), key=evaluate_library, reverse=True):
                library_queue.append(library)

        solution = Solution()  # Workable solution
        # Book_id sets
        scanned_books = set()  # Set of IDs all of scanned books
        unscanned_books = set([book.id_ for book in self.data.books])  # Set of IDs of all books not scanned
        book_evaluations = {}  # This is needed by the evaluate_book function
        book_evaluations = {book.id_: evaluate_book(book.id_) for book in self.data.books}  # Evaluate all books
        # Library collections
        signed_libraries = {}  # {library_id: MutableLibrary} of all libraries that have been signed up
        unsigned_libraries = {library.id_: MutableLibrary(library, scanned_books, evaluate_book) for library in
                              self.data.libraries}  # All libraries that have not been signed up
        signup_process = None  # Instance of SignupProcess: the library that is currently being signed up
        library_queue = deque(maxlen=self.data.L)
        queue_update_frequency = max(round(self.data.L / 100), 1)

        for day in range(self.data.D):
            # If 1. there is no library being signed up, 2. it's not the last day, and 3. there are available libraries,
            # choose a library to sign up
            if not signup_process and (day + 1) < self.data.D:
                if len(signed_libraries) % queue_update_frequency == 0:
                    update_library_queue()
                if library_queue:
                    new_library = library_queue.popleft()
                    signup_process = SignupProcess(new_library, day)
                    print("[DEBUG | Day {}] Signing up library {} ({} days)".format(day, new_library.id_,
                                                                                   new_library.signup_days))

            # If signup process has just finished, add library to solution
            if signup_process and signup_process.is_finished(day):
                signup_process.library.build_book_queue()
                add_library(signup_process.library.id_)
                signup_process = None

            # Pick books for each library that has already been signed up
            for library_id in solution.libraries:
                library = signed_libraries[library_id]
                for _ in range(library.throughput):
                    # Pick book to scan
                    book_id = library.get_next_book()
                    if book_id is not None:
                        add_book(library.id_, book_id)

        self.solution = solution

    def save(self):
        self.solution.save(self.get_output_path())


class SignupProcess:
    def __init__(self, library, start_day):
        self.library = library
        self.start_day = start_day

    def is_finished(self, current_day):
        return current_day - self.start_day >= self.library.signup_days


class NormalDistribution:
    def __init__(self, values):
        self.mean = np.mean(values)
        self.std = np.std(values)

    def percentile(self, value):
        if self.std == 0:
            return 0.5
        return norm.cdf(value, self.mean, self.std)


class MutableLibrary(Library):
    def __init__(self, library, all_scanned_books, book_evaluator):
        super().__init__(library.id_, library.books, library.signup_days, library.throughput)
        self.all_scanned_books = all_scanned_books  # ID of books scanned in ALL the libraries
        self.book_evaluator = book_evaluator  # A function that receives the book_id and returns a score
        self.unscanned_books = set(book.id_ for book in self.books)  # Set of IDs of books not scanned
        self.max_score = sum(map(book_evaluator, self.unscanned_books))  # The max score if all books were scanned
        self.book_queue = None

    def build_book_queue(self):
        self.book_queue = Queue(maxsize=len(self.unscanned_books))
        for book_id in sorted(self.unscanned_books, key=self.book_evaluator, reverse=True):
            self.book_queue.put(book_id)

    def get_next_book(self):
        while len(self.book_queue.queue) > 0:
            book_id = self.book_queue.get()
            if book_id in self.all_scanned_books:
                # The book may already have been scanned because
                # the queue is not update every time a new book is scanned
                continue
            return book_id
        return None

    # Maximum number of books this library could scan depending on how many days there are left
    def get_max_books(self, days_left):
        active_days = self.get_active_days()
        actual_days = min(active_days, days_left)
        return self.throughput * actual_days

    # Rough evaluation of the books in the library. (self.max_score in proportion to the number of days left)
    def get_rough_book_evaluation(self, days_left=np.Inf):
        if len(self.unscanned_books) == 0:
            return 0
        max_books = self.get_max_books(days_left)
        return self.max_score * max_books / len(self.unscanned_books)

    # How many days would there be without any books to scan
    def get_wasted_days(self, days_left):
        active_days = self.get_active_days()
        return max(active_days - days_left, 0)

    # On many days it would take to scan every book not yet scanned
    def get_active_days(self):
        return round(len(self.unscanned_books) / self.throughput)

    def add_book_scan(self, book_id):
        self.unscanned_books.remove(book_id)
        self.max_score -= self.book_evaluator(book_id)


if __name__ == '__main__':
    data_sets = ["a_example", "b_read_on", "c_incunabula", "d_tough_choices", "e_so_many_books",
                 "f_libraries_of_the_world"]
    for data_set in [data_sets[5]]:  # FIXME: Testing
        solver = Solver(data_set)
        print(solver.data_set)
        solver.solve()
        print(solver.evaluate(solver.solution))
        solver.save()
