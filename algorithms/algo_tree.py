"Алгоритм на дереве"

from collections import defaultdict
from bisect import bisect_left, bisect_right

def tree_add(root, left, right, pos, count):# O(log N)
    new = len(tree)
    tree.append(list(tree[root]))
    mid = (left + right) // 2 # left = 2*i+1, right = 2*i+2, parent = (i-1)//2
    if left == right:
        tree[new][0] += count # tree[i] = [sum, left_child, right_child]
        return new
    if pos <= mid:
        tree[new][1] = tree_add(tree[root][1], left, mid, pos, count)
    else:
        tree[new][2] = tree_add(tree[root][2], mid + 1, right, pos, count)
    tree[new][0] = tree[tree[new][1]][0] + tree[tree[new][2]][0]
    return new

def tree_query(root, left, right, l, r):  # O(log N)
    if l > right or r < left or root == 0:
        return 0
    if l <= left and right <= r:
        return tree[root][0]
    mid = (left + right) // 2
    return (tree_query(tree[root][1], left, mid, l, r) +
            tree_query(tree[root][2], mid + 1, right, l, r))


def prepare(rectangles):  # O(NlogN)
    check_rectangles(rectangles) # O(N)
    
    global tree
    tree = [[0, 0, 0]]

    # отсортировать точки за NlogN
    x_sort = sorted({x for r in rectangles for x in (r[0][0], r[1][0])})
    y_sort = sorted({y for r in rectangles for y in (r[0][1], r[1][1])})
    
    add = defaultdict(list)
    rem = defaultdict(list)

    # разделить на список на удаление/добавление за NlogN
    for (x1, y1), (x2, y2) in rectangles:  # O(N)
        y1_idx = bisect_left(y_sort, y1) # O(logN)
        y2_idx = bisect_left(y_sort, y2)
        add[x1].append((y1_idx, y2_idx)) # O(1)
        rem[x2].append((y1_idx, y2_idx))

    roots = {}
    root = 0
    n = len(y_sort)

    # составить дерево за NlogN
    for x in x_sort: # O(len(set(x)))
        # добавить отрезки в [x]
        for start, end in add[x]: # O(len(add[x])) <=> N/len(set(x))
            root = tree_add(root, 0, n - 1, start, +1) # O(log N)
            root = tree_add(root, 0, n - 1, end,   -1)

        # удалить отрезки из [x]
        for start, end in rem[x]:
            root = tree_add(root, 0, n - 1, start, -1)
            root = tree_add(root, 0, n - 1, end,   +1)

        roots[x] = root

    return (x_sort, y_sort, roots)

def find(prepared, dot):  # O(log N)
    xs, ys, roots = prepared
    x, y = dot

    ix = bisect_right(xs, x) - 1
    iy = bisect_right(ys, y) - 1

    if ix < 0 or iy < 0:
        return 0

    return tree_query(roots[xs[ix]], 0, len(ys) - 1, 0, iy)


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