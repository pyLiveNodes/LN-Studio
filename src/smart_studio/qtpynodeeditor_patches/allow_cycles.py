import typing
from typing import Optional
import qtpynodeeditor

from qtpynodeeditor.exceptions import (ConnectionDataTypeFailure,
                         ConnectionPointFailure, ConnectionPortNotEmptyFailure,
                         ConnectionRequiresPortFailure, ConnectionSelfFailure)
from qtpynodeeditor.port import PortType, opposite_port
from qtpynodeeditor.type_converter import TypeConverter

if typing.TYPE_CHECKING:
    from qtpynodeeditor.port import Port  # noqa

#### Monkey Patch cyclic connections
# Patches chance to conenct nodes cyclically, if livenodes does allow it


def can_connect(self) -> tuple['Port', Optional[TypeConverter]]:
        """
        Can connect when following conditions are met:
            1) Connection 'requires' a port - i.e., is missing either a start
               node or an end node
            2) Connection's vacant end is above the node port in the user
               interface
            3) Node port is vacant
            4) Connection does not introduce a cycle in the graph
            5) Connection type equals node port type, or there is a registered
               type conversion that can translate between the two

        Parameters
        ----------

        Returns
        -------
        port : Port
            The port to be connected.

        converter : TypeConverter
            The data type converter to use.

        Raises
        ------
        NodeConnectionFailure
        ConnectionDataTypeFailure
            If port data types are not compatible
        """
        # 1) Connection requires a port
        required_port = self.connection_required_port
        if required_port == PortType.none:
            raise ConnectionRequiresPortFailure('Connection requires a port')
        elif required_port not in (PortType.input, PortType.output):
            raise ValueError(f'Invalid port specified {required_port}')

        # 1.5) Forbid connecting the node to itself
        node = self.connection_node
        if node == self._node:
            raise ConnectionSelfFailure(f'Cannot connect {node} to itself')

        # 2) connection point is on top of the node port
        connection_point = self.connection_end_scene_position(required_port)
        port = self.node_port_under_scene_point(required_port,
                                                connection_point)
        if not port:
            raise ConnectionPointFailure(
                f'Connection point {connection_point} is not on node {node}')

        # 3) Node port is vacant
        if not port.can_connect:
            raise ConnectionPortNotEmptyFailure(
                f'Port {required_port} {port} cannot connect'
            )

        # 4) Cycle check
        # if self.creates_cycle:
        #     raise ConnectionCycleFailure(
        #         f'Connecting {self._node} and {node} would introduce a '
        #         f'cycle in the graph'
        #     )

        # 5) Connection type equals node port type, or there is a registered
        #    type conversion that can translate between the two
        connection_data_type = self._connection.data_type(opposite_port(required_port))

        candidate_node_data_type = port.data_type
        if connection_data_type.id == candidate_node_data_type.id:
            return port, None

        registry = self._scene.registry
        if required_port == PortType.input:
            converter = registry.get_type_converter(connection_data_type,
                                                    candidate_node_data_type)
        else:
            converter = registry.get_type_converter(candidate_node_data_type,
                                                    connection_data_type)
        if not converter:
            raise ConnectionDataTypeFailure(
                f'{connection_data_type} and {candidate_node_data_type} are not compatible'
            )

        return port, converter


qtpynodeeditor.node_connection_interaction.NodeConnectionInteraction.can_connect = can_connect
print('Patched cycles')
### End patch