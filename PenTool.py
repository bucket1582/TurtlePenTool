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
    RADIUS: Final[int] = 3

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
        pen.dot(HandlerAnchor.RADIUS + 1, "#000000")
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
        pen.dot(HandlerAnchor.RADIUS + 1, "#FFFFFF")

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
        # Remove handler
        self.un_draw()

        # Update position
        self._x, self._y = x, y

        # Draw
        self.draw()

        pen.pu()


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

    def __init__(self, x: int, y: int):
        global pen
        # Initialize fields
        self._x = x
        self._y = y
        self._handler_l = HandlerAnchor(-30, 0, self)
        self._handler_r = HandlerAnchor(30, 0, self)
        self._highlighted: bool = True
        self._handler_on: bool = True

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

        # Update position
        self._x, self._y = x, y

        # Draw
        self._draw()

        pen.pu()

    def get_pos(self) -> tuple[int, int]:
        return self._x, self._y

    def get_handlers(self) -> tuple[HandlerAnchor, HandlerAnchor]:
        return self._handler_l, self._handler_r

    def _draw(self):
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
    canvas.bind("<Button-1>", draw_anchor, True)


def draw_curve(pen: t.Turtle, curve: ParameterizedCurve2D, number_of_slices: int):
    delta_t = 1 / number_of_slices

    # Prepare for drawing
    pen.pu()
    pen.goto(curve.get_point(0))
    pen.pd()

    for i in range(1, number_of_slices + 1):
        print(delta_t * i)
        coordinate_of_next_point = curve.get_point(delta_t * i)
        print(f"t: {delta_t * i} -> point: {coordinate_of_next_point}")
        pen.goto(coordinate_of_next_point[0], coordinate_of_next_point[1])

    t.pu()


def draw_anchor(event):
    global pen, canvas
    x, y = _get_local_x_y(event)
    exists = Anchor.handle_click(x, y)

    if exists:
        anchor = Anchor.get_focused_anchor()
        anchor.highlight(True)
        canvas.bind("<B1-Motion>", lambda e: move_anchor(anchor, e))
        canvas.bind("<ButtonRelease-1>", lambda e: _end_move(anchor, e))
        return

    canvas.unbind("<B1-Motion>")
    canvas.unbind("<ButtonRelease-1>")
    Anchor(x, y)


def move_anchor(anchor: Anchor, event):
    x, y = _get_local_x_y(event)
    anchor.move(x, y)


def _end_move(anchor, event):
    global canvas
    anchor.highlight(True)


def _get_local_x_y(event) -> tuple[int, int]:
    global canvas
    return canvas.canvasx(event.x), -canvas.canvasy(event.y)


if __name__ == "__main__":
    setup()
