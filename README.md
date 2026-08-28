<div align="center">

# Лабораторная работа № 2

**Русский** 丨 [English](README_EN.md)

</div>

## Задача

Даны прямоугольники на плоскости с углами в целочисленных координатах ([1..10⁹],[1..10⁹]). Требуется как можно быстрее выдавать ответ на вопрос «Скольким прямоугольникам принадлежит точка (x,y)?» И подготовка данных должна занимать мало времени.

Только нижние границы включены => (x1<= x) && (x<x2) && (y1<=y) && (y<y2)

## Пример

Прямоугольники: {(2,2),(6,8)}, {(5,4),(9,10)}, {(4,0),(11,6)}, {(8,2),(12,12)}

Точка-ответ:
- (2,2) -> 1
- (12,12) -> 0
- (10,4) -> 2
- (5,5) -> 3
- (2,10) -> 0
- (2,8) -> 0

___


## Проверка устойчивости замеров

Методика измерений отдельно проверяется тремя одинаковыми контрольными нагрузками. Это позволяет обнаружить существенное влияние системного шума, порядка запуска и доступности данных. Подробности и команда запуска приведены в [отчёте `debag`](debag/README.md).


| Algo | Prepare | find | Описание |
|------|---------|------|----------|
| `brute` | O(1) | O(N) | Без подготовки. При поиске — перебор всех прямоугольников |
| `map` | O(N³) | O(log N) | Сжатие координат и построение двумерной карты |
| `tree` | O(N log N) | O(log N) | Сжатие координат и построение персистентного дерева отрезков |


## Генерация тестовых данных

Используется набор вложенных друг-в-друга прямоугольников с координатами с шагом, превышающим единицу. Для каждого значения $i$ от 1 до $N-1$:

$$x[0][0] = (10i, 10i)$$
$$x[1][1] = (10(2N - i), 10(2N - i))$$

- M = const

Используется псевдослучайная генерация точек, распределённых более-менее равномерно по ненулевому пересечению прямоугольников

$$x_i = (P_1 \cdot i)^{31} \bmod (20N)$$
$$y_i = (P_2 \cdot i)^{31} \bmod (20N)$$

где:
- $P_1,P_2$ — большие простые числа (разные для $x$ и $y$)
- Хэш-функция $(P \cdot i)^{31} \bmod m$ обеспечивает псевдослучайное распределение точек


## Запуск и автоматизация

Shell-скрипты разделены по назначению и находятся в `scripts/`:

| Команда | Назначение |
|---|---|
| `./scripts/run_tests.sh -run -all` | основные тесты, отчёт и общие графики |
| `./scripts/run_debag.sh` | контроль устойчивости измерений |
| `./scripts/build_reports.sh main|debag|all` | сборка README и графиков из временных CSV |
| `./scripts/create_archive.sh` | воспроизводимый архив `release.zip` |
| `./scripts/build_docker.sh` | локальный образ `lab2:latest` |
| `./scripts/release.sh` | последовательный запуск всех этапов |

### Основные тесты
```bash
./scripts/run_tests.sh -run -all
```

### Через Docker

```bash
docker compose run --rm lab2
```
<details>
  <summary>linux</summary>
  Если файлы создаются не от вашего пользователя:

  ```bash
  echo "UID=$(id -u)\nGID=$(id -g)" > .env
  ```
</details>



## Результаты тестирования


## Время подготовки


![Prepare Time](tests/report/resources/prepare_time.png)


![Prepare Linear No Map](tests/report/resources/prepare_linear_no_map.png)


![Prepare Log](tests/report/resources/prepare_log.png)


## Время поиска (для одного запроса)


![find Time](tests/report/resources/find_time.png) 


![find Log](tests/report/resources/find_log.png)


![find Linear No Brute](tests/report/resources/find_linear_no_brute.png)


## Общие графики


![Log Log](tests/report/resources/log_log.png)


## Общее время работы алгоритма

### Общая формула:
$$t(N, M) = PrepareTime(N) + M \times FindTime(N)$$
, где 
- N - число прямоугольников
- M - число точек

значения `PrepareTime(N)` и `FindTime(N)` взяты из `results.csv`


![Time by N](tests/report/resources/time_by_N.png)

![Time by N (log)](tests/report/resources/time_by_N_log.png)


![Time by M](tests/report/resources/time_by_M.png)


т.е. для алгоритмов A и B, запущенных одновременно, можно найти такие M и N при которых B становиться эффективнее (быстрее) A, другими словами - точку пересечения $t_A(N,M)$ и $t_B(N,M)$
$$PrepareTime_A(N) + M \times FindTime_A(N) = PrepareTime_B(N) + M \times FindTime_B(N)$$
$$,следовательно$$
$$M(N) = \frac{PrepareTime_B(N) - PrepareTime_A(N)}{FindTime_A(N) - FindTime_B(N)}$$


![Области оптимального алгоритма (линейный)](tests/report/resources/algo_regions_linear.png)

![Области оптимального алгоритма (логарифмический)](tests/report/resources/algo_regions_log.png)


## Вывод

Быстрее всего на вопрос «Скольким прямоугольникам принадлежит точка (x,y)?» ответит:
- алгоритм перебора — при малом M;
- алгоритм на карте — при огромном M;
- алгоритм на дереве — в остальных случаях (большинстве).


<details>
  <summary>P.S.</summary>
  
  
| команда | обновленные файлы |
|----------------|------------------|
| `./scripts/run_tests.sh -run` | `README.md`, `README_EN.md`, `tests/report/resources/*.png` |
| `./scripts/run_tests.sh -run -all` | `README.md`, `README_EN.md`, `tests/report/resources/*.png` |
| `./scripts/run_debag.sh` | `debag/README.md`, `debag/README_EN.md`, `debag/reports/resources/*.png` |
| `./scripts/build_reports.sh main|debag|all` | отчёты и графики из уже созданных временных CSV |
| `docker compose up` | `README.md`, `README_EN.md`, `tests/report/resources/*.png` |

Промежуточные JSON и CSV создаются только на время запуска и затем удаляются.

примерные графики t(N,M)

- **Brute**: `PrepareTime = 9.64e-08`, `FindTime = 2.04e-07 × N`
- **Map**: `PrepareTime = 2.81e-08 × N³`, `FindTime = 4.22e-08 × log₂(N)`
- **Tree**: `PrepareTime = 1.47e-06 × N × log₂(N)`, `FindTime = 1.75e-07 × log₂(N)`
</details>
