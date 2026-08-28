import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_ROOT / "tests" / "data" / "test_data.json"

MAX_N = 500
STEP = 50
NUM_DOTS = 1000

P1 = 1000000007
P2 = 1000000009


def generate_test_data():
    test_data = {}

    for n in range(0, MAX_N + 1, STEP):  
        # набор вложенных друг-в-друга с координатами с шагом больше 1
        rectangles = [
            ((10 * i, 10 * i), (10 * (2 * n - i), 10 * (2 * n - i)))
            for i in range(1, n)
        ]

        # неслучайный набор распределенных более-менее равномерно по ненулевому пересечению прямоугольников
        if n == 0:
            dots = []
        else:
            modulus = 20 * n
            dots = [
                ((P1 * i) ** 31 % modulus, (P2 * i) ** 31 % modulus)
                for i in range(1, NUM_DOTS + 1)
            ]

        test_data[str(n)] = {"rectangles": rectangles, "dots": dots}

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(test_data, f)

    print(f"Сохранено в {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_test_data()