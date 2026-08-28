"Алгоритм перебора"

# без подготовки
def prepare(rectangles): #O(1)
    #check_rectangles(rectangles) #O(N)
    return rectangles

# при поиске – просто перебор всех прямоугольников
def find(prepared, dot): #O(N)
    check_rectangles(prepared) #O(N)
    x, y = dot
    if x < 0 or y < 0 or x > 10**9 or y > 10**9:
        return 0

    s = 0
    for rect in prepared: 
        if rect[1][0] > x and rect[0][0] <= x and rect[1][1] > y and rect[0][1] <= y:
            s += 1
    return s

# field ([1..10^9],[1..10^9]). 
# rectangles <=> rect <=> list {(2,2),(6,8)}, {(5,4),(9,10)}, {(4,0),(11,6)}, {(8,2),(12,12)}
# prepared <=> map 
# point <=> (x,y)

#Присылать необходимо zip-архив, добавить в sh файл сворачивания в zip с флагом
#добавить docker yaml

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