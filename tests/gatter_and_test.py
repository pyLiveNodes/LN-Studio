import pytest
import multiprocessing as mp

from livenodes.node import Node, Location
from livenodes.sender import Sender

from livenodes_basic_nodes.gatter_and import Gatter_and


class Data(Sender):
    channels_in = []
    channels_out = ["Data"]

    def __init__(self, smaller_than = 5, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.smaller_than = smaller_than

    def _run(self):
        for ctr in range(10):
            self.info(ctr)
            self._emit_data(ctr < self.smaller_than, channel="Data")
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
    data_1 = Data(name="A", smaller_than=3, compute_on=Location.THREAD, block=True)
    data_2 = Data(name="B", smaller_than=5, compute_on=Location.THREAD, block=True)
    and_1 = Gatter_and(name="C", compute_on=Location.SAME)
    out_1 = Save(name="D", compute_on=Location.SAME)

    and_1.add_input(data_1, receiving_channel="Trigger 1")
    and_1.add_input(data_2, receiving_channel="Trigger 2")
    out_1.add_input(and_1, emitting_channel="Trigger")

    return data_1, data_2, and_1, out_1


# TODO: fix join=True in livenode repo, see #2
# class TestProcessing():

#     def test_calc(self, create_simple_graph):
#         data_1, data_2, and_1, out_1 = create_simple_graph

#         data_1.start(join=True)
#         data_1.stop()

#         assert out_1.get_state() == [True, True, True, False, False, False, False, False, False, False]
