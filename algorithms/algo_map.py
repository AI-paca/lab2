"Алгоритм на карте"

from bisect import bisect_left, bisect_right


def prepare(rectangles):  # O(N^3)
    check_rectangles(rectangles)

    # отсортировать точки за NlogN
    x_sort = sorted({x for r in rectangles for x in (r[0][0], r[1][0])})
    y_sort = sorted({y for r in rectangles for y in (r[0][1], r[1][1])})
    
    new_map = [[0] * len(y_sort) for _ in range(len(x_sort))]

    # предопределить карту N^3
    for (x1, y1), (x2, y2) in rectangles: # O(N)
        # найти границы 4logN
        ix1 = bisect_left(x_sort, x1)
        ix2 = bisect_left(x_sort, x2)
        iy1 = bisect_left(y_sort, y1)
        iy2 = bisect_left(y_sort, y2)

        for ix in range(ix1, ix2): # O(N)
            for iy in range(iy1, iy2): # O(N)
                new_map[ix][iy] += 1

    return (x_sort, y_sort, new_map)


def find(prepared, dot):  # O(logN)
    x, y = dot
    if x < 0 or y < 0 or x > 10**9 or y > 10**9:
        return 0

    x_sort, y_sort, grid = prepared

    idx_x = bisect_right(x_sort, x) - 1  # logN; ближайшая координата <= x
    idx_y = bisect_right(y_sort, y) - 1  # logN; ближайшая координата <= y

    if idx_x < 0 or idx_y < 0:
        return 0

    return grid[idx_x][idx_y]


################################################################################
def check_point(dot):
    x, y = dot
    if type(x) is not int or type(y) is not int:
        raise TypeError(f"Координаты должны быть целыми: ({x}, {y})")
    if x < 1 or y < 1:
        raise ValueError(f"Координаты не могут быть меньше 1: ({x}, {y})")
    if x > 10**9 or y > 10**9:
        raise ValueError(f"Координаты не могут превышать 10^9: ({x}, {y})")


def check_rectangles(rectangles):
    for rect in rectangles:
        for dot in rect:
            check_point(dot)
            
        # левый нижний < верхний правый
        (x1, y1), (x2, y2) = rect
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"Некорректные границы прямоугольника: ({x1},{y1})-({x2},{y2})")