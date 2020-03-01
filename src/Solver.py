import math
from collections import deque
from queue import Queue

import numpy as np
from scipy.optimize import shgo
from scipy.stats import norm

from BaseSolver import BaseSolver
from Data import Library
from Solution import Solution


class Parameters:
    BOOK_PARAMETERS = ["book_score", "book_rarity"]
    LIBRARY_PARAMETERS = ["library_book_eval", "library_book_qty", "library_active_days", "library_signup_speed"]
    DIMENSIONALITY = len(BOOK_PARAMETERS) + len(LIBRARY_PARAMETERS)

    def __init__(self, book_score=0.6, book_rarity=0.4, library_book_eval=0.3, library_book_qty=0.4,
                 library_active_days=0.1, library_signup_speed=0.2):
        self.book_score = book_score
        self.book_rarity = book_rarity
        self.library_book_eval = library_book_eval
        self.library_book_qty = library_book_qty
        self.library_active_days = library_active_days
        self.library_signup_speed = library_signup_speed
        self.normalize()

    def normalize(self):
        for param_set in [self.BOOK_PARAMETERS, self.LIBRARY_PARAMETERS]:
            set_sum = sum(getattr(self, param) for param in param_set)
            if set_sum == 0:
                set_sum = 1
            for param in param_set:
                setattr(self, param, getattr(self, param) / set_sum)

    def list(self):
        return [getattr(self, book_param) for book_param in self.BOOK_PARAMETERS] + \
               [getattr(self, library_param) for library_param in self.LIBRARY_PARAMETERS]


