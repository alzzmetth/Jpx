"""
JPX Expression Evaluator
Handles evaluation of expressions, conditions, and values.
"""

import re

class EvalParser:
    """Evaluator for JPX expressions."""
    
    # Comparison operators
    COMPARISON_OPS = {
        '==': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
        '<': lambda a, b: a < b,
        '<=': lambda a, b: a <= b,
        '>': lambda a, b: a > b,
        '>=': lambda a, b: a >= b,
    }
    
    def __init__(self, interpreter):
        self.interp = interpreter
        self.errors = interpreter.errors
        self.vars = interpreter.vars
        self.modules = interpreter.modules
    
    def evaluate_condition(self, condition):
        """
        Evaluate an if condition with && and || support.
        
        Args:
            condition: Condition string (e.g., '$x > 5 && $y < 10')
        
        Returns:
            Boolean result
        """
        condition = condition.strip()
        
        # Handle && (AND)
        if '&&' in condition:
            for part in condition.split('&&'):
                if not self._evaluate_simple(part.strip()):
                    return False
            return True
        
        # Handle || (OR)
        if '||' in condition:
            for part in condition.split('||'):
                if self._evaluate_simple(part.strip()):
                    return True
            return False
        
        # Simple condition
        return self._evaluate_simple(condition)
    
    def _evaluate_simple(self, expr):
        """Evaluate a simple condition without && or ||."""
        expr = expr.strip()
        
        # Find comparison operator
        for op in self.COMPARISON_OPS.keys():
            if op in expr:
                left, right = expr.split(op, 1)
                left_val = self.get_value(left.strip())
                right_val = self.get_value(right.strip())
                
                # Handle type mismatches
                if left_val['type'] != right_val['type']:
                    # Try to convert string to number if possible
                    if left_val['type'] in ('integer', 'float') and right_val['type'] == 'string':
                        try:
                            right_val['value'] = float(right_val['value'])
                            right_val['type'] = 'float'
                        except ValueError:
                            self.errors.runtime_error(f"Cannot compare number with non-numeric string '{right_val['value']}'")
                    elif left_val['type'] == 'string' and right_val['type'] in ('integer', 'float'):
                        try:
                            left_val['value'] = float(left_val['value'])
                            left_val['type'] = 'float'
                        except ValueError:
                            self.errors.runtime_error(f"Cannot compare non-numeric string '{left_val['value']}' with number")
                    else:
                        self.errors.runtime_error(f"Cannot compare {left_val['type']} with {right_val['type']}")
                
                # Perform comparison
                return self.COMPARISON_OPS[op](left_val['value'], right_val['value'])
        
        # No operator found, evaluate as boolean
        val = self.get_value(expr)
        return bool(val['value'])
    
    def get_value(self, token):
        """
        Get value from token (variable, literal, module attribute, function call).
        
        Args:
            token: Token string (e.g., '$x', '5', 'os.get("HOME")', 'Colors.RED')
        
        Returns:
            Dictionary with 'value' and 'type'
        """
        token = token.strip()
        
        # Check for function call: module.function(args)
        if '.' in token and '(' in token and ')' in token:
            match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', token)
            if match:
                mod_name, func_name, args_str = match.groups()
                if mod_name in self.modules:
                    module = self.modules[mod_name]
                    if func_name in module:
                        func = module[func_name]
                        args = self._parse_args(args_str)
                        # Call function with interpreter as first parameter
                        result = func(self.interp, *args)
                        return self._to_value(result)
        
        # Handle dot access for module attributes (e.g., Colors.RED)
        if '.' in token and not (token.startswith('"') or token.startswith("'")):
            parts = token.split('.')
            if parts[0] in self.modules:
                obj = self.modules[parts[0]]
                for attr in parts[1:]:
                    if attr in obj:
                        obj = obj[attr]
                    else:
                        break
                else:
                    return self._to_value(obj)
        
        # Variable reference
        if token.startswith('$'):
            name = token[1:]
            if name in self.vars:
                return self.vars[name]
            self.errors.runtime_error(f"Undefined variable: {token}")
        
        # Number
        try:
            if token.replace('.', '', 1).replace('-', '', 1).isdigit():
                if '.' in token:
                    return {'value': float(token), 'type': 'float'}
                return {'value': int(token), 'type': 'integer'}
        except:
            pass
        
        # Quoted string
        if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
            return {'value': token[1:-1], 'type': 'string'}
        
        # Boolean
        if token == 'true':
            return {'value': True, 'type': 'boolean'}
        if token == 'false':
            return {'value': False, 'type': 'boolean'}
        
        # Plain string
        return {'value': token, 'type': 'string'}
    
    def _parse_args(self, args_str):
        """Parse argument string, handle quotes and commas."""
        args = []
        current = []
        in_string = False
        quote = None
        
        for ch in args_str:
            if ch in ('"', "'"):
                if not in_string:
                    in_string = True
                    quote = ch
                elif quote == ch:
                    in_string = False
                current.append(ch)
            elif ch == ',' and not in_string:
                arg = ''.join(current).strip()
                if arg:
                    val = self.get_value(arg)
                    args.append(val['value'])
                current = []
            else:
                current.append(ch)
        
        last = ''.join(current).strip()
        if last:
            val = self.get_value(last)
            args.append(val['value'])
        
        return args
    
    def _to_value(self, value):
        """Convert Python value to JPX value dictionary."""
        if isinstance(value, str):
            return {'value': value, 'type': 'string'}
        elif isinstance(value, int):
            return {'value': value, 'type': 'integer'}
        elif isinstance(value, float):
            return {'value': value, 'type': 'float'}
        elif isinstance(value, bool):
            return {'value': value, 'type': 'boolean'}
        else:
            return {'value': str(value), 'type': 'string'}
    
    def interpolate(self, text):
        """
        Replace $variable and $module.attribute in text.
        
        Args:
            text: String containing $ references
        
        Returns:
            String with references replaced
        """
        def repl(match):
            full_ref = match.group(0)[1:]  # remove $
            
            # Handle dot notation (e.g., c.GREEN)
            if '.' in full_ref:
                parts = full_ref.split('.')
                if parts[0] in self.modules:
                    obj = self.modules[parts[0]]
                    for attr in parts[1:]:
                        if attr in obj:
                            obj = obj[attr]
                        else:
                            self.errors.runtime_error(f"Undefined attribute: {full_ref}")
                    return str(obj)
                else:
                    self.errors.runtime_error(f"Undefined module: {parts[0]}")
            
            # Regular variable
            if full_ref in self.vars:
                return str(self.vars[full_ref]['value'])
            self.errors.runtime_error(f"Undefined variable: ${full_ref}")
        
        return re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_.]*)', repl, text)
