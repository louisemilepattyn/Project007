# app/validators/accounting_rules.py
def reconcile(items):
    """Basic sanity checks."""
    warnings = []
    if not items:
        warnings.append("No items extracted.")
    return warnings
