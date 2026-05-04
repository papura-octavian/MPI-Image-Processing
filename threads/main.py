from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np

VALID_OPERATIONS = {"grayscale", "blur", "canny", "invert", "threshold"}

OPERATION_ALIASES = {
    "ivert": "invert",
    "inverrt": "invert",
    "invers": "invert",
    "gayscale": "grayscale",
    "bklur": "blur",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Proceseaza o imagine in paralel folosind threads."
    )

    parser.add_argument("input", help="Calea catre imaginea de intrare.")
    parser.add_argument("output", help="Calea catre imaginea de iesire.")
    parser.add_argument("operation", help="Operatia aplicata pe imagine.")

    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Numarul de thread-uri folosite.",
    )
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
    args.operation = normalize_operation(args.operation)
    return args


def normalize_operation(operation: str) -> str:
    normalized = OPERATION_ALIASES.get(operation.lower(), operation.lower())

    if normalized not in VALID_OPERATIONS:
        options = ", ".join(sorted(VALID_OPERATIONS))
        raise ValueError(
            f"Operatie invalida: {operation}. Alege una dintre: {options}"
        )

    return normalized


def normalize_kernel(kernel: int) -> int:
    if kernel < 1:
        return 1
    if kernel % 2 == 0:
        return kernel + 1
    return kernel


def halo_size(operation: str, kernel: int) -> int:
    if operation == "blur":
        return normalize_kernel(kernel) // 2
    if operation == "canny":
        return 1
    return 0


def split_image_with_halo(
    image: np.ndarray, num_threads: int, halo: int
) -> list[dict[str, np.ndarray | int]]:
    height = image.shape[0]
    base, extra = divmod(height, num_threads)

    chunks: list[dict[str, np.ndarray | int]] = []
    start_row = 0

    for i in range(num_threads):
        rows = base + (1 if i < extra else 0)
        end_row = start_row + rows

        halo_start = max(0, start_row - halo)
        halo_end = min(height, end_row + halo)

        chunks.append(
            {
                "index": i,
                "chunk": image[halo_start:halo_end].copy(),
                "trim_top": start_row - halo_start,
                "trim_bottom": halo_end - end_row,
            }
        )

        start_row = end_row

    return chunks


def to_gray(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def process_chunk(chunk: np.ndarray, args: argparse.Namespace) -> np.ndarray:
    operation = args.operation

    if operation == "grayscale":
        return to_gray(chunk)

    if operation == "blur":
        kernel = normalize_kernel(args.kernel)
        return cv2.GaussianBlur(chunk, (kernel, kernel), 0)

    if operation == "canny":
        gray = to_gray(chunk)
        return cv2.Canny(gray, args.low, args.high)

    if operation == "invert":
        return cv2.bitwise_not(chunk)

    if operation == "threshold":
        gray = to_gray(chunk)
        _, binary = cv2.threshold(gray, args.threshold, 255, cv2.THRESH_BINARY)
        return binary

    raise ValueError(f"Operatie necunoscuta: {operation}")


def trim_halo(processed: np.ndarray, trim_top: int, trim_bottom: int) -> np.ndarray:
    start = trim_top
    end = processed.shape[0] - trim_bottom if trim_bottom > 0 else processed.shape[0]
    return processed[start:end]


def process_chunk_task(chunk_data: dict, args: argparse.Namespace) -> tuple[int, np.ndarray]:
    index = chunk_data["index"]
    chunk = chunk_data["chunk"]
    trim_top = int(chunk_data["trim_top"])
    trim_bottom = int(chunk_data["trim_bottom"])

    processed = process_chunk(chunk, args)
    trimmed = trim_halo(processed, trim_top, trim_bottom)
    return index, trimmed


def save_result(path: str, image: np.ndarray) -> None:
    saved_ok = cv2.imwrite(path, image)
    if not saved_ok:
        raise ValueError(f"Nu am putut salva imaginea in: {path}")


def main() -> None:
    args = parse_args()

    if not os.path.exists(args.input):
        print(
            f"Eroare: Fisierul de intrare nu exista: {args.input}. "
            f"Rulezi din folderul: {os.getcwd()}",
            file=sys.stderr,
        )
        sys.exit(1)

    source_image = cv2.imread(args.input, cv2.IMREAD_COLOR)
    if source_image is None:
        print(
            f"Eroare: Nu am putut citi imaginea: {args.input}. "
            "Verifica extensia, calea si daca fisierul este valid.",
            file=sys.stderr,
        )
        sys.exit(1)

    num_threads = max(1, args.threads)
    halo = halo_size(args.operation, args.kernel)
    chunks = split_image_with_halo(source_image, num_threads, halo)

    results: list[tuple[int, np.ndarray]] = []

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {
            executor.submit(process_chunk_task, chunk_data, args): chunk_data["index"]
            for chunk_data in chunks
        }
        for future in as_completed(futures):
            results.append(future.result())

    # Sortam dupa index ca as_completed nu garanteaza ordinea.
    results.sort(key=lambda x: x[0])
    ordered_chunks = [chunk for _, chunk in results]

    final_image = np.vstack(ordered_chunks)
    save_result(args.output, final_image)
    print(
        f"Gata. Operatia '{args.operation}' a fost aplicata cu {num_threads} thread-uri."
    )


if __name__ == "__main__":
    main()
