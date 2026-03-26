# Image Processing - Secvential

### Acest folder contine varianta secventiala a proiectului de procesare de imagini. Programul citeste o imagine, aplica o singura operatie pe intreaga imagine, apoi salveaza rezultatul final. Scopul lui este sa ofere o implementare simpla, usor de testat si comparat cu varianta paralela.

## Cum functioneaza

### Scriptul principal este `secv.py`.
### Programul:
### 1. citeste argumentele din linia de comanda
### 2. incarca imaginea de intrare
### 3. aplica operatia ceruta
### 4. salveaza imaginea rezultata

## Operatii disponibile

### Grayscale

```bash
python3 secv.py images/input.png images/grayscale.png grayscale
```

### Blur

```bash
python3 secv.py images/input.png images/blur.png blur --kernel 7
```

### Canny

```bash
python3 secv.py images/input.png images/canny.png canny --low 50 --high 150
```

### Invert

```bash
python3 secv.py images/input.png images/invert.png invert
```

### Threshold

```bash
python3 secv.py images/input.png images/threshold.png threshold --threshold 120
```

## Dependente

### Python

Instalarea pachetelor necesare:

```bash
pip install -r req.txt
```

### Pachete folosite

### `opencv-python` - pentru citirea, procesarea si salvarea imaginilor
### `numpy` - pentru lucrul cu datele imaginii in format matrice

## Fisiere importante

### `secv.py` - implementarea procesarii secventiale
### `req.txt` - lista de dependente Python
### `images/` - exemple de imagini de intrare si iesire
