"""
JPX Core Interpreter
Main interpreter class that coordinates all modules.
"""

import os
import sys
import time
import importlib.util
from .errors import ErrorHandler, JPXError
from .parser import Parser, EvalParser
from .modules import GlobalModule, IfElseModule

class JPXInterpreter:
    """Main JPX Interpreter class."""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.filename = "<stdin>"
        self.all_lines = []
        self.current_block = []
        self.line_number = 0
        
        # Initialize error handler
        self.errors = ErrorHandler()
        
        # Initialize parsers
        self.parser = Parser(self)
        self.eval_parser = EvalParser(self)
        
        # Data storage
        self.vars = {}          # Global variables {name: {'value': val, 'type': type}}
        self.config = {}         # Global_entry config
        self.modules = {}        # Loaded modules {name: module_dict}
        
        # Initialize built-in modules
        self._init_builtin_modules()
        
        # Set lib path
        self.lib_path = os.path.join(os.path.dirname(__file__), 'modules')
    
    def _init_builtin_modules(self):
        """Initialize built-in modules."""
        # Global module
        global_mod = GlobalModule(self)
        self.modules['global'] = global_mod.__init_module__()
        
        # If-Else module
        ifelse_mod = IfElseModule(self)
        self.modules['if'] = ifelse_mod.__init_module__()
    
    def log(self, msg):
        """Print debug message if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {msg}", file=sys.stderr)
    
    def typewriter(self, text, speed=None):
        """
        Built-in typewriter function.
        
        Args:
            text: Text to display
            speed: Speed in seconds per character (uses config if None)
        """
        if speed is None:
            if 'typewriter' not in self.config:
                self.errors.runtime_error(
                    "global_entry [typewriter] not defined. "
                    "Example: global_entry [typewriter=0.05]"
                )
            speed = float(self.config['typewriter']['value'])
        
        for ch in text:
            print(ch, end='', flush=True)
            time.sleep(speed)
        print()
    
    def run_file(self, filename):
        """Execute a JPX file."""
        self.filename = filename
        self.errors.filename = filename
        
        if not os.path.exists(filename):
            self.errors.error(f"File '{filename}' not found", "FileNotFoundError")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.all_lines = content.split('\n')
            self.current_block = self.all_lines
            self._execute_block(0)
        except Exception as e:
            self.errors.error(str(e), "Exception")
    
    def _execute_block(self, start_line):
        """Execute a block of code."""
        i = start_line
        block_lines = self.current_block
        
        while i < len(block_lines):
            self.line_number = i + 1
            raw_line = block_lines[i].rstrip()
            line = raw_line.strip()
            
            # Update error context
            self.errors.set_context(self.line_number, raw_line)
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                i += 1
                continue
            
            # Parse the line
            parsed = self.parser.parse_line(line)
            if not parsed:
                i += 1
                continue
            
            stmt_type, content = parsed
            
            # Handle different statement types
            if stmt_type == 'if':
                i += 1
                if_block, i = self._collect_block(i)
                
                # Check if should execute
                should_execute = self.eval_parser.evaluate_condition(content)
                
                if should_execute:
                    old_block = self.current_block
                    self.current_block = if_block
                    self._execute_block(0)
                    self.current_block = old_block
                
                # Handle else if and else
                while i < len(block_lines):
                    next_line = block_lines[i].strip()
                    if not next_line or next_line.startswith('#'):
                        i += 1
                        continue
                    
                    next_parsed = self.parser.parse_line(next_line)
                    if not next_parsed:
                        i += 1
                        continue
                    
                    next_type, next_content = next_parsed
                    
                    if next_type == 'else_if' and not should_execute:
                        i += 1
                        else_if_block, i = self._collect_block(i)
                        
                        if self.eval_parser.evaluate_condition(next_content):
                            old_block = self.current_block
                            self.current_block = else_if_block
                            self._execute_block(0)
                            self.current_block = old_block
                            should_execute = True
                    
                    elif next_type == 'else' and not should_execute:
                        i += 1
                        else_block, i = self._collect_block(i)
                        
                        old_block = self.current_block
                        self.current_block = else_block
                        self._execute_block(0)
                        self.current_block = old_block
                        should_execute = True
                    
                    else:
                        break
            
            elif stmt_type == 'close':
                i += 1
                return i
            
            else:  # Regular statement
                try:
                    statements = self.parser.split_statements(line)
                    for stmt in statements:
                        if stmt:
                            self._execute_statement(stmt)
                except Exception as e:
                    self.errors.runtime_error(str(e))
                
                i += 1
        
        return i
    
    def _collect_block(self, start):
        """Collect lines until matching closing brace."""
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
            self.errors.syntax_error("Unclosed block")
        
        return block, i
    
    def _import_module(self, name):
        """Load module from modules folder."""
        if name in self.modules:
            return self.modules[name]
        
        module_path = os.path.join(self.lib_path, f"{name}.py")
        if not os.path.exists(module_path):
            self.errors.module_error(f"Module '{name}' not found in modules/")
        
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Initialize module if it has __init_module__
            if hasattr(module, '__init_module__'):
                module_dict = module.__init_module__(self)
            else:
                # Export all functions
                module_dict = {}
                for attr in dir(module):
                    if not attr.startswith('_'):
                        module_dict[attr] = getattr(module, attr)
            
            self.modules[name] = module_dict
            return module_dict
            
        except Exception as e:
            self.errors.module_error(f"Failed to load module '{name}': {e}")
    
    def _execute_statement(self, stmt):
        """Execute a single statement."""
        
        # Import module
        if stmt.startswith('[') and stmt.endswith(']'):
            mod_name = stmt[1:-1]
            self._import_module(mod_name)
            return
        
        # global [name=value]
        import re
        m = re.match(r'^global\s*\[\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+?)\s*\]$', stmt)
        if m:
            name, val_str = m.groups()
            val = self.eval_parser.get_value(val_str)
            self.vars[name] = val
            return
        
        # global_entry [name=value]
        m = re.match(r'^global_entry\s*\[\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+?)\s*\]$', stmt)
        if m:
            name, val_str = m.groups()
            val = self.eval_parser.get_value(val_str)
            
            # Validate typewriter entry
            if name == 'typewriter' and val['type'] not in ('integer', 'float'):
                self.errors.runtime_error(
                    f"global_entry [typewriter] must be a number, got {val['type']}"
                )
            
            self.config[name] = val
            return
        
        # print statement
        if stmt.startswith('print '):
            text = stmt[6:].strip()
            # Remove quotes if present
            if (text.startswith('"') and text.endswith('"')) or \
               (text.startswith("'") and text.endswith("'")):
                text = text[1:-1]
            # Interpolate variables
            text = self.eval_parser.interpolate(text)
            print(text)
            return
        
        # typewriter statement
        if stmt.startswith('typewriter '):
            text = stmt[11:].strip()
            # Remove quotes if present
            if (text.startswith('"') and text.endswith('"')) or \
               (text.startswith("'") and text.endswith("'")):
                text = text[1:-1]
            # Interpolate variables
            text = self.eval_parser.interpolate(text)
            self.typewriter(text)
            return
        
        # Module function call: module.function(args)
        if '.' in stmt and '(' in stmt and ')' in stmt:
            m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$', stmt)
            if m:
                mod_name, func_name, args_str = m.groups()
                if mod_name in self.modules:
                    module = self.modules[mod_name]
                    if func_name in module:
                        func = module[func_name]
                        args = self.eval_parser._parse_args(args_str)
                        # Call function
                        result = func(self, *args)
                        return result
        
        self.errors.syntax_error(f"Invalid syntax: '{stmt}'")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="JPX Interpreter")
    parser.add_argument('file', nargs='?', help='JPX source file (.jpx)')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--version', action='version', version='JPX 7.0')
    
    args = parser.parse_args()
    
    if not args.file:
        print("JPX Interpreter v7.0 - Modular")
        print("Usage: python -m interpreter.core file.jpx")
        print("\nModules available in interpreter/modules/")
        sys.exit(1)
    
    interp = JPXInterpreter(debug=args.debug)
    interp.run_file(args.file)

if __name__ == '__main__':
    main()
