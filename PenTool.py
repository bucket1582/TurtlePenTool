import turtle as t
from typing import Optional, Final
from time import time

from clickableObject import ClickableObject
from curve2D import *

pen: Optional[t.Turtle] = None
canvas: Optional[t.Canvas] = None
clicked_time: float = 0


class HandlerAnchor(ClickableObject):
    # Constants
    RADIUS: Final[int] = 5

    # Class fields
    _clicked_handler = None

    # Private fields
    _x: int = 0
    _y: int = 0
    _anchor = None
    is_highlighted: bool = False

    def __init__(self, x: int, y: int, anchor):
        self._x = x
        self._y = y
        self._anchor = anchor
        self.is_highlighted = False

    @classmethod
    def handle_click(cls, x: float, y: float) -> bool:
        cls._clicked_handler = None
        anc = Anchor.get_focused_anchor()
        if anc is None:
            return False

        for handler in anc.get_handlers():
            if handler.is_clicked(x, y):
                cls._clicked_handler = handler
                return True

        return False

    def is_clicked(self, x: float, y: float) -> bool:
        global_x, global_y = self.get_pos()
        # Box collider
        return x - HandlerAnchor.RADIUS < global_x < x + HandlerAnchor.RADIUS and \
               y - HandlerAnchor.RADIUS < global_y < y + HandlerAnchor.RADIUS

    def draw(self):
        global pen
        self.is_highlighted = True

        anc = self._anchor
        anc_x, anc_y = anc.get_pos()
        global_x, global_y = self.get_pos()

        # Goto the focused anchor's position
        pen.pu()
        pen.goto(anc_x, anc_y)

        # Un-draw handler
        pen.pd()
        pen.goto(global_x, global_y)
        pen.dot(HandlerAnchor.RADIUS + 3, "#000000")
        pen.dot(HandlerAnchor.RADIUS, "#FFFFFF")

        # Reset settings
        pen.pu()
        pen.goto(anc_x, anc_y)
        pen.color("#000000")

    def un_draw(self):
        global pen
        self.is_highlighted = False

        anc = self._anchor
        anc_x, anc_y = anc.get_pos()
        global_x, global_y = self.get_pos()

        # Goto the focused anchor's position
        pen.pu()
        pen.goto(anc_x, anc_y)

        # Un-draw handler
        pen.pd()
        pen.pencolor("#FFFFFF")
        pen.goto(global_x, global_y)
        pen.dot(HandlerAnchor.RADIUS + 3, "#FFFFFF")

        # Reset settings
        pen.pu()
        pen.goto(anc_x, anc_y)
        pen.color("#000000")

    def get_local_pos(self) -> tuple[int, int]:
        return self._x, self._y

    def get_pos(self) -> tuple[int, int]:
        x, y = self._anchor.get_pos()
        return x + self._x, y + self._y

    def move(self, x: int, y: int):
        global pen
        anc_x, anc_y = self._anchor.get_pos()

        # Remove handler
        self.un_draw()

        # Update lines
        # noinspection PyProtectedMember
        for connected_anchor, connection in self._anchor._connected_anchors_and_lines.items():
            if connection.handler_s == self:
                connection.update_handler((x - anc_x, y - anc_y), connection.handler_e.get_local_pos())
                continue

            if connection.handler_e == self:
                connection.update_handler(connection.handler_s.get_local_pos(), (x - anc_x, y - anc_y))
                continue

        # Update position
        self._x, self._y = x - anc_x, y - anc_y

        # Draw
        self.draw()

        self._anchor._draw()
        pen.pu()

    @classmethod
    def get_clicked_handler(cls):
        return cls._clicked_handler

    def set_default(self, x: int, y: int):
        self._x = x
        self._x = y


