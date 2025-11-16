from typing import List, Dict, Any, Optional
import yaml

BLANK = None  # Representación interna del blank

class Transition:
    def __init__(self, params: Dict[str, Any], output: Dict[str, Any]):
        # Params
        self.initial_state = str(params.get('initial_state'))
        # mem_cache_value may be None (wildcard) or a string
        self.mem_cache_value = params.get('mem_cache_value')
        # empty tape_input in YAML -> None
        self.tape_input = params.get('tape_input')
        # Output
        self.final_state = str(output.get('final_state'))
        self.out_mem_cache = output.get('mem_cache_value')
        self.tape_output = output.get('tape_output')
        self.tape_disp = output.get('tape_displacement')  # 'L', 'R' or 'S'

    def matches(self, state: str, tape_symbol, mem_cache) -> bool:
        if self.initial_state != state:
            return False
        if self.tape_input != tape_symbol:
            return False
        if self.mem_cache_value is None:
            return True
        return self.mem_cache_value == mem_cache

    def __repr__(self):
        return (f"Transition({self.initial_state}, {self.tape_input}, mc={self.mem_cache_value} -> "
                f"{self.final_state}, out={self.tape_output}, disp={self.tape_disp}, mc_out={self.out_mem_cache})")

class TuringMachine:
    def __init__(self, states: List[str], initial: str, finals: List[str],
                 alphabet: List[str], tape_alphabet: List[Any], transitions: List[Transition],
                 max_steps: int = 2000):
        self.states = states
        self.initial = str(initial)
        self.finals = set(map(str, finals))
        self.alphabet = alphabet
        self.tape_alphabet = tape_alphabet
        self.transitions = transitions
        self.max_steps = max_steps

        # runtime
        self.reset()

    def reset(self):
        self.tape = []          # ;ista de simbolos
        self.head = 0
        self.state = self.initial
        self.mem_cache = None
        self.ids = []  # hisotorial

    @staticmethod
    def _symbol_to_str(s):
        return '_' if s is None else str(s)

    def load_input(self, input_str: str, separator_char: Optional[str] = None):
        #Prepara la cinta a partir de input_str (string sin separador si separator_char None).
        self.tape = [c for c in input_str]
        if len(self.tape) == 0:
            self.tape = [BLANK]
        self.head = 0
        self.state = self.initial
        self.mem_cache = None
        self.ids = []
        self._record_id()

    def _read(self):
        if self.head < 0 or self.head >= len(self.tape):
            return BLANK
        val = self.tape[self.head]
        if val == '':
            return BLANK
        return val

    def _write(self, sym):
        if self.head < 0:
            # expand to the left
            extra = [BLANK] * (abs(self.head))
            self.tape = extra + self.tape
            self.head += len(extra)
        if self.head >= len(self.tape):
            self.tape += [BLANK] * (self.head - len(self.tape) + 1)
        self.tape[self.head] = sym

    def _record_id(self):
        tape_display = ''.join(self._symbol_to_str(s) for s in self.tape)
        display_chars = list(tape_display)
        idx = self.head
        if idx < 0:
            display_chars = ['_'] * (abs(idx)) + display_chars
            idx = 0
        if idx >= len(display_chars):
            display_chars += ['_'] * (idx - len(display_chars) + 1)
        display_chars[idx] = f'[{display_chars[idx]}]'
        tape_with_head = ''.join(display_chars)
        id_str = f"ID: state={self.state} mem_cache={self._symbol_to_str(self.mem_cache)} tape={tape_with_head}"
        self.ids.append(id_str)

    def step(self) -> bool:
        #Ejecuta un paso de la MT. Retorna True si aplicó una transición, False si no existe transición aplicable.
        current_sym = self._read()
        applicable = None
        for t in self.transitions:
            if t.matches(self.state, current_sym, self.mem_cache):
                applicable = t
                break
        if applicable is None:
            return False
        out_sym = applicable.tape_output
        self._write(out_sym)
        self.mem_cache = applicable.out_mem_cache
        if applicable.tape_disp is not None:
            disp = applicable.tape_disp.upper()
            if disp == 'L':
                self.head -= 1
            elif disp == 'R':
                self.head += 1
            elif disp == 'S':
                pass
            else:
                pass
        self.state = applicable.final_state
        self._record_id()
        return True

    def run(self, max_steps: Optional[int] = None) -> Dict[str, Any]:
        if max_steps is None:
            max_steps = self.max_steps
        steps = 0
        while steps < max_steps:
            if self.state in self.finals:
                return {'accepted': True, 'steps': steps, 'ids': self.ids}
            applied = self.step()
            if not applied:
                # no transition applicable
                return {'accepted': self.state in self.finals, 'steps': steps, 'ids': self.ids}
            steps += 1
        # reached step limit
        return {'accepted': self.state in self.finals, 'steps': steps, 'ids': self.ids, 'max_steps_hit': True}

    @classmethod
    def from_yaml(cls, data: Dict[str, Any]) -> 'TuringMachine':
        q_states = data.get('q_states', {})
        q_list = q_states.get('q_list', [])
        initial = q_states.get('initial')
        final = q_states.get('final')
        finals = [final] if isinstance(final, (str, int)) else final or []
        alphabet = data.get('alphabet', [])
        tape_alphabet = data.get('tape_alphabet', [])
        
        # parse transitions
        raw_delta = data.get('delta', [])
        transitions = []
        for entry in raw_delta:
            params = entry.get('params', {})
            output = entry.get('output', {})
            
            #Normalizar mem_cache_value también
            if 'mem_cache_value' in params and params['mem_cache_value'] == '':
                params['mem_cache_value'] = None
            if 'mem_cache_value' in output and output['mem_cache_value'] == '':
                output['mem_cache_value'] = None
                
            # Normalizar espacios en blanco a NONE
            if 'tape_input' in params and params['tape_input'] == '':
                params['tape_input'] = None
            if 'tape_output' in output and output['tape_output'] == '':
                output['tape_output'] = None
                
            transitions.append(Transition(params, output))
        
        return cls(states=q_list, initial=initial, finals=finals,
                alphabet=alphabet, tape_alphabet=tape_alphabet,
                transitions=transitions)

def load_yaml_file(path: str) -> Dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
