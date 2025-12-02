"""
Unit tests for Discovery worksheet validation script.
"""

import pytest
import tempfile
import os
from pathlib import Path
from validate_discovery_worksheet import (
    validate_file_extension,
    validate_file_size,
    validate_content_is_text,
    validate_no_malicious_content,
    validate_discovery_worksheet,
    ValidationError,
    MAX_FILE_SIZE
)


class TestValidateFileExtension:
    """Tests for validate_file_extension function."""
    
    def test_valid_md_extension(self):
        """Test that .md extension is accepted."""
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            temp_path = f.name
        
        try:
            # Should not raise
            validate_file_extension(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_uppercase_md_extension(self):
        """Test that .MD extension is accepted (case insensitive)."""
        with tempfile.NamedTemporaryFile(suffix='.MD', delete=False) as f:
            temp_path = f.name
        
        try:
            validate_file_extension(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_invalid_extension_txt(self):
        """Test that .txt extension is rejected."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValidationError, match="Invalid file extension"):
                validate_file_extension(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_invalid_extension_pdf(self):
        """Test that .pdf extension is rejected."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValidationError, match="Invalid file extension"):
                validate_file_extension(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_no_extension(self):
        """Test that file with no extension is rejected."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValidationError, match="Invalid file extension"):
                validate_file_extension(temp_path)
        finally:
            os.unlink(temp_path)


class TestValidateFileSize:
    """Tests for validate_file_size function."""
    
    def test_valid_file_size(self):
        """Test that file within size limit passes."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write("Small content")
            temp_path = f.name
        
        try:
            validate_file_size(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_file_size_at_limit(self):
        """Test that file at exact size limit passes."""
        # Create file at exactly 5MB
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.md') as f:
            f.write(b'x' * MAX_FILE_SIZE)
            temp_path = f.name
        
        try:
            validate_file_size(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_file_size_exceeds_limit(self):
        """Test that file exceeding size limit fails."""
        # Create file larger than 5MB
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.md') as f:
            f.write(b'x' * (MAX_FILE_SIZE + 1))
            temp_path = f.name
        
        try:
            with pytest.raises(ValidationError, match="exceeds maximum"):
                validate_file_size(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_empty_file(self):
        """Test that empty file fails."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            temp_path = f.name
        
        try:
            with pytest.raises(ValidationError, match="empty"):
                validate_file_size(temp_path)
        finally:
            os.unlink(temp_path)


class TestValidateContentIsText:
    """Tests for validate_content_is_text function."""
    
    def test_valid_text_content(self):
        """Test that valid text content passes."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write("# Markdown content\n\nThis is text.")
            temp_path = f.name
        
        try:
            validate_content_is_text(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_binary_content_fails(self):
        """Test that binary content fails."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.md') as f:
            f.write(b'\x00\x01\x02\x03\xff\xfe')
            temp_path = f.name
        
        try:
            with pytest.raises(ValidationError, match="binary data"):
                validate_content_is_text(temp_path)
        finally:
            os.unlink(temp_path)


class TestValidateNoMaliciousContent:
    """Tests for validate_no_malicious_content function."""
    
    def test_valid_markdown_content(self):
        """Test that valid markdown content passes."""
        content = "# Title\n\nThis is normal markdown."
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validate_no_malicious_content(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_script_tags_detected(self):
        """Test that script tags are detected."""
        content = "<script>alert('xss')</script>"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with pytest.raises(ValidationError, match="Malicious content"):
                validate_no_malicious_content(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_executable_code_detected(self):
        """Test that executable code patterns are detected."""
        content = "import os; os.system('rm -rf /')"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            with pytest.raises(ValidationError, match="Malicious content"):
                validate_no_malicious_content(temp_path)
        finally:
            os.unlink(temp_path)


class TestValidateDiscoveryWorksheet:
    """Tests for main validate_discovery_worksheet function."""
    
    def test_valid_file_passes_all_checks(self):
        """Test that a valid file passes all validation checks."""
        content = "# SLODLC Discovery Worksheet\n\nService: Test Service"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            is_valid, message = validate_discovery_worksheet(temp_path)
            assert is_valid is True
            assert "passed" in message.lower()
        finally:
            os.unlink(temp_path)
    
    def test_invalid_extension_fails(self):
        """Test that invalid extension causes validation to fail."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Content")
            temp_path = f.name
        
        try:
            is_valid, message = validate_discovery_worksheet(temp_path)
            assert is_valid is False
            assert "extension" in message.lower()
        finally:
            os.unlink(temp_path)
    
    def test_oversized_file_fails(self):
        """Test that oversized file fails validation."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.md') as f:
            f.write(b'x' * (MAX_FILE_SIZE + 1))
            temp_path = f.name
        
        try:
            is_valid, message = validate_discovery_worksheet(temp_path)
            assert is_valid is False
            assert "size" in message.lower() or "exceeds" in message.lower()
        finally:
            os.unlink(temp_path)
    
    def test_binary_file_fails(self):
        """Test that binary file fails validation."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.md') as f:
            f.write(b'\x00\x01\x02\x03')
            temp_path = f.name
        
        try:
            is_valid, message = validate_discovery_worksheet(temp_path)
            assert is_valid is False
            assert "binary" in message.lower()
        finally:
            os.unlink(temp_path)
    
    def test_malicious_content_fails(self):
        """Test that malicious content fails validation."""
        content = "<script>alert('xss')</script>"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            is_valid, message = validate_discovery_worksheet(temp_path)
            assert is_valid is False
            assert "malicious" in message.lower() or "detected" in message.lower()
        finally:
            os.unlink(temp_path)
    
    def test_nonexistent_file_fails(self):
        """Test that nonexistent file fails validation."""
        is_valid, message = validate_discovery_worksheet("/nonexistent/file.md")
        assert is_valid is False
        assert "not found" in message.lower()

