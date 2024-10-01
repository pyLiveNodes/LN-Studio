#### Monkey Patch auto layouts
# Patches more options for auto layouts

import qtpynodeeditor.flow_scene


def auto_arrange(self,
                 layout='planar_layout',
                 scale=700,
                 align='horizontal',
                 **kwargs):
    '''
    Automatically arrange nodes with networkx, if available
    Raises
    ------
    ImportError
        If networkx is unavailable
    '''
    import networkx
    dig = self.to_digraph()

    try:
        if hasattr(networkx.layout, layout):
            layout_func = getattr(networkx.layout, layout)
        else:
            layout_func = getattr(networkx.nx_agraph, layout)
    except KeyError:
        raise ValueError('Unknown layout type {}'.format(layout)) from None

    layout = layout_func(dig, **kwargs)
    for node, pos in layout.items():
        pos_x, pos_y = pos
        node.position = (pos_x * scale, pos_y * scale)

qtpynodeeditor.flow_scene.FlowScene.auto_arrange = auto_arrange
print('Patched Auto Layouts')
### End patch
