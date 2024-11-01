'''
Claude

Prompt: 

Write a unification function for first order logic, using Python. Use a nested list to represent a predicate. For example, P(x) would be ['P', 'x'], where 'P' is the predicate and 'x' is a variable. Represent constants as a list ['a']. So, P(a) where 'a' is a constant would be ['P', ['a']]. Functions should be similar. f(x) should  be ['f', 'x']. So, P(x,a,f(x)) where 'x' is a variable, 'a' is a constant and f(x) is a function, the corresponding representation should be ['P', ['a'], ['f', 'x']]. The function should take two arguments, the literals to be unified.

...

It says "TypeError: unhashable type: 'list'".

'''
def occurs_check(var, term, substitution):
    """
    Check if variable occurs in term under given substitution.
    This prevents infinite recursion in cases like X = f(X).
    """
    if var == term:
        return True
    elif isinstance(term, list) and len(term) > 1:
        # If term is a function or predicate, check all arguments
        return any(occurs_check(var, t, substitution) for t in term[1:])
    elif isinstance(term, str) and term in substitution:
        return occurs_check(var, substitution[term], substitution)
    return False

def to_immutable(term):
    """
    Convert a term to an immutable form (using tuples instead of lists).
    """
    if isinstance(term, list):
        return tuple(to_immutable(t) for t in term)
    return term

def to_mutable(term):
    """
    Convert a term back to a mutable form (using lists instead of tuples).
    """
    if isinstance(term, tuple):
        return list(to_mutable(t) for t in term)
    return term

def substitute(term, substitution):
    """
    Apply substitution to a term.
    """
    if isinstance(term, str):  # Variable
        if term in substitution:
            return to_mutable(substitution[term])
        return term
    elif isinstance(term, list):
        if len(term) == 1:  # Constant
            return term
        # Function or predicate: apply substitution to all arguments
        return [term[0]] + [substitute(arg, substitution) for arg in term[1:]]
    return term

def unify(term1, term2, substitution=None):
    """
    Unify two terms under a given substitution.
    Returns the most general unifier if it exists, None otherwise.
    
    Args:
        term1: First term to unify
        term2: Second term to unify
        substitution: Current substitution (default: empty dict)
    
    Returns:
        Dictionary representing the most general unifier, or None if unification fails
    """
    if substitution is None:
        substitution = {}
    
    # Apply current substitution to both terms
    term1 = substitute(term1, substitution)
    term2 = substitute(term2, substitution)
    
    # If terms are identical after substitution, success
    if term1 == term2:
        return substitution
    
    # If term1 is a variable
    if isinstance(term1, str):
        if occurs_check(term1, term2, substitution):
            return None  # Occurs check failed
        substitution[term1] = to_immutable(term2)
        return substitution
    
    # If term2 is a variable
    if isinstance(term2, str):
        if occurs_check(term2, term1, substitution):
            return None  # Occurs check failed
        substitution[term2] = to_immutable(term1)
        return substitution
    
    # If both terms are lists (predicates or functions)
    if isinstance(term1, list) and isinstance(term2, list):
        # Check if they have the same predicate/function symbol and arity
        if term1[0] != term2[0] or len(term1) != len(term2):
            return None
        
        # Recursively unify all arguments
        for arg1, arg2 in zip(term1[1:], term2[1:]):
            substitution = unify(arg1, arg2, substitution)
            if substitution is None:
                return None
                
        return substitution
    
    # If we get here, unification has failed
    return None

# Helper function to print substitutions in a readable format
def print_substitution(substitution):
    if substitution is None:
        print("Unification failed")
    else:
        print("Unification succeeded with substitution:")
        for var, term in substitution.items():
            print(f"{var} = {to_mutable(term)}")

# Example usage
if __name__ == "__main__":
    # Example 1: P(x) and P(a)
    term1 = ['P', 'x']
    term2 = ['P', ['a']]
    print(term1,"\n",term2)
    print("\nExample 1:")
    result = unify(term1, term2)
    print_substitution(result)

    # Example 2: P(x, f(x)) and P(y, f(y))
    term1 = ['P', 'x', ['f', 'x']]
    term2 = ['P', 'y', ['f', 'y']]
    result = unify(term1, term2)
    print("\nExample 2:")
    print(term1,"\n",term2)
    print_substitution(result)

    # Example 3: P(x, g(b), f(g(a))) and P(y, y, f(g(a)))
    term1 = ['P', 'x', ['g', ['b']], ['f', ['g', ['a']]]]
    term2 = ['P', 'y', 'y', ['f', 'y']]
    result = unify(term1, term2)
    print("\nExample 3:")
    print(term1,"\n",term2)
    print_substitution(result)

    # Example 4: P(x) and P(Socrates)
    term1 = ['P', ['x']]
    term2 = ['P', ['Socrates']]
    result = unify(term1, term2)
    print("\nExample 4:")
    print(term1,"\n",term2)
    print_substitution(result)
