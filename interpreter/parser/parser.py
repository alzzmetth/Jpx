"""
JPX Parser Module
Handles parsing of JPX code into statements and blocks.
"""

import re

class Parser:
    """Main parser for JPX code."""
    
    def __init__(self, interpreter):
        self.interp = interpreter
        self.errors = interpreter.errors
    
    def parse_line(self, line):
        """
        Parse a single line of JPX code.
        Returns: (statement_type, content, condition) or None if empty/comment
        """
        line = line.strip()
        if not line or line.startswith('#'):
            return None
        
        # Check for if statement
        if line.startswith('if '):
            if not line.endswith('{'):
                self.errors.syntax_error("Expected '{' after if condition")
            condition = line[3:-1].strip()
            return ('if', condition)
        
        # Check for else if
        if line.startswith('} else if '):
            if not line.endswith('{'):
                self.errors.syntax_error("Expected '{' after else if")
            condition = line[10:-1].strip()
            return ('else_if', condition)
        
        # Check for else
        if line == '} else {':
            return ('else', None)
        
        # Check for closing brace
        if line == '}':
            return ('close', None)
        
        # Regular statement
        return ('statement', line)
    
    def split_statements(self, line):
        """
        Split a line into multiple statements based on semicolons,
        respecting strings and brackets.
        
        Args:
            line: Line of JPX code
            
        Returns:
            List of individual statements
        """
        statements = []
        current = []
        in_string = False
        quote_char = None
        bracket_depth = 0
        
        i = 0
        while i < len(line):
            char = line[i]
            
            # Handle string start/end
            if char in ('"', "'") and bracket_depth == 0:
                if not in_string:
                    in_string = True
                    quote_char = char
                elif quote_char == char:
                    in_string = False
                    quote_char = None
                current.append(char)
            
            # Handle brackets
            elif char == '[' and not in_string:
                bracket_depth += 1
                current.append(char)
            elif char == ']' and not in_string:
                bracket_depth -= 1
                if bracket_depth < 0:
                    self.errors.syntax_error("Unmatched closing bracket ']'")
                current.append(char)
            
            # Handle statement separator
            elif char == ';' and bracket_depth == 0 and not in_string:
                stmt = ''.join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
            
            # Handle escaped characters
            elif char == '\\' and i + 1 < len(line):
                i += 1
                current.append(line[i])
            
            else:
                current.append(char)
            
            i += 1
        
        # Add the last statement
        last_stmt = ''.join(current).strip()
        if last_stmt:
            statements.append(last_stmt)
        
        if bracket_depth > 0:
            self.errors.syntax_error("Unclosed bracket '['")
        
        if in_string:
            self.errors.syntax_error(f"Unclosed string (started with {quote_char})")
        
        return statements
