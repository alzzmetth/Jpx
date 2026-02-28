"""
JPX If-Else Module
Handles if-else control flow statements.
"""

class IfElseModule:
    """Module for handling if-else control flow."""
    
    def __init__(self, interpreter):
        self.interp = interpreter
        self.errors = interpreter.errors
        self.blocks = []  # Stack of blocks being processed
    
    def evaluate(self, condition):
        """
        Evaluate an if condition.
        
        Args:
            condition: Condition string
        
        Returns:
            Boolean result
        """
        return self.interp.eval_parser.evaluate_condition(condition)
    
    def enter_block(self, block_type, condition=None):
        """
        Enter a new block (if, else if, else).
        
        Args:
            block_type: 'if', 'else_if', or 'else'
            condition: Condition string (for if and else_if)
        """
        self.blocks.append({
            'type': block_type,
            'condition': condition,
            'executed': False
        })
    
    def exit_block(self):
        """Exit current block."""
        if self.blocks:
            return self.blocks.pop()
        return None
    
    def should_execute(self, condition=None):
        """
        Determine if current block should execute.
        
        Args:
            condition: Condition to evaluate (for if/else_if)
        
        Returns:
            Boolean indicating whether to execute
        """
        # If no blocks, always execute
        if not self.blocks:
            return True
        
        current = self.blocks[-1]
        
        # If block
        if current['type'] == 'if':
            result = self.evaluate(condition)
            current['executed'] = result
            return result
        
        # Else if block
        elif current['type'] == 'else_if':
            # Check if any previous block executed
            for block in self.blocks[:-1]:
                if block['executed']:
                    current['executed'] = False
                    return False
            
            result = self.evaluate(condition)
            current['executed'] = result
            return result
        
        # Else block
        elif current['type'] == 'else':
            # Check if any previous block executed
            for block in self.blocks[:-1]:
                if block['executed']:
                    current['executed'] = False
                    return False
            
            current['executed'] = True
            return True
        
        return True
    
    def in_if_block(self):
        """Check if currently in an if block."""
        return bool(self.blocks)
    
    def __init_module__(self):
        """Initialize module exports."""
        return {
            'evaluate': self.evaluate,
            'should_execute': self.should_execute,
            'in_if_block': self.in_if_block,
        }
