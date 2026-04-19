"""À lancer avec le MÊME Python que manage.py runserver : vérifie librosa / torch / transformers."""

from __future__ import annotations

import sys


def main() -> None:
    print("Python :", sys.executable)
    try:
        import librosa  # noqa: F401

        print("librosa : OK")
    except ImportError as e:
        print("librosa : MANQUANT ->", e)
        sys.exit(1)
    try:
        import torch  # noqa: F401

        print("torch : OK")
    except ImportError as e:
        print("torch : MANQUANT ->", e)
        sys.exit(1)
    try:
        import transformers  # noqa: F401

        print("transformers : OK")
    except ImportError as e:
        print("transformers : MANQUANT ->", e)
        sys.exit(1)
    print("Tout est pret pour l'analyse vocale.")


if __name__ == "__main__":
    main()
