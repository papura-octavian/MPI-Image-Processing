from __future__ import annotations

import argparse
import os
import sys

import cv2
import numpy as np
from mpi4py import MPI

# Lista cu operatiile pe care programul le stie.
VALID_OPERATIONS = {"grayscale", "blur", "canny", "invert", "threshold"}

# For FatFingers
OPERATION_ALIASES = {
    "ivert": "invert",
    "inverrt": "invert",
    "invers": "invert",
    "gayscale": "grayscale",
    "bklur": "blur",
}


def parse_args() -> argparse.Namespace:
    # Citim argumentele date in terminal.
    # Exemplu:
    # mpiexec -n 4 python3 main.py input.jpg output.jpg blur --kernel 7
    parser = argparse.ArgumentParser(
        description="Proceseaza o imagine in paralel folosind MPI."
    )

    parser.add_argument("input", help="Calea catre imaginea de intrare.")
    parser.add_argument("output", help="Calea catre imaginea de iesire.")
    parser.add_argument("operation", help="Operatia aplicata pe imagine.")

    parser.add_argument(
        "--kernel",
        type=int,
        default=5,
        help="Dimensiunea kernelului pentru blur.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=127,
        help="Pragul folosit la threshold.",
    )
    parser.add_argument(
        "--low",
        type=int,
        default=100,
        help="Pragul mic pentru Canny.",
    )
    parser.add_argument(
        "--high",
        type=int,
        default=200,
        help="Pragul mare pentru Canny.",
    )

    args = parser.parse_args()

    # Verificam si normalizam operatia aleasa.
    args.operation = normalize_operation(args.operation)
    return args


def normalize_operation(operation: str) -> str:
    # Trecem totul la litere mici si corectam typo-uri comune.
    normalized = OPERATION_ALIASES.get(operation.lower(), operation.lower())

    # Daca operatia nu exista, oprim programul cu un mesaj clar.
    if normalized not in VALID_OPERATIONS:
        options = ", ".join(sorted(VALID_OPERATIONS))
        raise ValueError(
            f"Operatie invalida: {operation}. Alege una dintre: {options}"
        )

    return normalized


def normalize_kernel(kernel: int) -> int:
    # Pentru blur, kernel-ul trebuie sa fie pozitiv si impar.
    # Daca utilizatorul da 6, il transformam in 7.
    if kernel < 1:
        return 1
    if kernel % 2 == 0:
        return kernel + 1
    return kernel


def halo_size(operation: str, kernel: int) -> int:
    # Unele filtre au nevoie de vecini.
    # Asta inseamna ca fiecare bucata de imagine primeste
    # cateva linii extra sus si jos.
    if operation == "blur":
        return normalize_kernel(kernel) // 2
    if operation == "canny":
        return 1
    return 0


def split_image_with_halo(
    image: np.ndarray, num_processes: int, halo: int
) -> list[dict[str, np.ndarray | int]]:
    # Impartim imaginea pe orizontala.
    # Fiecare proces va primi un numar de linii.
    height = image.shape[0]

    # base = cate linii primeste fiecare proces minim.
    # extra = cate procese mai primesc inca o linie in plus.
    base, extra = divmod(height, num_processes)

    chunks_for_processes: list[dict[str, np.ndarray | int]] = []
    start_row = 0

    for process_index in range(num_processes):
        rows_for_this_process = base + (1 if process_index < extra else 0)
        end_row = start_row + rows_for_this_process

        # Adaugam halo sus si jos, fara sa iesim din imagine.
        halo_start = max(0, start_row - halo)
        halo_end = min(height, end_row + halo)

        chunks_for_processes.append(
            {
                # Bucata efectiva trimisa procesului.
                "chunk": image[halo_start:halo_end].copy(),

                # Cate linii extra trebuie taiate dupa procesare.
                "trim_top": start_row - halo_start,
                "trim_bottom": halo_end - end_row,
            }
        )

        start_row = end_row

    return chunks_for_processes


