import hashlib
import json


def generate_fingerprint(answers: dict, template_version: str) -> str:
    """
    Generate a deterministic fingerprint from quiz answers.
    
    Args:
        answers: Dictionary of quiz answers
        template_version: Template version string
        
    Returns:
        SHA256 hash as hex string
    """
    # Convert answers to canonical JSON with sorted keys
    canonical_json = json.dumps(answers, sort_keys=True, ensure_ascii=False)
    
    # Combine with template version
    combined = f"{template_version}:{canonical_json}"
    
    # Generate SHA256 hash
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    return hash_obj.hexdigest()