# noinspection PyProtectedMember
class Anchor(ClickableObject):
    # Constants
    RADIUS: Final[int] = 5
    HANDLER_RADIUS: Final[int] = 3

    # Class fields
    _anchors: list = []
    _focused_anchor = None

    # Private fields
    _x: int = 0
    _y: int = 0
    _highlighted: bool = False
    _handler_on: bool = False
    _connected_anchors_and_lines: dict = {}

    def __init__(self, x: int, y: int):
        global pen
        # Initialize fields
        self._x = x
        self._y = y
        self._highlighted: bool = True
        self._handler_on: bool = True
        self._connected_anchors_and_lines = dict()

        # Add to _anchors
        Anchor._anchors.append(self)
        Anchor._focused_anchor = self

        self._draw()

    @classmethod
    def handle_click(cls, x: float, y: float) -> bool:
        # Change focused anchor
        # Return true if there is an anchor clicked
        # false if not
        if cls._focused_anchor is not None:
            cls._focused_anchor.un_highlight()

        for anchor in cls._anchors:
            if anchor.is_clicked(x, y):
                anchor.highlight(True)
                return True
        return False

    @classmethod
    def get_focused_anchor(cls):
        return cls._focused_anchor

    def is_clicked(self, x: float, y: float) -> bool:
        # Box collider
        return x - Anchor.RADIUS < self._x < x + Anchor.RADIUS and \
               y - Anchor.RADIUS < self._y < y + Anchor.RADIUS

    def highlight(self, show_handler: bool = False):
        global pen
        # If another anchor is focused, un-focus it.
        if Anchor._focused_anchor is not None and Anchor._focused_anchor != self:
            Anchor._focused_anchor.un_highlight()

        if show_handler:
            self._handler_on = True

        # Focus self
        Anchor._focused_anchor = self
        self._highlighted = True

        # Draw
        self._draw()

    def un_highlight(self):
        global pen
        # Check focused
        if Anchor._focused_anchor == self:
            Anchor._focused_anchor = None
            self._handler_on = False
        self._highlighted = False

        # Draw
        self._draw()

    def move(self, x: int, y: int):
        global pen
        # Remove handler
        self._un_draw()

        # Update lines
        for connected_anchor, connection in self._connected_anchors_and_lines.items():
            if connection.anc_s == self:
                connection.update_anchor((x, y), connected_anchor.get_pos())
                continue

            connection.update_anchor(connected_anchor.get_pos(), (x, y))

        # Update position
        self._x, self._y = x, y

        # Draw
        self._draw()

        pen.pu()

    def connect(self, other_anchor):
        if other_anchor in self._connected_anchors_and_lines.keys():
            return

        # Add line
        line = Line(self, other_anchor)
        self._connected_anchors_and_lines[other_anchor] = line
        other_anchor._connected_anchors_and_lines[self] = line

    def get_pos(self) -> tuple[int, int]:
        return self._x, self._y

    def get_handlers(self) -> list[HandlerAnchor]:
        handlers = []
        for line in self._connected_anchors_and_lines.values():
            if line.anc_s == self:
                handlers.append(line.handler_s)
                continue

            if line.anc_e == self:
                handlers.append(line.handler_e)
                continue
        return handlers

    def _draw(self):
        global pen
        # Goto the anchor's position
        pen.pu()
        pen.goto(self._x, self._y)

        if self._handler_on:
            self._draw_handlers()
        else:
            self._hide_handlers()

        if self._highlighted:
            # Goto the anchor's position
            pen.pu()
            pen.goto(self._x, self._y)

            # Draw anchor
            pen.pd()
            pen.dot(Anchor.RADIUS + 3, "#0000FF")
            pen.dot(Anchor.RADIUS, "#FFFFFF")

            pen.pu()
            return

        # Goto the anchor's position
        pen.pu()
        pen.goto(self._x, self._y)

        # Draw anchor
        pen.pd()
        pen.dot(Anchor.RADIUS + 3, "#FFFFFF")
        pen.dot(Anchor.RADIUS, "#000000")

        pen.pu()

    def _un_draw(self):
        global pen
        # Goto the anchor's position
        pen.pu()
        pen.goto(self._x, self._y)

        self._hide_handlers()

        pen.pu()
        pen.goto(self._x, self._y)

        pen.pd()
        pen.dot(Anchor.RADIUS + 3, "#FFFFFF")

        pen.pu()
        return

    def _draw_handlers(self):
        global pen
        self._handler_on = True

        for handler in self.get_handlers():
            handler.draw()

    def _hide_handlers(self):
        global pen
        self._handler_on = False

        for handler in self.get_handlers():
            handler.un_draw()