def to_gray(image: np.ndarray) -> np.ndarray:
    # Daca este deja grayscale, nu mai convertim.
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def process_chunk(chunk: np.ndarray, args: argparse.Namespace) -> np.ndarray:
    # Aici se aplica operatia ceruta pe bucata locala.
    operation = args.operation

    if operation == "grayscale":
        return to_gray(chunk)

    if operation == "blur":
        kernel = normalize_kernel(args.kernel)
        return cv2.GaussianBlur(chunk, (kernel, kernel), 0)

    if operation == "canny":
        # Canny merge pe grayscale.
        gray = to_gray(chunk)
        return cv2.Canny(gray, args.low, args.high)

    if operation == "invert":
        # Inversam culorile imaginii.
        return cv2.bitwise_not(chunk)

    if operation == "threshold":
        # Facem imaginea alb-negru in functie de prag.
        gray = to_gray(chunk)
        _, binary = cv2.threshold(gray, args.threshold, 255, cv2.THRESH_BINARY)
        return binary

    raise ValueError(f"Operatie necunoscuta: {operation}")


def trim_halo(processed_chunk: np.ndarray, trim_top: int, trim_bottom: int) -> np.ndarray:
    # Taiem liniile extra care au fost folosite doar pentru calcul.
    start = trim_top
    end = (
        processed_chunk.shape[0] - trim_bottom
        if trim_bottom > 0
        else processed_chunk.shape[0]
    )
    return processed_chunk[start:end]


def save_result(path: str, image: np.ndarray) -> None:
    # Salvam imaginea finala pe disk.
    saved_ok = cv2.imwrite(path, image)
    if not saved_ok:
        raise ValueError(f"Nu am putut salva imaginea in: {path}")


def main() -> None:
    # COMM_WORLD = toate procesele pornite cu mpiexec.
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # args va exista initial doar pe procesul 0.
    args = None

    # Aici vom pune bucata trimisa fiecarui proces.
    local_data = None

    # Daca apare o eroare pe procesul 0, o trimitem la toate procesele.
    metadata = {"error": None}

    if rank == 0:
        try:
            # Doar procesul 0 citeste argumentele si imaginea originala.
            args = parse_args()

            if not os.path.exists(args.input):
                raise FileNotFoundError(
                    f"Fisierul de intrare nu exista: {args.input}. "
                    f"Rulezi din folderul: {os.getcwd()}"
                )

            source_image = cv2.imread(args.input, cv2.IMREAD_COLOR)
            if source_image is None:
                raise ValueError(
                    f"Nu am putut citi imaginea: {args.input}. "
                    "Verifica extensia, calea si daca fisierul este valid."
                )

            # Calculam cate linii extra trebuie trimise la margini.
            halo = halo_size(args.operation, args.kernel)

            # Impartim imaginea in bucati pentru toate procesele.
            local_data = split_image_with_halo(source_image, size, halo)
        except Exception as exc:  # pragma: no cover - pentru rulare MPI
            metadata["error"] = str(exc)

            # Punem cate un None pentru fiecare proces,
            # ca scatter sa aiba totusi ceva de trimis.
            local_data = [None] * size

    # Toate procesele afla daca a aparut o eroare.
    metadata = comm.bcast(metadata, root=0)

    # Toate procesele primesc aceleasi argumente.
    args = comm.bcast(args, root=0)

    if metadata["error"] is not None:
        if rank == 0:
            print(f"Eroare: {metadata['error']}", file=sys.stderr)
        sys.exit(1)

    # Fiecare proces primeste bucata lui de imagine.
    local_data = comm.scatter(local_data, root=0)
    local_chunk = local_data["chunk"]
    trim_top = int(local_data["trim_top"])
    trim_bottom = int(local_data["trim_bottom"])

    # Fiecare proces lucreaza local pe bucata lui.
    processed_chunk = process_chunk(local_chunk, args)

    # Eliminam halo-ul, pentru ca nu trebuie pastrat in rezultatul final.
    processed_chunk = trim_halo(processed_chunk, trim_top, trim_bottom)

    # Trimitem bucatile procesate inapoi la procesul 0.
    gathered_chunks = comm.gather(processed_chunk, root=0)

    if rank == 0:
        # Reconstruim imaginea finala lipind bucatile una sub alta.
        final_image = np.vstack(gathered_chunks)
        save_result(args.output, final_image)
        print(
            f"Gata. Operatia '{args.operation}' a fost aplicata cu {size} procese."
        )


if __name__ == "__main__":
    main()
