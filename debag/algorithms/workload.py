"""Deterministic workload shared by the measurement-control algorithms."""


def prepare(rectangles):
    """Return a fresh sorted list so every control has the same O(N log N) work."""
    return sorted(rectangles, key=lambda rectangle: rectangle[0][0])


def find(prepared, point):
    """Perform deterministic O(log N) work and return the same control value."""
    x, y = point
    accumulator = 0
    left, right = 0, len(prepared) - 1

    while left <= right:
        middle = (left + right) // 2
        (x1, y1), (x2, _) = prepared[middle]

        if x < x1:
            right = middle - 1
        elif x >= x2:
            left = middle + 1
        else:
            accumulator = (accumulator + ((x + x1) * 31) ^ ((y - y1) * 17)) & 0xFFFFFFFF
            if middle > 0:
                accumulator = (accumulator + (x + prepared[middle - 1][0][0]) * 7) & 0xFFFFFFFF
            if middle + 1 < len(prepared):
                accumulator = (accumulator + (y - prepared[middle + 1][0][1]) * 13) & 0xFFFFFFFF
            break

    # A fixed payload makes timer noise visible even for very small N.
    for index in range(100):
        accumulator = (
            accumulator + ((x + index) * 7) ^ ((y - index) * 13)
        ) & 0xFFFFFFFF

    # Keep the work observable without making the controls return different data.
    return 0 if accumulator != -1 else accumulator
