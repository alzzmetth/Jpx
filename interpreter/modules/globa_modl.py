"""
JPX Global Module
Handles global variable declarations and management.
"""

class GlobalModule:
    """Module for handling global variables."""
    
    def __init__(self, interpreter):
        self.interp = interpreter
        self.errors = interpreter.errors
        self.vars = interpreter.vars
    
    def set(self, name, value):
        """
        Set a global variable.
        
        Args:
            name: Variable name
            value: Value string to parse
        
        Returns:
            True if successful
        """
        if not name.isidentifier():
            self.errors.syntax_error(f"Invalid variable name: '{name}'")
        
        val = self.interp.eval_parser.get_value(value)
        self.vars[name] = val
        return True
    
    def get(self, name):
        """
        Get a global variable value.
        
        Args:
            name: Variable name
        
        Returns:
            Variable value or None if not found
        """
        if name in self.vars:
            return self.vars[name]['value']
        return None
    
    def exists(self, name):
        """Check if variable exists."""
        return name in self.vars
    
    def delete(self, name):
        """Delete a global variable."""
        if name in self.vars:
            del self.vars[name]
            return True
        return False
    
    def list(self):
        """List all global variables."""
        return list(self.vars.keys())
    
    def __init_module__(self):
        """Initialize module exports."""
        return {
            'set': self.set,
            'get': self.get,
            'exists': self.exists,
            'delete': self.delete,
            'list': self.list,
        }
