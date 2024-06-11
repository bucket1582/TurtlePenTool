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

    def __init__(self, x: int, y: int, anchor):
        self._x = x
        self._y = y
        self._anchor = anchor

    @classmethod
    def handle_click(cls, x: float, y: float) -> bool:
        cls._clicked_handler = None
        anc = Anchor.get_focused_anchor()
        if anc is None:
            return False

        h_l, h_r = anc.get_handlers()
        if h_l.is_clicked(x, y):
            cls._clicked_handler = h_l
            return True
        if h_r.is_clicked(x, y):
            cls._clicked_handler = h_r
            return True

        return False

    def is_clicked(self, x: float, y: float) -> bool:
        global_x, global_y = self.get_pos()
        # Box collider
        return x - HandlerAnchor.RADIUS < global_x < x + HandlerAnchor.RADIUS and \
               y - HandlerAnchor.RADIUS < global_y < y + HandlerAnchor.RADIUS

    def draw(self):
        global pen
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
            anc_s_handler = self._anchor.get_handlers()
            if anc_s_handler[0] == self:
                anc_s_handler = ((x - anc_x, y - anc_y), anc_s_handler[1].get_local_pos())
            else:
                anc_s_handler = (anc_s_handler[0].get_local_pos(), (x - anc_x, y - anc_y))

            anc_e_handler = connected_anchor.get_handlers()
            anc_e_handler = (anc_e_handler[0].get_local_pos(), anc_e_handler[1].get_local_pos())
            connection.redraw_bezier_exp(
                self._anchor.get_pos(), anc_s_handler, connected_anchor.get_pos(), anc_e_handler
            )

        # Update position
        self._x, self._y = x - anc_x, y - anc_y

        # Draw
        self.draw()

        self._anchor.draw()
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
    _handler_l: HandlerAnchor
    _handler_r: HandlerAnchor
    _highlighted: bool = False
    _handler_on: bool = False
    _connected_anchors_and_lines: dict = {}

    def __init__(self, x: int, y: int):
        global pen
        # Initialize fields
        self._x = x
        self._y = y
        self._handler_l = HandlerAnchor(-30, 0, self)
        self._handler_r = HandlerAnchor(30, 0, self)
        self._highlighted: bool = True
        self._handler_on: bool = True
        self._connected_anchors_and_lines = dict()

        # Add to _anchors
        Anchor._anchors.append(self)
        Anchor._focused_anchor = self

        self.draw()

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
        self.draw()

    def un_highlight(self):
        global pen
        # Check focused
        if Anchor._focused_anchor == self:
            Anchor._focused_anchor = None
            self._handler_on = False
        self._highlighted = False

        # Draw
        self.draw()

    def move(self, x: int, y: int):
        global pen
        # Remove handler
        self._un_draw()

        # Update lines
        for connected_anchor, connection in self._connected_anchors_and_lines.items():
            anc_s_handler = self.get_handlers()
            anc_s_handler = (anc_s_handler[0].get_local_pos(), anc_s_handler[1].get_local_pos())

            anc_e_handler = connected_anchor.get_handlers()
            anc_e_handler = (anc_e_handler[0].get_local_pos(), anc_e_handler[1].get_local_pos())
            connection.redraw_bezier_exp((x, y), anc_s_handler, connected_anchor.get_pos(), anc_e_handler)

        # Update position
        self._x, self._y = x, y

        # Draw
        self.draw()

        pen.pu()

    def connect(self, other_anchor):
        if other_anchor in self._connected_anchors_and_lines.keys():
            return

        if len(self._connected_anchors_and_lines) == 0 and len(other_anchor._connected_anchors_and_lines) == 0:
            # Set handlers to default
            self._default_handler_for_connection(other_anchor)
            other_anchor._default_handler_for_connection(self)

        # Add line
        line = Line(self, other_anchor)
        self._connected_anchors_and_lines[other_anchor] = line
        other_anchor._connected_anchors_and_lines[self] = line

    def get_pos(self) -> tuple[int, int]:
        return self._x, self._y

    def get_handlers(self) -> tuple[HandlerAnchor, HandlerAnchor]:
        return self._handler_l, self._handler_r

    def draw(self):
        global pen
        # Goto the anchor's position
        pen.pu()
        pen.goto(self._x, self._y)

        if self._handler_on:
            self._draw_handlers()
        else:
            self._remove_handlers()

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

        self._remove_handlers()

        pen.pu()
        pen.goto(self._x, self._y)

        pen.pd()
        pen.dot(Anchor.RADIUS + 3, "#FFFFFF")

        pen.pu()
        return

    def _draw_handlers(self):
        global pen
        self._handler_on = True

        for handler in (self._handler_l, self._handler_r):
            handler.draw()

    def _remove_handlers(self):
        global pen
        self._handler_on = False

        for handler in (self._handler_l, self._handler_r):
            handler.un_draw()

    def _default_handler_for_connection(self, other_anchor):
        # Compute tangent
        other_pos = other_anchor.get_pos()
        adj_x = self._x if self._x != other_pos[0] else self._x - 1e-2
        tangent = (self._y - other_pos[1]) / (adj_x - other_pos[0])

        # If handler is on, move the handler
        if self._handler_on:
            if _is_left(self, other_anchor):
                x = 20
                self._handler_r.move(self._x + x, self._y + tangent * x)
                return

            x = -20
            self._handler_l.move(self._x + x, self._y + tangent * x)
            return

        # If handler is off, move (silently)
        if _is_left(self, other_anchor):
            x = 20
            self._handler_r.set_default(self._x + x, self._y + tangent * x)
            return

        x = -20
        self._handler_l.set_default(self._x + x, self._y + tangent * x)


