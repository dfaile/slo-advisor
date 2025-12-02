"""
Utility functions for file handling, sanitization, and error document generation.
"""

import re
from datetime import datetime
from typing import Optional


def read_file_content(file_path: str) -> str:
    """
    Read file content as text.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        File content as string
        
    Raises:
        IOError: If file cannot be read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        raise ValueError("File contains binary data and cannot be read as text")


def is_text_based(content: bytes) -> bool:
    """
    Check if content is text-based (not binary).
    
    Args:
        content: File content as bytes
        
    Returns:
        True if content appears to be text-based, False otherwise
    """
    # Check for null bytes which indicate binary content
    if b'\x00' in content:
        return False
    
    # Try to decode as UTF-8
    try:
        content.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent prompt injection attacks.
    
    Removes or escapes potentially dangerous patterns that could be used
    to manipulate AI prompts.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove common prompt injection patterns
    # Remove instructions that try to override system prompts
    patterns_to_remove = [
        r'(?i)ignore\s+(previous|above|all)\s+(instructions|prompts|rules)',
        r'(?i)forget\s+(everything|all|previous)',
        r'(?i)you\s+are\s+now',
        r'(?i)system\s*:\s*',
        r'(?i)assistant\s*:\s*',
        r'(?i)user\s*:\s*',
    ]
    
    sanitized = text
    for pattern in patterns_to_remove:
        sanitized = re.sub(pattern, '', sanitized)
    
    # Escape potential command injection
    # Remove backticks that could be used for code execution
    sanitized = sanitized.replace('```', '')
    
    # Remove excessive newlines that could break formatting
    sanitized = re.sub(r'\n{10,}', '\n\n', sanitized)
    
    return sanitized.strip()


def detect_malicious_patterns(content: str) -> list[str]:
    """
    Detect potentially malicious patterns in content.
    
    Args:
        content: Content to check
        
    Returns:
        List of detected malicious patterns (empty if none found)
    """
    malicious_patterns = []
    
    # Script tags
    if re.search(r'<script[^>]*>', content, re.IGNORECASE):
        malicious_patterns.append("Script tags detected")
    
    # Executable code patterns
    if re.search(r'(?i)(exec|eval|system|subprocess|os\.system)', content):
        malicious_patterns.append("Executable code patterns detected")
    
    # JavaScript event handlers
    if re.search(r'on\w+\s*=', content, re.IGNORECASE):
        malicious_patterns.append("JavaScript event handlers detected")
    
    # Data URIs that could contain scripts
    if re.search(r'data:text/html', content, re.IGNORECASE):
        malicious_patterns.append("Data URI with HTML content detected")
    
    # Base64 encoded scripts (basic detection)
    if re.search(r'data:[^;]+;base64,[A-Za-z0-9+/=]{100,}', content):
        malicious_patterns.append("Large base64 encoded content detected")
    
    return malicious_patterns


def generate_error_document(error_message: str, service_name: str, 
                            error_details: Optional[str] = None) -> str:
    """
    Generate an error document with timestamp and error details.
    
    Args:
        error_message: Main error message
        service_name: Name of the service
        error_details: Optional additional error details
        
    Returns:
        Error document content as Markdown string
    """
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    doc = f"""# SLO Implementation Guide Generation Error

**Service:** {service_name}
**Timestamp:** {timestamp}

## Error

{error_message}

"""
    
    if error_details:
        doc += f"""## Error Details

```
{error_details}
```

"""
    
    doc += """## Next Steps

Please review the error above and:
1. Check that your Discovery worksheet is properly formatted
2. Verify that all required fields are provided
3. Ensure the file is a valid Markdown document
4. Try again or contact support if the issue persists

"""
    
    return doc