class Solver(BaseSolver):
    def __init__(self, data_set, params=None, library_queue_updates=20, debug=False):
        super().__init__(data_set)
        self.debug = debug
        self.params = params if params is not None else Parameters()
        # How many times to update the library queue as the solver progresses
        self.queue_update_frequency = math.ceil(self.data.L / library_queue_updates)
        # Data stats/distributions
        self.book_occurrences = self.get_book_occurrences()  # Sets of IDs of libraries in which each book exists
        self.book_availability_dist = NormalDistribution([len(libs) for book, libs in self.book_occurrences.items()])
        self.book_score_dist = NormalDistribution([book.score for book in self.data.books])
        self.library_signup_dist = NormalDistribution([library.signup_days for library in self.data.libraries])
        self.library_books_dist = NormalDistribution([len(library.books) for library in self.data.libraries])
        self.library_throughput_dist = NormalDistribution([library.throughput for library in self.data.libraries])

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
            active_days_pct = library.get_active_days(days_left) / days_left
            max_books_percentile = self.library_books_dist.percentile(max_books)
            signup_speed_percentile = 1 - (self.library_signup_dist.percentile(library.signup_days))

            # The scale doesn't matter; no need to normalize between [0, 1]
            return self.params.library_book_eval * avg_book_evaluation + \
                   self.params.library_book_qty * max_books_percentile + \
                   self.params.library_active_days * active_days_pct + \
                   self.params.library_signup_speed * signup_speed_percentile

        def evaluate_book(book_id):
            if book_id in book_evaluations:  # Cache
                return book_evaluations[book_id]
            book = self.data.books[book_id]
            book_occurrences = len(self.book_occurrences[book_id])
            score_percentile = self.book_score_dist.percentile(book.score)
            rarity_percentile = 1 - self.book_availability_dist.percentile(book_occurrences)
            return (self.params.book_score * score_percentile + self.params.book_rarity * rarity_percentile) / 2

        def update_library_queue():
            library_queue.clear()
            for library in sorted(unsigned_libraries.values(), key=evaluate_library, reverse=True):
                library_queue.append(library)

        def next_library():
            while library_queue:
                library = library_queue.popleft()
                if not library.unscanned_books:  # Skip if there are no books to scan
                    continue
                return library
            return None

        solution = Solution()  # Workable solution
        # Books
        scanned_books = set()  # Set of IDs all of scanned books
        unscanned_books = set([book.id_ for book in self.data.books])  # Set of IDs of all books not scanned
        book_evaluations = {}  # This is needed by the evaluate_book function
        book_evaluations = {book.id_: evaluate_book(book.id_) for book in self.data.books}  # Evaluate all books
        # Libraries
        signed_libraries = {}  # {library_id: MutableLibrary} of all libraries that have been signed up
        unsigned_libraries = {library.id_: MutableLibrary(library, evaluate_book) for library in
                              self.data.libraries}  # All libraries that have not been signed up
        signup_process = None  # Instance of SignupProcess: the library that is currently being signed up
        library_queue = deque(maxlen=self.data.L)

        for day in range(self.data.D):
            days_left = self.data.D - day  # How many days remain until the end, including the current day
            # If signup process has just finished, add library to solution
            # and immediately scan all books from it until the last day or until it runs out of books
            if signup_process and signup_process.is_finished(day):
                new_library = signup_process.library
                new_library.build_book_queue()
                add_library(new_library.id_)
                signup_process = None
                # Scan all books in the library
                for book_id in new_library.next_books(days_left):
                    add_book(new_library.id_, book_id)
                # Remove the library from book_occurrences
                # for book_id in new_library.unscanned_books:
                #     self.book_occurrences[book_id].remove(new_library.id_)

            # Choose a library to sign up if:
            # 1. there is no library being signed up, 2. it's not the last day, and 3. there are available libraries,
            if not signup_process and days_left > 1:
                if len(signed_libraries) % self.queue_update_frequency == 0:
                    update_library_queue()
                new_library = next_library()
                if new_library:
                    signup_process = SignupProcess(new_library, day)
                    self.debug and print("[DEBUG | Day {}] Signing up library {} ({} days)".format(day, new_library.id_,
                                                                                                   new_library.signup_days))

        self.solution, self.score = solution, self.evaluate(solution)

    # Optimize parameters
    def optimize(self):
        def eval_(param_list):
            self.params = Parameters(*param_list)
            self.solve()
            return -self.score

        def save(param_list, score):
            with open(self.get_output_path().replace('.txt', '_params.txt'), 'w') as file:
                file.write(f"{' '.join(map(lambda p: str(p), param_list))}\n")
                file.write("{}\n".format(score))

        bounds = [(0, 1)] * Parameters.DIMENSIONALITY
        # This doesn't work well. TODO: Try another optimizer
        result = shgo(eval_, bounds, options={
            'disp': True,
            'maxtime': 7200  # seconds
        })
        param_list = Parameters(*result.x).list()
        score = -result.fun
        save(param_list, score)
        return param_list, score

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
    def __init__(self, library, book_evaluator):
        super().__init__(library.id_, library.books, library.signup_days, library.throughput)
        self.book_evaluator = book_evaluator  # A function that receives the book_id and returns a score
        self.unscanned_books = set(book.id_ for book in self.books)  # Set of IDs of books not scanned
        self.max_score = sum(map(book_evaluator, self.unscanned_books))  # The max score if all books were scanned
        self.book_queue = None

    def build_book_queue(self):
        self.book_queue = Queue(maxsize=len(self.unscanned_books))
        for book_id in sorted(self.unscanned_books, key=self.book_evaluator, reverse=True):
            self.book_queue.put(book_id)

    # Pop, from the book queue, the first book that has not been scanned
    def next_book(self):
        while len(self.book_queue.queue) > 0:
            book_id = self.book_queue.get()
            if book_id not in self.unscanned_books:
                # The book may already have been scanned because
                # the QUEUE is not update every time a new book is scanned (but the set is)
                continue
            return book_id
        return None

    # Pop, from the book queue, the maximum number of books that can be scanned in N days
    def next_books(self, days):
        max_books = self.get_max_books(days)
        book_list = []
        for _ in range(max_books):
            next_book = self.next_book()
            if next_book is None:
                break
            book_list.append(next_book)
        return book_list

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
        return max(days_left - active_days, 0)

    # On many days it would take to scan every book not yet scanned
    def get_active_days(self, days_left=np.Inf):
        max_days = math.ceil(len(self.unscanned_books) / self.throughput)
        return min(max_days, days_left)

    def add_book_scan(self, book_id):
        self.unscanned_books.remove(book_id)
        self.max_score -= self.book_evaluator(book_id)


if __name__ == '__main__':
    parameters = [
        # book_score, book_rarity, library_book_eval, library_book_qty, library_active_days, library_signup_speed
        Parameters(),  # A
        Parameters(0.5, 0.5, 0, 0, 0, 1),  # B - only the signup time changes
        Parameters(0.7, 0.3, 0.1, 0.3, 0.3, 0.3),  # C
        Parameters(0, 1, 0, 1, 0, 0),  # D - constant book score, signup time and throughput
        Parameters(0.9, 0.1, 0.28, 0.1, 0.005, 0.25),  # E - way more books than libraries; rarity is not too important
        Parameters(0.9, 0.1, 0.4, 0.1, 0, 0.5)  # F
    ]
    data_sets = ["a_example", "b_read_on", "c_incunabula", "d_tough_choices", "e_so_many_books",
                 "f_libraries_of_the_world"]
    for data_set, parameters in zip(data_sets, parameters):
        solver = Solver(data_set, parameters, library_queue_updates=500, debug=True)
        print(solver.data_set)
        solver.solve()
        print(solver.score)
        solver.save()
