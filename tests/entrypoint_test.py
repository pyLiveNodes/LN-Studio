import glob
from os.path import dirname, basename, isfile, join
from importlib.metadata import entry_points

import pytest


@pytest.fixture
def discovered_modules():
    exclude = ['__init__', 'utils']
    modules = glob.glob(join(dirname(__file__), '../src/livenodes_basic_nodes/', "*.py"))
    names = [basename(f)[:-3] for f in modules if isfile(f)]
    return [f for f in names if not f in exclude]

class TestProcessing():
    def test_modules_discoverable(self, discovered_modules):
        assert len(discovered_modules) > 0

    def test_all_declared(self, discovered_modules):
        livnodes_entrypoints = [x.name for x in entry_points()['livenodes.nodes']]

        assert set(livnodes_entrypoints) == set(discovered_modules)

    def test_loads_class(self):
        math_floor = [x.load() for x in entry_points()['livenodes.nodes'] if x.name == 'math_floor'][0]
        from livenodes_basic_nodes.math_floor import Math_floor
        assert math_floor == Math_floor

    def test_all_loadable(self):
        for x in entry_points()['livenodes.nodes']:
            x.load()




# if __name__ == "__main__":
#     TestProcessing().test_loads_class()
#     TestProcessing().test_all_loadable()
#     TestProcessing().test_all_loadable(discovered_modules())