class Line:
    # Class fields
    number_of_slices = 20

    # Private fields
    anc_s: Anchor
    anc_e: Anchor
    bezier_exp: BezierCurve2D
    handler_s: HandlerAnchor
    handler_e: HandlerAnchor

    def __init__(self, start_anchor: Anchor, end_anchor: Anchor):
        self.anc_s = start_anchor
        self.anc_e = end_anchor

        self._default_handlers()
        self._make_bezier_exp()
        self._draw()

    def _draw(self):
        global pen
        delta_t = 1 / Line.number_of_slices

        # Prepare for drawing
        pen.pu()
        pen.goto(self.bezier_exp.get_point(0))

        pen.pencolor("#000000")
        pen.pd()

        for i in range(1, Line.number_of_slices + 1):
            coordinate_of_next_point = self.bezier_exp.get_point(delta_t * i)
            pen.goto(coordinate_of_next_point[0], coordinate_of_next_point[1])

        t.pu()

    def update_anchor(self, new_anc_s_pos: tuple[int, int], new_anc_e_pos: tuple[int, int]):
        self._update(new_anc_s_pos, self.handler_s.get_local_pos(), new_anc_e_pos, self.handler_e.get_local_pos())

    def update_handler(self, new_handler_s_pos: tuple[int, int], new_handler_e_pos: tuple[int, int]):
        self._update(self.anc_s.get_pos(), new_handler_s_pos, self.anc_e.get_pos(), new_handler_e_pos)

    def _un_draw(self):
        global pen
        delta_t = 1 / Line.number_of_slices

        # Prepare for drawing
        pen.pu()
        pen.goto(self.bezier_exp.get_point(0))

        pen.pencolor("#FFFFFF")
        pen.pd()

        for i in range(1, Line.number_of_slices + 1):
            coordinate_of_next_point = self.bezier_exp.get_point(delta_t * i)
            pen.goto(coordinate_of_next_point[0], coordinate_of_next_point[1])

        t.pu()

    def _make_bezier_exp(self):
        intersection = _find_intersection_of_handlers(
            self.anc_s.get_pos(), self.handler_s.get_local_pos(),
            self.anc_e.get_pos(), self.handler_e.get_local_pos()
        )

        self.bezier_exp = BezierCurve2D(self.anc_s.get_pos(), intersection, self.anc_e.get_pos())

    def _update(
            self, new_anc_s_pos: tuple[int, int], new_handler_s_pos: tuple[int, int],
            new_anc_e_pos: tuple[int, int], new_handler_e_pos: tuple[int, int]
    ):
        intersection = _find_intersection_of_handlers(
            new_anc_s_pos, new_handler_s_pos, new_anc_e_pos, new_handler_e_pos
        )

        self._un_draw()
        self.bezier_exp = BezierCurve2D(new_anc_s_pos, intersection, new_anc_e_pos)
        self._draw()

    # noinspection PyProtectedMember
    def _default_handlers(self):
        anc_l, anc_r = (self.anc_s, self.anc_e) if _is_left(self.anc_s, self.anc_e) else (self.anc_e, self.anc_s)
        adj_l_x, l_y = anc_l.get_pos()
        r_x, r_y = anc_r.get_pos()

        # Find tangent
        if adj_l_x == r_x:
            adj_l_x -= 1e-2
        tangent = (r_y - l_y) / (r_x - adj_l_x)

        x = 10
        if self.anc_s == anc_l:
            self.handler_s = HandlerAnchor(x, int(tangent * x), anc_l)
            self.handler_e = HandlerAnchor(-x, int(-tangent * x), anc_r)
            return

        self.handler_s = HandlerAnchor(-x, int(-tangent * x), anc_r)
        self.handler_e = HandlerAnchor(x, int(tangent * x), anc_l)


def _is_left(anchor_1: Anchor, anchor_2: Anchor) -> bool:
    return anchor_1.get_pos()[0] <= anchor_2.get_pos()[0]


