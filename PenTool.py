import turtle as t
from Curve2D import *


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


if __name__ == "__main__":
    t.tracer(0, 0)
    t.ht()
    sample_curve = BezierCurve2D((-500, -300), (0, 300), (500, -300))
    draw_curve(t.getturtle(), sample_curve, 1000)
    t.goto((0, 300))
    t.dot(10, "#ff0000")
    t.goto((-500, -300))
    t.dot(10, "#00ff00")
    t.goto((500, -300))
    t.dot(10, "#0000ff")
    t.mainloop()