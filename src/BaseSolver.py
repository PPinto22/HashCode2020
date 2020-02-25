import os

from Data import Data


class BaseSolver:
    INPUT_DIR = "../input"
    OUTPUT_DIR = "../output"

    def __init__(self, data_set):
        """
        :param data_set:  name of the input data set. E.g. a_example
        """
        self.data_set = os.path.splitext(data_set)[0]
        self.input_path = '{}/{}.txt'.format(self.INPUT_DIR, self.data_set)
        self.data = Data(self.input_path)
        self.solution = None

    def create_output_dir(self):
        if not os.path.exists(self.OUTPUT_DIR):
            os.makedirs(self.OUTPUT_DIR)

    def get_output_path(self, make_unique=False):
        def _get_output_path(counter=0):
            return '{}/{}{}.txt'.format(self.OUTPUT_DIR, self.data_set, counter if counter > 0 else "")

        for i in range(999):
            path = _get_output_path(i)
            if not (make_unique and os.path.exists(path)):
                return path
        raise FileExistsError

    def solve(self):
        # TODO: set self.solution
        pass

    def save(self):
        # TODO: write self.solution to self.output_path
        pass