def _find_intersection_of_handlers(
    anc_s_pos: tuple[int, int], handler_s: tuple[int, int],
    anc_e_pos: tuple[int, int], handler_e: tuple[int, int]
) -> tuple[float, float]:
    is_left = anc_s_pos[0] <= anc_e_pos[0]
    l_anc, r_anc, l_handler, r_handler = \
        (anc_s_pos, anc_e_pos, handler_s, handler_e) if is_left else \
        (anc_e_pos, anc_s_pos, handler_e, handler_s)

    # If handler's x is 0 ZeroDivisionException will occur
    l_x_adj, l_y = l_handler
    r_x_adj, r_y = r_handler
    if l_x_adj == 0:
        l_x_adj = 1e-3

    if r_x_adj == 0:
        r_x_adj = 1e-3

    l_tangent = l_y / l_x_adj
    r_tangent = r_y / r_x_adj

    l_anc_x, l_anc_y = l_anc
    r_anc_x, r_anc_y = r_anc

    # Avoid parallel
    l_tangent = l_tangent if l_tangent != r_tangent else l_tangent - 1e-1

    # Tangent value may be zero. Avoid ZeroDivisionException
    tangent_diff_adj = l_tangent - r_tangent if l_tangent - r_tangent != 0 else 1e-3

    intersect_x = (l_tangent * l_anc_x - r_tangent * r_anc_x + r_anc_y - l_anc_y) / tangent_diff_adj
    intersect_y = l_tangent * (intersect_x - l_anc_x) + l_anc_y
    return intersect_x, intersect_y


def setup():
    global pen
    t.tracer(0, 0)
    t.ht()
    setup_canvas_event_listeners()
    pen = t.getturtle()
    t.mainloop()


def setup_canvas_event_listeners():
    global canvas
    canvas = t.getcanvas()
    canvas.bind("<KeyRelease>", change_mode)
    t.getscreen().listen()
    # canvas.bind("<Button-1>", direct_move_handler, True)


def draw_curve(pen: t.Turtle, curve: ParameterizedCurve2D, number_of_slices: int):
    delta_t = 1 / number_of_slices

    # Prepare for drawing
    pen.pu()
    pen.goto(curve.get_point(0))
    pen.pd()

    for i in range(1, number_of_slices + 1):
        coordinate_of_next_point = curve.get_point(delta_t * i)
        pen.goto(coordinate_of_next_point[0], coordinate_of_next_point[1])

    t.pu()


def change_mode(event):
    key = event.char
    if key == "p":
        # Pen tool
        canvas.unbind("<B1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
        canvas.unbind("<Button-1>")
        canvas.bind("<Button-1>", pen_tool_handler)
        # canvas.bind("")
        return

    if key == "m":
        # Direct move tool
        canvas.unbind("<B1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
        canvas.unbind("<Button-1>")
        canvas.bind("<Button-1>", direct_move_handler)
        return


def pen_tool_handler(event):
    global pen, canvas
    x, y = _get_local_x_y(event)

    prev_focus = Anchor.get_focused_anchor()

    h_exists = HandlerAnchor.handle_click(x, y)
    if h_exists:
        return

    anc_exists = Anchor.handle_click(x, y)
    if anc_exists:
        # Line adding
        new_focus = Anchor.get_focused_anchor()
        prev_focus.connect(new_focus)
        # noinspection PyProtectedMember
        new_focus._draw()
        return

    canvas.unbind("<B1-Motion>")
    canvas.unbind("<ButtonRelease-1>")
    Anchor(x, y)


def direct_move_handler(event):
    global pen, canvas
    x, y = _get_local_x_y(event)

    h_exists = HandlerAnchor.handle_click(x, y)
    if h_exists:
        handler = HandlerAnchor.get_clicked_handler()
        canvas.unbind("<B1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
        canvas.bind("<B1-Motion>", lambda e: move_handler(handler, e))
        return

    anc_exists = Anchor.handle_click(x, y)
    if anc_exists:
        anchor = Anchor.get_focused_anchor()
        anchor.highlight(True)
        canvas.unbind("<B1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
        canvas.bind("<B1-Motion>", lambda e: move_anchor(anchor, e))
        canvas.bind("<ButtonRelease-1>", lambda e: _end_move(anchor, e))
        return


def move_anchor(anchor: Anchor, event):
    x, y = _get_local_x_y(event)
    anchor.move(x, y)


def _end_move(anchor, event):
    global canvas
    anchor.highlight(True)


def move_handler(handler: HandlerAnchor, event):
    x, y = _get_local_x_y(event)
    handler.move(x, y)


def _get_local_x_y(event) -> tuple[int, int]:
    global canvas
    return canvas.canvasx(event.x), -canvas.canvasy(event.y)


if __name__ == "__main__":
    setup()
