# Image Processing

### The project will perform parallel image processing by dividing the image into multiple sections, with each process applying processing operations to its assigned portion. At the end, the results will be combined into a final image. The goal is to reduce the overall processing time by using parallel execution.

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

# Dependencies

### Py

Install the necessary requierments
```bash
pip install -r req.txt
```

### Windows

Need to download [MPI](https://www.microsoft.com/en-us/download/details.aspx?id=105289) and add to path 

### Linux 
Need to isntal dependences

```bash
sudo apt update
sudo apt install openmpi-bin libopenmpi-dev
```