# Python 성능 최적화 실전 가이드

Python은 느리다는 편견이 있지만, 올바른 도구를 쓰면 충분히 빠른 코드를 작성할 수 있습니다.

## 먼저 측정하라

최적화는 추측이 아닌 측정에서 시작합니다.

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 측정할 코드
result = my_heavy_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

라인별 분석은 `line_profiler`:

```bash
pip install line-profiler
kernprof -l -v script.py
```

## NumPy 벡터화

반복문을 NumPy 연산으로 대체하면 10~100배 빨라집니다.

```python
import numpy as np
import time

data = np.random.randn(1_000_000)

# 느린 방법
start = time.perf_counter()
result = [x ** 2 for x in data]
print(f"List comprehension: {time.perf_counter() - start:.3f}s")

# 빠른 방법
start = time.perf_counter()
result = data ** 2
print(f"NumPy: {time.perf_counter() - start:.3f}s")
```

## 제너레이터로 메모리 절약

```python
# 메모리를 한 번에 다 쓰는 방법
def read_all(filename):
    with open(filename) as f:
        return f.readlines()  # 전체 파일을 메모리에 올림

# 제너레이터로 스트리밍
def stream_lines(filename):
    with open(filename) as f:
        for line in f:
            yield line.strip()  # 한 줄씩 처리
```

## Cython / Numba

순수 Python 병목이라면 JIT 컴파일을 활용합니다.

```python
from numba import njit
import numpy as np

@njit
def fast_sum(arr):
    total = 0.0
    for x in arr:
        total += x
    return total

arr = np.random.randn(10_000_000)
fast_sum(arr)  # 첫 호출은 컴파일, 이후는 C 속도
```

## 멀티프로세싱

CPU 바운드 작업은 GIL 우회를 위해 `multiprocessing`을 씁니다.

```python
from multiprocessing import Pool

def process_chunk(chunk):
    return [x ** 2 for x in chunk]

data = list(range(1_000_000))
chunks = [data[i::4] for i in range(4)]

with Pool(4) as pool:
    results = pool.map(process_chunk, chunks)
```

## 요약

| 상황 | 도구 |
|------|------|
| 수치 연산 | NumPy / SciPy |
| 반복 최적화 | Numba `@njit` |
| CPU 병렬 | multiprocessing |
| I/O 병렬 | asyncio / threading |
| C 확장 | Cython |
