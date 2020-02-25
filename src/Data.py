class Data:
    def __init__(self, input_file):
        self.B, self.L, self.D = None, None, None
        self.books = []
        self.libraries = []
        self.read_data(input_file)

    def read_data(self, input_file):
        with open(input_file, 'r') as file:
            self.B, self.L, self.D = [int(x) for x in file.readline().split()]
            self.books = [Book(id_, int(score)) for id_, score in enumerate(file.readline().split())]
            for i in range(self.L):
                book_qty, signup_days, throughput = map(int, file.readline().split())
                book_ids = list(map(int, file.readline().split()))
                books = [self.books[i] for i in book_ids]
                self.libraries.append(Library(i, books, signup_days, throughput))


class Entity:
    def __init__(self, id_):
        self.id_ = id_

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id_ == other.id_

    def __ne__(self, other):
        return not isinstance(other, self.__class__) or self.id_ != other.id_

    def __hash__(self):
        return self.id_


class Book(Entity):
    def __init__(self, id_, score):
        super().__init__(id_)
        self.score = score


class Library(Entity):
    def __init__(self, id_, books, signup_days, throughput):
        super().__init__(id_)
        self.books = set(books)
        self.book_qty = len(books)
        self.signup_days = signup_days
        self.throughput = throughput
