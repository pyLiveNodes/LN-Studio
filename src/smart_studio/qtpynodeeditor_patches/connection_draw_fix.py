
#### Monkey Patch connection drawing
# Patches wrong type, orig: QPoint, correct: QPointF

from qtpy.QtCore import QSize, Qt, QPointF
from qtpy.QtGui import QIcon, QPen

from qtpynodeeditor.connection_geometry import ConnectionGeometry
from qtpynodeeditor.enums import PortType
import qtpynodeeditor.connection_painter


def draw_normal_line(painter, connection, style):
    if connection.requires_port:
        return

    # colors
    normal_color_out = style.get_normal_color()
    normal_color_in = normal_color_out

    selected_color = style.selected_color

    gradient_color = False
    if style.use_data_defined_colors:
        data_type_out = connection.data_type(PortType.output)
        data_type_in = connection.data_type(PortType.input)

        gradient_color = data_type_out.id != data_type_in.id

        normal_color_out = style.get_normal_color(data_type_out.id)
        normal_color_in = style.get_normal_color(data_type_in.id)
        selected_color = normal_color_out.darker(200)

    # geometry
    geom = connection.geometry
    line_width = style.line_width

    # draw normal line
    p = QPen()
    p.setWidth(line_width)

    graphics_object = connection.graphics_object
    selected = graphics_object.isSelected()

    cubic = qtpynodeeditor.connection_painter.cubic_path(geom)
    if gradient_color:
        painter.setBrush(Qt.NoBrush)

        c = normal_color_out
        if selected:
            c = c.darker(200)

        p.setColor(c)
        painter.setPen(p)

        segments = 60

        for i in range(segments):
            ratio_prev = float(i) / segments
            ratio = float(i + 1) / segments

            if i == segments / 2:
                c = normal_color_in
                if selected:
                    c = c.darker(200)

                p.setColor(c)
                painter.setPen(p)

            painter.drawLine(cubic.pointAtPercent(ratio_prev),
                             cubic.pointAtPercent(ratio))

        icon = QIcon(":convert.png")

        pixmap = icon.pixmap(QSize(22, 22))
        painter.drawPixmap(
            cubic.pointAtPercent(0.50) - QPointF(pixmap.width() / 2,
                                                 pixmap.height() / 2), pixmap)
    else:
        p.setColor(normal_color_out)

        if selected:
            p.setColor(selected_color)

        painter.setPen(p)
        painter.setBrush(Qt.NoBrush)

        painter.drawPath(cubic)


qtpynodeeditor.connection_painter.draw_normal_line = draw_normal_line

### End patch