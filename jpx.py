#!/usr/bin/env python3
"""
JPX Interpreter dengan Module System
Module bisa akses interpreter via parameter pertama
"""

import sys
import re
import time
import os
import importlib.util

class JPXValue:
    def __init__(self, value):
        self.value = value
        self.type = self._get_type(value)
    
    def _get_type(self, value):
        if isinstance(value, str):
            return 'string'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, bool):
            return 'boolean'
        return 'unknown'
    
    def __str__(self):
        return str(self.value)

class JPXInterpreter:
    def __init__(self):
        self.vars = {}           # global variables
        self.config = {}          # global_entry config
        self.modules = {}         # loaded modules {name: module_dict}
        self.line = 0
        self.file = ""
        self.all_lines = []
        self.current_block = []
        self.lib_path = os.path.join(os.path.dirname(__file__), 'lib')
    
    def typewriter(self, text, speed=None):
        """Built-in typewriter function - bisa dipanggil module"""
        if speed is None:
            speed = float(self.config.get('typewriter', JPXValue(0.05)).value)
        for ch in text:
            print(ch, end='', flush=True)
            time.sleep(speed)
        print()
    
    def error(self, msg, line_num=None, line_text=None):
        print(f"\n╔══════════════════════════════════════════════════════════╗")
        print(f"║                    JPX ERROR                              ║")
        print(f"╚══════════════════════════════════════════════════════════╝")
        if line_num:
            print(f"\n  📍 Line {line_num}: {line_text}")
        print(f"\n  ❌ {msg}\n")
        sys.exit(1)
    
    def run(self, filename):
        self.file = filename
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.all_lines = content.split('\n')
            self.current_block = self.all_lines
            self._execute_block(0)
        except Exception as e:
            self.error(f"File error: {e}")
    
    def _import_module(self, name):
        """Load module from lib/ folder"""
        if name in self.modules:
            return self.modules[name]
        
        module_path = os.path.join(self.lib_path, f"{name}.py")
        if not os.path.exists(module_path):
            self.error(f"Module '{name}' not found in lib/")
        
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Call module init with interpreter
            if hasattr(module, '__init__'):
                module_dict = module.__init__(self)
                self.modules[name] = module_dict
            else:
                # Fallback: export semua fungsi
                module_dict = {}
                for attr in dir(module):
                    if not attr.startswith('_'):
                        module_dict[attr] = getattr(module, attr)
                self.modules[name] = module_dict
            
            return self.modules[name]
        except Exception as e:
            self.error(f"Failed to load module '{name}': {e}")
    
    def _execute_block(self, start_line):
        i = start_line
        block_lines = self.current_block
        
        while i < len(block_lines):
            self.line = i + 1
            raw_line = block_lines[i].rstrip()
            line = raw_line.strip()
            
            if not line or line.startswith('#'):
                i += 1
                continue
            
            if line == '}':
                i += 1
                return i
            
            # IF STATEMENT
            if line.startswith('if '):
                if not line.endswith('{'):
                    self.error("Expected '{' after if", self.line, raw_line)
                
                condition = line[3:-1].strip()
                i += 1
                if_block, i = self._collect_block(i)
                
                old_block = self.current_block
                self.current_block = if_block
                
                if self._eval_condition(condition):
                    self._execute_block(0)
                
                self.current_block = old_block
                
                # Handle else if and else
                while i < len(block_lines):
                    next_line = block_lines[i].strip()
                    if not next_line or next_line.startswith('#'):
                        i += 1
                        continue
                    
                    if next_line.startswith('} else if '):
                        if not next_line.endswith('{'):
                            self.error("Expected '{' after else if", i+1, block_lines[i])
                        condition = next_line[10:-1].strip()
                        i += 1
                        else_if_block, i = self._collect_block(i)
                        
                        self.current_block = else_if_block
                        if self._eval_condition(condition):
                            self._execute_block(0)
                        self.current_block = old_block
                        continue
                    
                    elif next_line == '} else {':
                        i += 1
                        else_block, i = self._collect_block(i)
                        
                        self.current_block = else_block
                        self._execute_block(0)
                        self.current_block = old_block
                        continue
                    
                    else:
                        break
                continue
            
            # EXECUTE STATEMENT
            try:
                statements = self._split_statements(line)
                for stmt in statements:
                    if stmt:
                        self._execute_statement(stmt)
            except Exception as e:
                self.error(str(e), self.line, raw_line)
            
            i += 1
        
        return i
    
    def _collect_block(self, start):
        block = []
        brace_count = 1
        i = start
        block_lines = self.current_block
        
        while i < len(block_lines) and brace_count > 0:
            line = block_lines[i]
            stripped = line.strip()
            
            if not stripped or stripped.startswith('#'):
                block.append(line)
                i += 1
                continue
            
            for ch in stripped:
                if ch == '{':
                    brace_count += 1
                elif ch == '}':
                    brace_count -= 1
            
            if brace_count > 0:
                block.append(line)
            i += 1
        
        if brace_count != 0:
            self.error("Unclosed block", self.line, "")
        
        return block, i
    
    def _split_statements(self, line):
        statements = []
        current = []
        in_string = False
        quote_char = None
        
        for ch in line:
            if ch in ('"', "'"):
                if not in_string:
                    in_string = True
                    quote_char = ch
                elif quote_char == ch:
                    in_string = False
                current.append(ch)
            elif ch == ';' and not in_string:
                stmt = ''.join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
            else:
                current.append(ch)
        
        last = ''.join(current).strip()
        if last:
            statements.append(last)
        
        return statements
    
    def _execute_statement(self, stmt):
        # IMPORT [module]
        if stmt.startswith('[') and stmt.endswith(']'):
            mod = stmt[1:-1]
            self._import_module(mod)
            return
        
        # global [name=value]
        m = re.match(r'^global\s*\[\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+?)\s*\]$', stmt)
        if m:
            name, val = m.groups()
            self.vars[name] = self._parse_value(val)
            return
        
        # global_entry [name=value]
        m = re.match(r'^global_entry\s*\[\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+?)\s*\]$', stmt)
        if m:
            name, val = m.groups()
            val = self._parse_value(val)
            if name == 'typewriter':
                try:
                    float(val.value)
                except:
                    self.error("global_entry [typewriter] must be a number (e.g., 0.05)")
            self.config[name] = val
            return
        
        # print statement (built-in)
        if stmt.startswith('print '):
            text = stmt[6:].strip()
            text = self._parse_string(text)
            text = self._interpolate(text)
            print(text)
            return
        
        # TYPEWRITER (built-in)
        if stmt.startswith('typewriter '):
            text = stmt[11:].strip()
            text = self._parse_string(text)
            text = self._interpolate(text)
            self.typewriter(text)
            return
        
        # MODULE.FUNCTION call (dengan interp sebagai parameter pertama)
        if '.' in stmt and '(' in stmt and ')' in stmt:
            match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', stmt)
            if match:
                mod_name, func_name, args_str = match.groups()
                if mod_name in self.modules:
                    module = self.modules[mod_name]
                    if func_name in module:
                        func = module[func_name]
                        # Parse arguments
                        args = self._parse_args(args_str)
                        # Panggil function dengan interp sebagai parameter pertama
                        result = func(self, *args)
                        # Handle return value if needed
                        return
        
        self.error(f"Invalid syntax: {stmt}")
    
    def _parse_args(self, args_str):
        """Parse argument string, handle quotes and commas"""
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
                    args.append(self._parse_value(arg).value)
                current = []
            else:
                current.append(ch)
        
        last = ''.join(current).strip()
        if last:
            args.append(self._parse_value(last).value)
        
        return args
    
    def _parse_value(self, s):
        s = s.strip()
        
        # Handle dot access for modules (e.g., Colors.RED)
        if '.' in s and not (s.startswith('"') or s.startswith("'")):
            parts = s.split('.')
            if parts[0] in self.modules:
                obj = self.modules[parts[0]]
                for attr in parts[1:]:
                    if attr in obj:
                        obj = obj[attr]
                    else:
                        break
                else:
                    return JPXValue(obj)
        
        # Number
        try:
            if s.replace('.', '', 1).replace('-', '', 1).isdigit():
                if '.' in s:
                    return JPXValue(float(s))
                return JPXValue(int(s))
        except:
            pass
        
        # Quoted string
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return JPXValue(s[1:-1])
        
        # Boolean
        if s == 'true':
            return JPXValue(True)
        if s == 'false':
            return JPXValue(False)
        
        # Variable reference
        if s.startswith('$'):
            name = s[1:]
            if name in self.vars:
                return self.vars[name]
            self.error(f"Undefined variable: {s}")
        
        # Plain string
        return JPXValue(s)
    
    def _parse_string(self, s):
        s = s.strip()
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
            return s[1:-1]
        return s
    
    def _interpolate(self, s):
        """Replace $variable and $module.attribute"""
        def repl(m):
            full_ref = m.group(0)[1:]  # remove $
            
            # Check for dot notation (e.g., c.GREEN)
            if '.' in full_ref:
                parts = full_ref.split('.')
                if parts[0] in self.modules:
                    obj = self.modules[parts[0]]
                    for attr in parts[1:]:
                        if attr in obj:
                            obj = obj[attr]
                        else:
                            self.error(f"Undefined attribute: {full_ref}")
                    return str(obj)
                else:
                    self.error(f"Undefined module: {parts[0]}")
            
            # Regular variable
            if full_ref in self.vars:
                return str(self.vars[full_ref].value)
            self.error(f"Undefined variable: ${full_ref}")
        
        return re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_.]*)', repl, s)
    
    def _eval_condition(self, cond):
        cond = cond.strip()
        
        if '&&' in cond:
            for part in cond.split('&&'):
                if not self._eval_simple(part.strip()):
                    return False
            return True
        
        if '||' in cond:
            for part in cond.split('||'):
                if self._eval_simple(part.strip()):
                    return True
            return False
        
        return self._eval_simple(cond)
    
    def _eval_simple(self, expr):
        expr = expr.strip()
        
        for op in ['==', '!=', '<=', '>=', '<', '>']:
            if op in expr:
                left, right = expr.split(op, 1)
                left_val = self._get_value(left.strip())
                right_val = self._get_value(right.strip())
                
                if left_val.type != right_val.type:
                    if left_val.type in ('integer', 'float') and right_val.type == 'string':
                        try:
                            right_val = JPXValue(float(right_val.value))
                        except:
                            self.error(f"Cannot compare number with string '{right_val.value}'")
                    elif left_val.type == 'string' and right_val.type in ('integer', 'float'):
                        try:
                            left_val = JPXValue(float(left_val.value))
                        except:
                            self.error(f"Cannot compare string '{left_val.value}' with number")
                    else:
                        self.error(f"Cannot compare {left_val.type} with {right_val.type}")
                
                if op == '==':
                    return left_val.value == right_val.value
                elif op == '!=':
                    return left_val.value != right_val.value
                elif op == '<':
                    return left_val.value < right_val.value
                elif op == '<=':
                    return left_val.value <= right_val.value
                elif op == '>':
                    return left_val.value > right_val.value
                elif op == '>=':
                    return left_val.value >= right_val.value
        
        val = self._get_value(expr)
        return bool(val.value)
    
    def _get_value(self, token):
        token = token.strip()
        
        if token.startswith('$'):
            name = token[1:]
            if '.' in name:
                parts = name.split('.')
                if parts[0] in self.modules:
                    obj = self.modules[parts[0]]
                    for attr in parts[1:]:
                        if attr in obj:
                            obj = obj[attr]
                        else:
                            self.error(f"Undefined attribute: {token}")
                    return JPXValue(obj)
            else:
                if name in self.vars:
                    return self.vars[name]
                self.error(f"Undefined variable: {token}")
        
        try:
            if token.replace('.', '', 1).replace('-', '', 1).isdigit():
                if '.' in token:
                    return JPXValue(float(token))
                return JPXValue(int(token))
        except:
            pass
        
        if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
            return JPXValue(token[1:-1])
        
        if token == 'true':
            return JPXValue(True)
        if token == 'false':
            return JPXValue(False)
        
        return JPXValue(token)

def main():
    if len(sys.argv) < 2:
        print("JPX Interpreter v6.0 - Modular")
        print("Usage: python jpx.py file.jpx")
        sys.exit(1)
    
    jpx = JPXInterpreter()
    jpx.run(sys.argv[1])

if __name__ == '__main__':
    main()
