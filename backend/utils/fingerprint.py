import hashlib
import json
import logging

logger = logging.getLogger(__name__)


def generate_fingerprint(answers: dict, template_version: str) -> str:
    """
    Generate a deterministic fingerprint from quiz answers.
    Ensures different answers produce different fingerprints.
    
    Args:
        answers: Dictionary of quiz answers (must contain all answer data)
        template_version: Template version string
        
    Returns:
        SHA256 hash as hex string
    """
    # Normalize answers to ensure consistent hashing
    # Convert to dict if it's not already, and ensure all values are strings
    normalized_answers = {}
    
    if isinstance(answers, dict):
        # Sort keys and ensure all values are properly serialized
        for key in sorted(answers.keys()):
            value = answers[key]
            # Convert to string if not already, preserving the actual value
            if isinstance(value, (dict, list)):
                # For nested structures, use JSON stringification
                normalized_answers[key] = json.dumps(value, sort_keys=True, ensure_ascii=False)
            else:
                # Convert to string, preserving None as "None"
                normalized_answers[key] = str(value) if value is not None else "None"
    else:
        # If answers is not a dict, convert it
        logger.warning(f"Answers is not a dict, type: {type(answers)}")
        normalized_answers = {"raw": json.dumps(answers, sort_keys=True, ensure_ascii=False)}
    
    # Convert to canonical JSON with sorted keys
    canonical_json = json.dumps(normalized_answers, sort_keys=True, ensure_ascii=False)
    
    # Combine with template version
    combined = f"{template_version}:{canonical_json}"
    
    # Log for debugging (first 100 chars only)
    logger.debug(f"Fingerprint input (first 100 chars): {combined[:100]}...")
    
    # Generate SHA256 hash
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    fingerprint = hash_obj.hexdigest()
    
    logger.debug(f"Generated fingerprint: {fingerprint[:16]}... (from {len(combined)} chars)")
    
    return fingerprint