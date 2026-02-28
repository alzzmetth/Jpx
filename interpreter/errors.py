"""
JPX Error Handling Module
"""

import sys

class JPXError(Exception):
    """Base exception for JPX interpreter errors."""
    pass

class JPXSyntaxError(JPXError):
    """Exception raised for syntax errors in JPX code."""
    pass

class JPXRuntimeError(JPXError):
    """Exception raised for runtime errors in JPX code."""
    pass

class JPXModuleError(JPXError):
    """Exception raised for module-related errors."""
    pass

class ErrorHandler:
    """Centralized error handling for JPX interpreter."""
    
    def __init__(self, filename="<stdin>"):
        self.filename = filename
        self.line_number = 0
        self.line_content = ""
    
    def set_context(self, line_num, line_content):
        """Set current line context for error reporting."""
        self.line_number = line_num
        self.line_content = line_content
    
    def error(self, message, error_type="Error"):
        """
        Display error message with context and exit.
        
        Args:
            message: Error message
            error_type: Type of error (Syntax, Runtime, Module, etc.)
        """
        output = []
        output.append(f"\n╔══════════════════════════════════════════════════════════╗")
        output.append(f"║                    JPX {error_type:<30}║")
        output.append(f"╚══════════════════════════════════════════════════════════╝")
        
        if self.line_number > 0:
            output.append(f"")
            output.append(f"  📍 Location: {self.filename}, line {self.line_number}")
            if self.line_content:
                output.append(f"  📝 Code:     {self.line_number} | {self.line_content}")
        
        output.append(f"")
        output.append(f"  ❌ {message}")
        output.append(f"")
        
        print("\n".join(output), file=sys.stderr)
        sys.exit(1)
    
    def syntax_error(self, message):
        """Raise syntax error."""
        self.error(message, "SyntaxError")
    
    def runtime_error(self, message):
        """Raise runtime error."""
        self.error(message, "RuntimeError")
    
    def module_error(self, message):
        """Raise module error."""
        self.error(message, "ModuleError")
