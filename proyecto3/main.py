import argparse
from turing_machine import TuringMachine

def main():
    parser = argparse.ArgumentParser(description="Simulador de MT (una cinta) - CLI")
    parser.add_argument("yaml", help="Ruta al archivo YAML de la MT")
    parser.add_argument("--ids-out", help="Si se indica, exporta las IDs a este .txt por cada cadena (agrega sufijo).", default=None)
    args = parser.parse_args()

    tm = TuringMachine.load_from_yaml(args.yaml)

    if not tm.inputs:
        print("No hay 'inputs' en el YAML. Agrega una lista de cadenas bajo 'inputs'.")
        return

    for idx, w in enumerate(tm.inputs, 1):
        print(f"\nCadena #{idx}: {w}")
        tm.reset(w)
        status = tm.run_all()

        print("\nIDs:")
        print(tm.export_id_log())

        if status == "accepted":
            print("\nResultado: ACEPTADA ")
        elif status == "rejected":
            print("\nResultado: RECHAZADA ")
        else:
            print("\nResultado: Límite de pasos alcanzado (trátalo como rechazo)")

        # Exportar IDs (opcional)
        if args.ids_out:
            path = f"{args.ids_out.rstrip('.txt')}_cadena{idx}.txt"
            with open(path, "w", encoding="utf-8") as f:
                f.write(tm.export_id_log() + "\n")
                f.write({
                    "accepted": "ACEPTADA ",
                    "rejected": "RECHAZADA ",
                    "max_steps": "Límite de pasos "
                }[status])
            print(f"IDs exportadas a: {path}")

if __name__ == "__main__":
    main()
