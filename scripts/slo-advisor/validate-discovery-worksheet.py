#!/usr/bin/env python3
"""
Validation script for SLODLC Discovery worksheet files.

Validates that uploaded files meet security and format requirements:
- File extension must be .md
- File size must be within limits (max 5MB)
- Content must be text-based (not binary)
- No malicious patterns (script tags, executable code, etc.)
"""

import os
import sys
from pathlib import Path
from typing import Tuple

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    is_text_based,
    detect_malicious_patterns,
    read_file_content
)


# Constants
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
ALLOWED_EXTENSIONS = ['.md']


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_file_extension(file_path: str) -> None:
    """
    Validate that file has .md extension.
    
    Args:
        file_path: Path to the file
        
    Raises:
        ValidationError: If file extension is not .md
    """
    file_ext = Path(file_path).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Invalid file extension: '{file_ext}'. "
            f"Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed."
        )


def validate_file_size(file_path: str) -> None:
    """
    Validate that file size is within limits (max 5MB).
    
    Args:
        file_path: Path to the file
        
    Raises:
        ValidationError: If file size exceeds maximum
    """
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        size_mb = file_size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise ValidationError(
            f"File size ({size_mb:.2f} MB) exceeds maximum allowed size "
            f"({max_mb} MB)."
        )
    
    if file_size == 0:
        raise ValidationError("File is empty.")


def validate_content_is_text(file_path: str) -> None:
    """
    Validate that file content is text-based (not binary).
    
    Args:
        file_path: Path to the file
        
    Raises:
        ValidationError: If file contains binary data
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            if not is_text_based(content):
                raise ValidationError(
                    "File contains binary data. Only text-based Markdown files are allowed."
                )
    except IOError as e:
        raise ValidationError(f"Error reading file: {str(e)}")


def validate_no_malicious_content(file_path: str) -> None:
    """
    Validate that file does not contain malicious patterns.
    
    Args:
        file_path: Path to the file
        
    Raises:
        ValidationError: If malicious patterns are detected
    """
    try:
        content = read_file_content(file_path)
        malicious_patterns = detect_malicious_patterns(content)
        
        if malicious_patterns:
            patterns_str = "; ".join(malicious_patterns)
            raise ValidationError(
                f"Malicious content detected: {patterns_str}. "
                "File contains potentially dangerous patterns and cannot be processed."
            )
    except ValueError as e:
        raise ValidationError(str(e))
    except IOError as e:
        raise ValidationError(f"Error reading file content: {str(e)}")


def validate_discovery_worksheet(file_path: str) -> Tuple[bool, str]:
    """
    Main validation function for Discovery worksheet files.
    
    Performs all validation checks:
    1. File extension validation
    2. File size validation
    3. Content is text-based
    4. No malicious patterns
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        Tuple of (is_valid, message)
        - is_valid: True if file passes all validations, False otherwise
        - message: Success message or error description
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"
        
        # Run all validation checks
        validate_file_extension(file_path)
        validate_file_size(file_path)
        validate_content_is_text(file_path)
        validate_no_malicious_content(file_path)
        
        return True, "File validation passed successfully."
        
    except ValidationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error during validation: {str(e)}"


def main():
    """
    Command-line interface for validation script.
    
    Usage:
        python validate-discovery-worksheet.py <file_path>
    """
    if len(sys.argv) != 2:
        print("Usage: python validate-discovery-worksheet.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    is_valid, message = validate_discovery_worksheet(file_path)
    
    if is_valid:
        print(f"✓ {message}")
        sys.exit(0)
    else:
        print(f"✗ Validation failed: {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()

