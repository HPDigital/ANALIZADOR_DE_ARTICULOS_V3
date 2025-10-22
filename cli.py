import argparse
import os
import sys
from typing import List

from analyzer import find_pdfs, load_openai_client, process_pdf


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analizador de Artículos (CLI)")
    p.add_argument("--in", dest="input_path", required=True, help="Archivo PDF o carpeta")
    p.add_argument("--out", dest="out_dir", default=None, help="Carpeta de salida")
    p.add_argument("--model", dest="model", default="gpt-4o-2024-08-06")
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--max-output-tokens", type=int, default=1200)
    p.add_argument("--api-key", dest="api_key", default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()

    target = args.input_path
    out_dir = args.out_dir
    api_key = args.api_key
    model = args.model
    temperature = args.temperature
    max_output_tokens = args.max_output_tokens

    try:
        client = load_openai_client(api_key)
    except Exception as e:
        print(f"[ERROR] OpenAI: {e}")
        return 2

    paths: List[str] = []
    if os.path.isdir(target):
        paths = find_pdfs(target, recursive=True)
    elif os.path.isfile(target) and target.lower().endswith(".pdf"):
        paths = [target]
    else:
        print("[ERROR] Ruta no válida. Use un PDF o una carpeta con PDFs.")
        return 1

    if not paths:
        print("[WARN] No se encontraron PDFs.")
        return 0

    ok, fail = 0, 0
    for i, pdf in enumerate(paths, 1):
        print(f"[{i}/{len(paths)}] Procesando: {pdf}")
        try:
            out_path = process_pdf(
                pdf,
                client,
                out_dir,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            print(f"  ✓ Guardado: {out_path}")
            ok += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            fail += 1

    print(f"Completado. Exitosos: {ok}, Fallidos: {fail}")
    return 0 if fail == 0 else 3


if __name__ == "__main__":
    sys.exit(main())

