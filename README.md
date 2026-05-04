# Procesare de Imagini

### Proiectul realizeaza procesarea paralela a unei imagini prin impartirea acesteia in mai multe sectiuni, fiecare proces aplicand operatiile de procesare pe portiunea sa. La final, rezultatele sunt combinate intr-o imagine finala. Scopul este reducerea timpului total de procesare prin executie paralela.

### Grayscale

```bash
mpiexec -n 4 python3 main.py input.jpg grayscale.jpg grayscale
```
### Blur

```bash
mpiexec -n 4 python3 main.py input.jpg blur.jpg blur
```

### Canny

```bash
mpiexec -n 4 python3 main.py input.jpg canny.jpg canny
```

### Invert

```bash
mpiexec -n 4 python3 main.py input.jpg invert.jpg invert
```

### Threshold

```bash
mpiexec -n 4 python3 main.py input.jpg threshold.jpg threshold
```

# Dependente

### Python

Instaleaza dependentele necesare:
```bash
pip install -r req.txt
```

### Windows

Este necesar sa descarci [MPI](https://www.microsoft.com/en-us/download/details.aspx?id=105289) si sa il adaugi in PATH.

### Linux

Instaleaza dependentele de sistem:

```bash
sudo apt update
sudo apt install openmpi-bin libopenmpi-dev
```

---

# Comparatie performanta

Timpii de mai jos au fost obtinuti prin rularea de **10 ori** a fiecarei comenzi pe aceeasi imagine de intrare (`secv/images/input.png`, `970 × 740` px, 3 canale `uint8`), folosind `.venv/bin/python` (Python 3.12).

Valorile reprezinta timpul **end-to-end** al executiei (pornire proces, citire imagine, procesare, scriere pe disc).

**Parametrii folositi:**
- `blur --kernel 7`
- `canny --low 50 --high 150`
- `threshold --threshold 120`

---

## Sequential (1 proces, fara paralelism)

| Operatie | Timp mediu (ms) | Mediana (ms) | Minim (ms) | Maxim (ms) |
|---|---:|---:|---:|---:|
| grayscale | 220.52 | 216.55 | 213.56 | 259.72 |
| blur | 236.74 | 231.99 | 229.78 | 265.57 |
| canny | 210.09 | 208.95 | 205.73 | 217.26 |
| invert | 235.76 | 229.31 | 226.05 | 275.27 |
| threshold | 214.82 | 214.85 | 205.78 | 231.44 |

---

## Threads (4 thread-uri, `concurrent.futures.ThreadPoolExecutor`)

| Operatie | Timp mediu (ms) | Mediana (ms) | Minim (ms) | Maxim (ms) |
|---|---:|---:|---:|---:|
| grayscale | 143.02 | 141.58 | 129.36 | 154.36 |
| blur | 158.39 | 153.41 | 137.32 | 202.10 |
| canny | 147.94 | 145.23 | 136.75 | 166.30 |
| invert | 145.86 | 139.52 | 132.46 | 169.60 |
| threshold | 144.83 | 142.95 | 137.08 | 154.06 |

---

## MPI (4 procese, `mpi4py`)

| Operatie | Timp mediu (ms) | Mediana (ms) | Minim (ms) | Maxim (ms) |
|---|---:|---:|---:|---:|
| grayscale | 1046.04 | 894.31 | 807.91 | 2581.78 |
| blur | 924.77 | 928.19 | 812.48 | 1015.71 |
| canny | 916.31 | 913.52 | 888.20 | 939.31 |
| invert | 915.64 | 912.78 | 890.49 | 941.55 |
| threshold | 916.06 | 914.90 | 887.79 | 953.88 |

---

## Rezumat speedup fata de varianta secventiala

| Operatie | Threads (4T) | MPI (4P) |
|---|---:|---:|
| grayscale | **1.54×** mai rapid | 4.74× mai lent |
| blur | **1.49×** mai rapid | 3.91× mai lent |
| canny | **1.42×** mai rapid | 4.36× mai lent |
| invert | **1.62×** mai rapid | 3.88× mai lent |
| threshold | **1.48×** mai rapid | 4.26× mai lent |

---

## Observatii

- **Threads** este mai rapid decat varianta secventiala cu ~35–60% datorita faptului ca OpenCV elibereaza GIL-ul in timpul operatiilor numerice, permitand thread-urilor sa ruleze cu adevarat in paralel.
- **MPI** este de ~4× mai lent decat varianta secventiala pentru aceasta imagine. Motivul principal este overhead-ul de pornire: `mpiexec -n 4` lanseaza 4 procese Python independente (fiecare cu initializarea interpetorului, importul cv2/numpy/mpi4py, negocierea MPI), overhead ce domina complet timpul real de procesare pe o imagine de 970×740 px.
- Pentru imagini mult mai mari sau batch-uri, MPI ar putea recupera diferenta — costul fix de pornire devine neglijabil raportat la volumul de calcul.
- Varianta cu threads ramane cea mai eficienta pentru procesarea unei singure imagini de dimensiuni medii pe o masina locala.
