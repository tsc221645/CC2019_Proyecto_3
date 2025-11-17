

#Uso:
#    python main.py example.yaml

#Imprime las IDs (descripciones instantáneas) paso a paso y al final muestra si la cadena fue aceptada.
import sys
from pathlib import Path
import yaml
from turing_machine import TuringMachine, load_yaml_file, BLANK

def parse_simulation_string(s: str):
    # El separador que el usuario use para dividir partes (si existe) se mantiene; 
    # Para nuestras máquinas de ejemplo solo vamos a tomar la cadena tal cual.
    return s

def run_from_file(yaml_path: str):
    data = load_yaml_file(yaml_path)
    tm = TuringMachine.from_yaml(data)
    sim_strings = data.get('simulation_strings', [])
    if not sim_strings:
        print("No hay cadenas en simulation_strings.")
        return
    for idx, s in enumerate(sim_strings):
        inp = parse_simulation_string(s)
        print("="*60)
        print(f"Simulación {idx+1}: input='{s}'")
        tm.reset()
        tm.load_input(inp)
        result = tm.run()
        print(f"Resultado: accepted={result.get('accepted')} steps={result.get('steps')}")
        print("IDs (instantáneas):")
        for idd in result.get('ids', []):
            print(idd)
        if result.get('max_steps_hit'):
            print("ATENCIÓN: se alcanzó el límite máximo de pasos; la ejecución fue detenida.")
    print("="*60)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python main.py <archivo_yaml>")
        sys.exit(1)
    path = sys.argv[1]
    if not Path(path).exists():
        print(f"El archivo {path} no existe.")
        sys.exit(1)
    run_from_file(path)