class Line:
    # Class fields
    number_of_slices = 10

    # Private fields
    anc_s: Anchor
    anc_e: Anchor
    bezier_exp: BezierCurve2D

    def __init__(self, start_anchor: Anchor, end_anchor: Anchor):
        self.anc_s = start_anchor
        self.anc_e = end_anchor

        self._make_bezier_exp()
        self.draw()

    def draw(self):
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
        # Find if start anchor or end anchor is in left side
        if _is_left(self.anc_s, self.anc_e):
            left_anchor = self.anc_s
            right_anchor = self.anc_e
        else:
            left_anchor = self.anc_e
            right_anchor = self.anc_s

        left_handlers = left_anchor.get_handlers()
        left_handlers = (left_handlers[0].get_local_pos(), left_handlers[1].get_local_pos())

        right_handlers = right_anchor.get_handlers()
        right_handlers = (right_handlers[0].get_local_pos(), right_handlers[1].get_local_pos())

        # Compute intersection of handlers
        intersection = _find_intersection_of_handlers(
            left_anchor.get_pos(), left_handlers,
            right_anchor.get_pos(), right_handlers
        )

        # Add bezier_expression
        self.bezier_exp = BezierCurve2D(self.anc_s.get_pos(), intersection, self.anc_e.get_pos())

    def redraw_bezier_exp(
            self, new_anc_s_pos: tuple[int, int], new_anc_s_handlers: tuple[tuple[int, int], tuple[int, int]],
            new_anc_e_pos: tuple[int, int], new_anc_e_handlers: tuple[tuple[int, int], tuple[int, int]]
    ):
        is_left = new_anc_s_pos[0] <= new_anc_e_pos[0]
        left_anchor = new_anc_s_pos if is_left else new_anc_e_pos
        right_anchor = new_anc_e_pos if is_left else new_anc_s_pos

        left_handlers = new_anc_s_handlers if is_left else new_anc_e_handlers
        right_handlers = new_anc_e_handlers if is_left else new_anc_s_handlers

        intersection = _find_intersection_of_handlers(left_anchor, left_handlers, right_anchor, right_handlers)

        self._un_draw()
        self.bezier_exp = BezierCurve2D(left_anchor, intersection, right_anchor)
        self.draw()


def _is_left(anchor_1: Anchor, anchor_2: Anchor) -> bool:
    return anchor_1.get_pos()[0] <= anchor_2.get_pos()[0]


def _find_intersection_of_handlers(
    anc_l_pos: tuple[int, int], anc_l_handlers: tuple[tuple[int, int], tuple[int, int]],
    anc_r_pos: tuple[int, int], anc_r_handlers: tuple[tuple[int, int], tuple[int, int]]
) -> tuple[float, float]:
    left_anchor_right_handler = anc_l_handlers[1]
    right_anchor_left_handler = anc_r_handlers[0]

    # If handler's x is 0 ZeroDivisionException will occur
    l_x_adj, l_y = left_anchor_right_handler
    r_x_adj, r_y = right_anchor_left_handler
    if l_x_adj == 0:
        l_x_adj = 1e-3

    if r_x_adj == 0:
        r_x_adj = 1e-3

    l_tangent = l_y / l_x_adj
    r_tangent = r_y / r_x_adj

    l_anc_x, l_anc_y = anc_l_pos
    r_anc_x, r_anc_y = anc_r_pos

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
