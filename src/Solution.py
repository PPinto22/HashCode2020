class Solution:
    def __init__(self, libraries=None, books=None):
        # List of library IDs, ordered by signup day
        self.libraries = libraries if libraries is not None else []
        # List of book IDs per library {library_id: [book_id]}
        self.books = books if books is not None else {}
        self._i = 0  # Iterator index

    def add_library(self, library_id):
        self.libraries.append(library_id)
        self.books[library_id] = []

    def add_book(self, library_id, book_id):
        self.books[library_id].append(book_id)

    def save(self, file_path):
        with open(file_path, "w") as file:
            file.write("{}\n".format(len(self.libraries)))
            for library_id, library_books in self:
                file.write("{} {}\n".format(library_id, len(library_books)))
                file.write(f"{' '.join(map(str, [book_id for book_id in library_books]))}\n")

    # Get pair (library, library_books)
    def __getitem__(self, i):
        if i >= len(self):
            raise IndexError
        library = self.libraries[i]
        return library, self.books[library]

    def __next__(self):
        if self._i >= len(self.libraries):
            self._i = 0
            raise StopIteration
        item = self[self._i]
        self._i += 1
        return item

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.libraries)
