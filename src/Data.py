class Data:
    def __init__(self, input_file):
        self.B, self.L, self.D = None, None, None
        self.books = []
        self.libraries = []
        self.read_data(input_file)

    def read_data(self, input_file):
        with open(input_file, 'r') as file:
            self.B, self.L, self.D = [int(x) for x in file.readline().split()]
            self.books = [Book(id, int(score)) for id, score in enumerate(file.readline().split())]
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

    def get_total_book_score(self):
        return sum(book.score for book in self.books)
