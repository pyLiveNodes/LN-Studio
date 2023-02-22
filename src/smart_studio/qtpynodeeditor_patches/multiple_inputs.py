#### Monkey patch qtpynodeeditor to allow for multiple input connections
# Patch aims to allow multiple inputs to a node, not implemented yet

import qtpynodeeditor
from qtpynodeeditor import exceptions
import uuid
from qtpynodeeditor.connection_geometry import ConnectionGeometry

from qtpynodeeditor import (PortType, Connection)


def new_init(self, port_a, port_b=None, *, style, converter=None):
    super(Connection, self).__init__()
    self._uid = str(uuid.uuid4())

    if port_a is None:
        raise ValueError('port_a is required')
    elif port_a is port_b:
        raise ValueError('Cannot connect a port to itself')

    if port_a.port_type == PortType.input:
        in_port = port_a
        out_port = port_b
    else:
        in_port = port_b
        out_port = port_a

    if in_port is not None and out_port is not None:
        if in_port.port_type == out_port.port_type:
            raise exceptions.PortsOfSameTypeError(
                'Cannot connect two ports of the same type')

    self._ports = {PortType.input: in_port, PortType.output: out_port}

    if in_port is not None:
        if in_port.connections:
            conn, = in_port.connections
            existing_in, existing_out = conn.ports
            if existing_in == in_port and existing_out == out_port:
                raise exceptions.PortsAlreadyConnectedError(
                    'Specified ports already connected')
            raise exceptions.MultipleInputConnectionError(
                f'Maximum one connection per input port '
                f'(existing: {conn})')

    if in_port and out_port:
        self._required_port = PortType.none
    elif in_port:
        self._required_port = PortType.output
    else:
        self._required_port = PortType.input

    self._last_hovered_node = None
    self._converter = converter
    self._style = style
    self._connection_geometry = ConnectionGeometry(style)
    self._graphics_object = None


qtpynodeeditor.Connection.__init__ = new_init

### End Patch
