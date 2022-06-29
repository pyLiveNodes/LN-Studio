import pytest
import multiprocessing as mp

from livenodes.node import Node, Location
from livenodes.sender import Sender

from livenodes_basic_nodes.math_floor import Math_floor


class Data(Sender):
    channels_in = []
    channels_out = ["Data"]

    def _run(self):
        for ctr in range(10):
            self.info(ctr)
            self._emit_data(ctr / 5.0, channel="Data")
            yield ctr < 9

class Save(Node):
    channels_in = ["Data"]
    channels_out = []

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.out = mp.SimpleQueue()

    def process(self, data, **kwargs):
        self.out.put(data)

    def get_state(self):
        res = []
        while not self.out.empty():
            res.append(self.out.get())
        return res


# Arrange
@pytest.fixture
def create_simple_graph():
    data_1 = Data(name="A", compute_on=Location.SAME, block=True)
    floor_1 = Math_floor(name="C", compute_on=Location.SAME)
    out_1 = Save(name="D", compute_on=Location.SAME)

    floor_1.add_input(data_1)
    out_1.add_input(floor_1)

    return data_1, floor_1, out_1


class TestProcessing():

    def test_floor(self, create_simple_graph):
        data_1, floor_1, out_1 = create_simple_graph

        data_1.start()
        data_1.stop()

        assert out_1.get_state() == [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
