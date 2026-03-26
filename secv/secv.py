from __future__ import annotations

import argparse
import os

import cv2
import numpy as np

# Lista cu operatiile pe care programul le accepta.
VALID_OPERATIONS = {"grayscale", "blur", "canny", "invert", "threshold"}


def parse_args() -> argparse.Namespace:
    # Citim argumentele date in terminal.
    # Exemplu:
    # python3 secv.py images/input.jpg images/output.jpg blur --kernel 7
    operations_text = ", ".join(sorted(VALID_OPERATIONS))
    parser = argparse.ArgumentParser(
        description=(
            "Proceseaza o imagine in mod secvential.\n"
            f"Operatii disponibile: {operations_text}."
        ),
        epilog=(
            "Exemple:\n"
            "  python3 secv.py images/input.jpg images/out.jpg grayscale\n"
            "  python3 secv.py images/input.jpg images/out.jpg blur --kernel 7\n"
            "  python3 secv.py images/input.jpg images/out.jpg canny --low 50 --high 150\n"
            "  python3 secv.py images/input.jpg images/out.jpg invert\n"
            "  python3 secv.py images/input.jpg images/out.jpg threshold --threshold 120"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("input", help="Calea catre imaginea de intrare.")
    parser.add_argument("output", help="Calea catre imaginea de iesire.")
    parser.add_argument(
        "operation",
        help=f"Operatia aplicata pe imagine. Alege dintre: {operations_text}.",
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
    # Transformam textul in litere mici si verificam operatia.
    operation = operation.lower()

    if operation not in VALID_OPERATIONS:
        options = ", ".join(sorted(VALID_OPERATIONS))
        raise ValueError(f"Operatie invalida: {operation}. Alege una dintre: {options}")

    return operation


def normalize_kernel(kernel: int) -> int:
    # Pentru blur, kernelul trebuie sa fie pozitiv si impar.
    if kernel < 1:
        return 1
    if kernel % 2 == 0:
        return kernel + 1
    return kernel


def to_gray(image: np.ndarray) -> np.ndarray:
    # Daca imaginea este deja grayscale, o lasam asa.
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def process_image(image: np.ndarray, args: argparse.Namespace) -> np.ndarray:
    # Aplicam operatia aleasa pe intreaga imagine.
    if args.operation == "grayscale":
        return to_gray(image)

    if args.operation == "blur":
        kernel = normalize_kernel(args.kernel)
        return cv2.GaussianBlur(image, (kernel, kernel), 0)

    if args.operation == "canny":
        gray = to_gray(image)
        return cv2.Canny(gray, args.low, args.high)

    if args.operation == "invert":
        return cv2.bitwise_not(image)

    if args.operation == "threshold":
        gray = to_gray(image)
        _, binary = cv2.threshold(gray, args.threshold, 255, cv2.THRESH_BINARY)
        return binary

    raise ValueError(f"Operatie necunoscuta: {args.operation}")


def load_image(path: str) -> np.ndarray:
    # Verificam daca fisierul exista si il citim.
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fisierul de intrare nu exista: {path}")

    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Nu am putut citi imaginea: {path}")

    return image


def save_image(path: str, image: np.ndarray) -> None:
    # Salvam rezultatul final.
    saved_ok = cv2.imwrite(path, image)
    if not saved_ok:
        raise ValueError(f"Nu am putut salva imaginea in: {path}")


def main() -> None:
    # Pasii programului sunt simpli:
    # 1. citim argumentele
    # 2. citim imaginea
    # 3. aplicam operatia
    # 4. salvam rezultatul
    args = parse_args()
    image = load_image(args.input)
    result = process_image(image, args)
    save_image(args.output, result)

    print(f"Gata. Operatia '{args.operation}' a fost aplicata secvential.")


if __name__ == "__main__":
    main()
