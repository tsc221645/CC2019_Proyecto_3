from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple, List, Any
import yaml
from collections import defaultdict

Move = str  #

@dataclass
class Transition:
    next_state: str
    write_symbol: str
    move: Move

def _normalize_transitions(raw: Dict[str, Any]) -> Dict[Tuple[str, str], Transition]:

    out: Dict[Tuple[str, str], Transition] = {}

    def _add(kstate: str, ksym: str, arr: List[str]):
        if len(arr) != 3:
            raise ValueError(f"Transición mal formada para ({kstate}, {ksym}): {arr}")
        nxt, w, m = arr
        if m not in ("L", "R", "N"):
            raise ValueError(f"Movimiento inválido {m} en ({kstate}, {ksym})")
        out[(kstate, ksym)] = Transition(nxt, w, m)

    if any(isinstance(v, dict) for v in raw.values()):
        for st, inner in raw.items():
            if not isinstance(inner, dict):
                raise ValueError("Formato de transiciones inconsistente.")
            for sym, arr in inner.items():
                _add(st, str(sym), arr)
        return out

    for k, arr in raw.items():
        s = str(k).strip().replace('"', "'")
        if not (s.startswith("(") and s.endswith(")")):
            raise ValueError(f"Clave de transición inválida: {k}")
        inside = s[1:-1]
        parts = [p.strip() for p in inside.split(",")]
        if len(parts) != 2:
            raise ValueError(f"Clave de transición inválida: {k}")
        st, sy = parts
        if st.startswith("'") and st.endswith("'"): st = st[1:-1]
        if sy.startswith("'") and sy.endswith("'"): sy = sy[1:-1]
        _add(st, sy, arr)
    return out

class TuringMachine:
    
    def __init__(self, description: Dict[str, Any]):
        self.states: List[str] = description["states"]
        self.input_alphabet: List[str] = description["input_alphabet"]
        self.tape_alphabet: List[str] = description["tape_alphabet"]
        self.blank: str = description["blank_symbol"]
        self.initial_state: str = description["initial_state"]
        self.final_states: List[str] = description["final_states"]
        self.inputs: List[str] = description.get("inputs", [])
        self.max_steps: int = description.get("max_steps", 10000)

        if not set(self.input_alphabet).issubset(set(self.tape_alphabet)):
            raise ValueError("El alfabeto de cinta debe contener al alfabeto de entrada.")
        if self.blank not in self.tape_alphabet:
            raise ValueError("El símbolo blank debe pertenecer al alfabeto de cinta.")

        self.transitions: Dict[Tuple[str, str], Transition] = _normalize_transitions(
            description["transitions"]
        )

        self._tape = defaultdict(lambda: self.blank)  
        self._head = 0
        self._state = self.initial_state
        self._steps = 0
        self._id_log: List[str] = []

    def reset(self, input_string: str) -> None:
        self._tape = defaultdict(lambda: self.blank)
        for i, ch in enumerate(input_string):
            if ch not in self.tape_alphabet:
                raise ValueError(f"Símbolo de entrada fuera del alfabeto de cinta: {ch}")
            self._tape[i] = ch
        self._head = 0
        self._state = self.initial_state
        self._steps = 0
        self._id_log = []
        self._id_log.append(self.current_id_string())

    def is_accepting(self) -> bool:
        return self._state in self.final_states

    def step(self) -> str:
        if self.is_accepting():
            return "accepted"
        if self._steps >= self.max_steps:
            return "max_steps"

        sym = self._tape[self._head]
        key = (self._state, sym)
        if key not in self.transitions:
            return "accepted" if self.is_accepting() else "rejected"

        tr = self.transitions[key]
        self._tape[self._head] = tr.write_symbol
        if tr.move == "R":
            self._head += 1
        elif tr.move == "L":
            self._head -= 1
        elif tr.move == "N":
            pass
        else:
            raise ValueError(f"Movimiento inválido: {tr.move}")

        self._state = tr.next_state
        self._steps += 1
        self._id_log.append(self.current_id_string())

        if self.is_accepting():
            return "accepted"
        if self._steps >= self.max_steps:
            return "max_steps"
        return "running"

    def run_all(self) -> str:
        while True:
            status = self.step()
            if status in ("accepted", "rejected", "max_steps"):
                return status

    def current_window(self, radius: int = 40) -> tuple[str, int]:
        if len(self._tape) == 0:
            return self.blank, 0
        min_i = min(self._tape.keys())
        max_i = max(self._tape.keys())
        left = min(min_i, self._head - radius)
        right = max(max_i, self._head + radius)
        chars = [self._tape[i] for i in range(left, right + 1)]
        head_pos = self._head - left
        return "".join(chars), head_pos

    def current_id_string(self) -> str:
        tape_str, head_local = self.current_window(radius=40)
        return f"({self._state}, {tape_str}, {head_local})"

    def export_id_log(self) -> str:
        return "\n".join(self._id_log)

   
    @staticmethod
    def load_from_yaml(path: str) -> "TuringMachine":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return TuringMachine(data)
