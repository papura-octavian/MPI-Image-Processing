# Documentatie Proiect

## 1. Cerintele / tema proiectului

Acest repository contine implementarea secventiala a unui proiect de procesare de imagini.

- Algoritm / abordare: procesare secventiala a unei imagini digitale, fara paralelizare, fara impartirea imaginii in blocuri si fara combinarea unor rezultate partiale.
- Limbaj de programare: Python 3.
- Biblioteci folosite:
  - `opencv-python` pentru citirea, procesarea si salvarea imaginilor.
  - `numpy` pentru reprezentarea datelor imaginii sub forma de tablouri.
- Fisier principal: `secv.py`.
- Model de executie: aplicatia citeste o imagine, aplica o singura operatie pe intreaga imagine si salveaza rezultatul.

Operatii implementate:

- `grayscale`
- `blur`
- `canny`
- `invert`
- `threshold`

Fluxul programului:

1. Citeste argumentele din linia de comanda.
2. Incarca imaginea de intrare folosind OpenCV.
3. Valideaza operatia si parametrii primiti.
4. Proceseaza imaginea secvential.
5. Salveaza rezultatul in fisierul de iesire.

Exemple de rulare:

```bash
.venv/bin/python secv.py images/input.png images/grayscale.png grayscale
.venv/bin/python secv.py images/input.png images/blur.png blur --kernel 7
.venv/bin/python secv.py images/input.png images/canny.png canny --low 50 --high 150
.venv/bin/python secv.py images/input.png images/invert.png invert
.venv/bin/python secv.py images/input.png images/threshold.png threshold --threshold 120
```

Imaginea folosita la testare are dimensiunea `970 x 740` pixeli, cu 3 canale de culoare (`uint8`).

## 2. Informatii despre masina pe care a fost rulat codul

Mediul pe care au fost colectate rezultatele:

- Sistem de operare: Zorin OS 18 (Ubuntu noble base)
- Kernel: Linux `6.17.0-19-generic`
- Arhitectura: `x86_64`
- Procesor: 12th Gen Intel(R) Core(TM) i5-12450H
- Numar CPU logice: 12
- Numar nuclee fizice: 8
- Frecventa maxima raportata: 4.40 GHz
- Memorie RAM: 15 GiB
- Python: `3.12.3`

Dependente folosite la rulare:

- `opencv-python 4.13.0.92`
- `numpy 2.4.3`

## 3. Rezultate experimentale

Timpii de mai jos au fost obtinuti prin rularea de 10 ori a fiecarei comenzi, pe aceeasi imagine de intrare (`images/input.png`), folosind interpretul din mediul virtual local `.venv/bin/python`.

Valorile reprezinta timpul end-to-end al executiei, deci includ:

- pornirea procesului Python
- citirea imaginii
- procesarea propriu-zisa
- scrierea imaginii rezultate pe disc

### Parametrii folositi

- `blur --kernel 7`
- `canny --low 50 --high 150`
- `threshold --threshold 120`

### Timpi de executie

| Operatie | Timp mediu (ms) | Mediana (ms) | Minim (ms) | Maxim (ms) |
| --- | ---: | ---: | ---: | ---: |
| grayscale | 220.52 | 216.55 | 213.56 | 259.72 |
| blur | 236.74 | 231.99 | 229.78 | 265.57 |
| canny | 210.09 | 208.95 | 205.73 | 217.26 |
| invert | 235.76 | 229.31 | 226.05 | 275.27 |
| threshold | 214.82 | 214.85 | 205.78 | 231.44 |

### Observatii

- In acest set de teste, `canny` a avut cel mai mic timp mediu de executie.
- `blur` si `invert` au fost cele mai lente dintre operatiile masurate.
- Diferentele dintre operatii sunt relativ mici pentru aceasta imagine, ceea ce sugereaza ca o parte semnificativa din timpul total vine din costurile fixe de pornire, I/O si apelurile OpenCV.
- Pentru o comparatie mai relevanta intre varianta secventiala si una paralela, ar merita folosite imagini mai mari sau batch-uri de imagini.
