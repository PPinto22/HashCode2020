class Data:
    def __init__(self, input_file):
        self.B, self.L, self.D = None, None, None
        self.books = []
        self.books_scores = []
        self.libraries = []
        self.read_data(input_file)

    def read_data(self, input_file):
        with open(input_file, 'r') as file:
            self.B, self.L, self.D = [int(x) for x in file.readline().split()]
            self.books_scores = list(map(int, file.readline().split()))
            self.books = [Book(id, score) for id, score in enumerate(self.books_scores)]
            for i in range(self.L):
                book_qty, signup_days, throughput = map(int, file.readline().split())
                book_ids = list(map(int, file.readline().split()))
                books = [self.books[i] for i in book_ids]
                self.libraries.append(Library(i, books, signup_days, throughput))


class Book:
    def __init__(self, id, score):
        self.id = id
        self.score = score


class Library:
    def __init__(self, id, books, signup_days, throughput):
        self.id = id
        self.books = books
        self.book_qty = len(books)
        self.signup_days = signup_days
        self.throughput = throughput
        self.avg_book_score = None
        self.uniqueness_factor = None
        self.uniqueness_factor_average_score = None

    def get_total_book_score(self):
        return sum(book.score for book in self.books)
