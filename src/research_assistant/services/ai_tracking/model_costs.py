"""Utility for tracking AI model costs"""

class AIModelCosts:
    """Tracks costs for different AI models"""
    
    COSTS = {
        # OpenAI Models
        'gpt-4o-mini': {
            'prompt': 0.00015,    # $0.15 per 1K prompt tokens
            'completion': 0.00060  # $0.60 per 1K completion tokens
        },
        'gpt-4o': {
            'prompt': 0.00050,     # $0.50 per 1K prompt tokens
            'completion': 0.00150   # $1.50 per 1K completion tokens
        },
        'gpt-3.5-turbo': {
            'prompt': 0.00010,     # $0.10 per 1K prompt tokens
            'completion': 0.00020   # $0.20 per 1K completion tokens
        },
        # Add other models as needed
    }
    
    @classmethod
    def get_cost(cls, model_name):
        """Get cost rates for a model"""
        model_name = model_name.lower()
        
        # Handle various model name formats
        for key in cls.COSTS.keys():
            if key in model_name:
                return cls.COSTS[key]
        
        # Default to GPT-3.5 if model not found
        print(f"WARNING: Cost not found for model {model_name}, using gpt-3.5-turbo rates")
        return cls.COSTS['gpt-3.5-turbo']
    
    @classmethod
    def calculate_cost(cls, prompt_tokens, completion_tokens, model_name, is_cached=False):
        """Calculate cost for a specific usage"""
        if is_cached:
            return 0.0  # No cost for cached responses
            
        cost_rates = cls.get_cost(model_name)
        
        prompt_cost = (prompt_tokens / 1000) * cost_rates['prompt']
        completion_cost = (completion_tokens / 1000) * cost_rates['completion']
        
        total_cost = prompt_cost + completion_cost
        
        print(f"Cost calculation for {model_name}: {prompt_tokens} prompt tokens, {completion_tokens} completion tokens")
        print(f"Prompt cost: ${prompt_cost:.6f}, Completion cost: ${completion_cost:.6f}, Total: ${total_cost:.6f}")
        
        return {
            'prompt_cost': prompt_cost,
            'completion_cost': completion_cost,
            'total_cost': total_cost,
            'cost_per_1k_prompt': cost_rates['prompt'],
            'cost_per_1k_completion': cost_rates['completion']
        }