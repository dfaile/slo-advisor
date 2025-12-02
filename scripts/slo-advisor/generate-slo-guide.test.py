"""
Unit tests for SLO Implementation Guide generation script.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent))

# Import the module (handle hyphen in filename)
import importlib.util
spec = importlib.util.spec_from_file_location("generate_slo_guide", Path(__file__).parent / "generate-slo-guide.py")
generate_slo_guide = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_slo_guide)

# Import functions from the module
create_prompt_template = generate_slo_guide.create_prompt_template
initialize_openai_client = generate_slo_guide.initialize_openai_client
call_openai_api = generate_slo_guide.call_openai_api
format_as_markdown_document = generate_slo_guide.format_as_markdown_document
generate_output_filename = generate_slo_guide.generate_output_filename
estimate_tokens = generate_slo_guide.estimate_tokens
check_token_limit = generate_slo_guide.check_token_limit
chunk_discovery_content = generate_slo_guide.chunk_discovery_content


class TestCreatePromptTemplate:
    """Tests for create_prompt_template function."""
    
    def test_prompt_includes_discovery_content(self):
        """Test that prompt includes the Discovery worksheet content."""
        discovery = "# Service: Test Service\n\nThis is test content."
        platform = "Dynatrace"
        
        prompt = create_prompt_template(discovery, platform)
        
        assert discovery in prompt
        assert "Test Service" in prompt
    
    def test_prompt_includes_observability_platform(self):
        """Test that prompt includes the observability platform."""
        discovery = "Test discovery content"
        platform = "Grafana"
        
        prompt = create_prompt_template(discovery, platform)
        
        assert platform in prompt
        assert "Grafana" in prompt
    
    def test_prompt_includes_required_sections(self):
        """Test that prompt requests all required sections."""
        discovery = "Test content"
        platform = "Splunk"
        
        prompt = create_prompt_template(discovery, platform)
        
        required_sections = [
            "Service Overview",
            "SLI Definitions",
            "SLO Targets",
            "Error Budgets",
            "Implementation Steps",
            "Monitoring and Alerting",
            "Validation and Testing",
            "Maintenance and Review"
        ]
        
        for section in required_sections:
            assert section in prompt
    
    def test_prompt_includes_platform_specific_instructions(self):
        """Test that prompt includes platform-specific instructions."""
        discovery = "Test content"
        platform = "LogicMonitor"
        
        prompt = create_prompt_template(discovery, platform)
        
        assert platform in prompt
        assert "platform-specific" in prompt.lower()
        assert "LogicMonitor" in prompt
    
    def test_prompt_includes_slodlc_context(self):
        """Test that prompt includes SLODLC context."""
        discovery = "Test content"
        platform = "Dynatrace"
        
        prompt = create_prompt_template(discovery, platform)
        
        assert "SLODLC" in prompt
        assert "SLO Development Lifecycle" in prompt


class TestGenerateOutputFilename:
    """Tests for generate_output_filename function."""
    
    def test_normal_filename_generation(self):
        """Test normal filename generation."""
        filename = generate_output_filename("my-service", is_error=False)
        assert filename == "my-service-slo-implementation-guide.md"
    
    def test_error_filename_generation(self):
        """Test error filename generation."""
        filename = generate_output_filename("my-service", is_error=True)
        assert filename == "my-service-slo-implementation-guide-ERROR.md"
    
    def test_filename_sanitization(self):
        """Test that service names are sanitized for filenames."""
        filename = generate_output_filename("My Service Name!", is_error=False)
        assert "my-service-name" in filename
        assert "!" not in filename
    
    def test_filename_lowercase(self):
        """Test that filenames are lowercase."""
        filename = generate_output_filename("MY-SERVICE", is_error=False)
        assert filename == "my-service-slo-implementation-guide.md"
    
    def test_filename_removes_special_chars(self):
        """Test that special characters are removed or replaced."""
        filename = generate_output_filename("service@name#123", is_error=False)
        assert "@" not in filename
        assert "#" not in filename
        assert "service" in filename.lower()
    
    def test_filename_fallback(self):
        """Test that empty service name uses fallback."""
        filename = generate_output_filename("", is_error=False)
        assert "service" in filename


class TestFormatAsMarkdownDocument:
    """Tests for format_as_markdown_document function."""
    
    def test_document_includes_header(self):
        """Test that document includes proper header."""
        content = "# Generated Guide\n\nContent here"
        service = "test-service"
        platform = "Dynatrace"
        
        doc = format_as_markdown_document(content, service, platform)
        
        assert "# SLO Implementation Guide" in doc
        assert service in doc
        assert platform in doc
    
    def test_document_includes_timestamp(self):
        """Test that document includes timestamp."""
        content = "Test content"
        doc = format_as_markdown_document(content, "service", "Grafana")
        
        assert "Generated:" in doc
        assert "UTC" in doc
    
    def test_document_includes_methodology(self):
        """Test that document includes SLODLC methodology."""
        content = "Test content"
        doc = format_as_markdown_document(content, "service", "Splunk")
        
        assert "SLODLC" in doc
        assert "SLO Development Lifecycle" in doc
    
    def test_document_preserves_content(self):
        """Test that original content is preserved."""
        content = "# My Guide\n\nThis is the content."
        doc = format_as_markdown_document(content, "service", "platform")
        
        assert "My Guide" in doc
        assert "This is the content" in doc
    
    def test_document_ends_with_newline(self):
        """Test that document ends with newline."""
        content = "Test content"
        doc = format_as_markdown_document(content, "service", "platform")
        
        assert doc.endswith('\n')


class TestEstimateTokens:
    """Tests for estimate_tokens function."""
    
    def test_token_estimation_returns_integer(self):
        """Test that token estimation returns an integer."""
        text = "This is a test string with some content."
        tokens = estimate_tokens(text)
        
        assert isinstance(tokens, int)
        assert tokens > 0
    
    def test_token_estimation_scales_with_text_length(self):
        """Test that token count scales with text length."""
        short_text = "Short"
        long_text = "This is a much longer text string that should have more tokens than the short one."
        
        short_tokens = estimate_tokens(short_text)
        long_tokens = estimate_tokens(long_text)
        
        assert long_tokens > short_tokens
    
    def test_token_estimation_handles_empty_string(self):
        """Test that empty string returns zero tokens."""
        tokens = estimate_tokens("")
        assert tokens == 0


class TestCheckTokenLimit:
    """Tests for check_token_limit function."""
    
    def test_small_content_does_not_exceed_limit(self):
        """Test that small content does not exceed limit."""
        content = "Small content"
        exceeds, tokens, limit = check_token_limit(content, "Dynatrace", "gpt-4")
        
        assert not exceeds
        assert tokens < limit
    
    def test_returns_token_count(self):
        """Test that function returns token count."""
        content = "Test content"
        exceeds, tokens, limit = check_token_limit(content, "Grafana", "gpt-3.5-turbo")
        
        assert isinstance(tokens, int)
        assert tokens >= 0
    
    def test_returns_limit(self):
        """Test that function returns the limit."""
        content = "Test content"
        exceeds, tokens, limit = check_token_limit(content, "Splunk", "gpt-4")
        
        assert isinstance(limit, int)
        assert limit > 0


class TestChunkDiscoveryContent:
    """Tests for chunk_discovery_content function."""
    
    def test_chunking_returns_list(self):
        """Test that chunking returns a list."""
        content = "# Section 1\n\nContent 1\n\n## Section 2\n\nContent 2"
        chunks = chunk_discovery_content(content, 1000, "gpt-4")
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
    
    def test_chunking_preserves_content(self):
        """Test that chunking preserves all content."""
        content = "# Section 1\n\nContent 1\n\n## Section 2\n\nContent 2"
        chunks = chunk_discovery_content(content, 1000, "gpt-4")
        
        combined = "\n\n".join(chunks)
        assert "Section 1" in combined
        assert "Content 1" in combined
        assert "Section 2" in combined
        assert "Content 2" in combined
    
    def test_chunking_handles_small_content(self):
        """Test that small content returns single chunk."""
        content = "Small content"
        chunks = chunk_discovery_content(content, 1000, "gpt-4")
        
        assert len(chunks) == 1
        assert chunks[0] == content


class TestInitializeOpenAIClient:
    """Tests for initialize_openai_client function."""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-123'})
    @patch('generate_slo_guide.OpenAI')
    def test_initializes_client_with_valid_key(self, mock_openai):
        """Test that client initializes with valid API key."""
        client = initialize_openai_client()
        mock_openai.assert_called_once_with(api_key='test-key-123')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_raises_error_when_key_missing(self):
        """Test that function raises error when API key is missing."""
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            initialize_openai_client()
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': ''})
    def test_raises_error_when_key_empty(self):
        """Test that function raises error when API key is empty."""
        with pytest.raises(ValueError, match="empty"):
            initialize_openai_client()


class TestCallOpenAIAPI:
    """Tests for call_openai_api function."""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_successful_api_call(self):
        """Test successful API call."""
        # Mock client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated guide content"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call API with mocked client
        result = call_openai_api(mock_client, "Test prompt", "gpt-4")
        
        assert result == "Generated guide content"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_api_call_with_rate_limit_error(self):
        """Test API call handling rate limit error."""
        from openai import RateLimitError
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RateLimitError(
            "Rate limit exceeded",
            response=MagicMock(),
            body=MagicMock()
        )
        
        # Should raise exception after retries
        with pytest.raises(Exception, match="Rate limit"):
            call_openai_api(mock_client, "Test prompt", "gpt-4", max_retries=0)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_api_call_with_empty_response(self):
        """Test API call handling empty response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(ValueError, match="empty"):
            call_openai_api(mock_client, "Test prompt", "gpt-4")
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_api_call_with_timeout_error(self):
        """Test API call handling timeout error."""
        from openai import APITimeoutError
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APITimeoutError(
            "Request timed out",
            request=MagicMock()
        )
        
        # Should raise TimeoutError after retries
        with pytest.raises(TimeoutError, match="timed out"):
            call_openai_api(mock_client, "Test prompt", "gpt-4", max_retries=0)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_api_call_with_connection_error(self):
        """Test API call handling connection error."""
        from openai import APIConnectionError
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = APIConnectionError(
            "Connection failed",
            request=MagicMock()
        )
        
        # Should raise Exception after retries
        with pytest.raises(Exception, match="Connection"):
            call_openai_api(mock_client, "Test prompt", "gpt-4", max_retries=0)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_api_call_with_authentication_error(self):
        """Test API call handling authentication error."""
        from openai import APIError
        
        mock_client = MagicMock()
        mock_error = APIError(
            "Invalid API key",
            request=MagicMock(),
            body={"error": {"message": "Invalid authentication"}}
        )
        mock_client.chat.completions.create.side_effect = mock_error
        
        # Should raise ValueError for authentication errors
        with pytest.raises(ValueError, match="API key"):
            call_openai_api(mock_client, "Test prompt", "gpt-4")
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_api_call_with_invalid_response_structure(self):
        """Test API call handling invalid response structure."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = None  # Invalid: no choices
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(ValueError, match="invalid response structure"):
            call_openai_api(mock_client, "Test prompt", "gpt-4")
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_api_call_with_empty_choices_array(self):
        """Test API call handling empty choices array."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = []  # Empty choices
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(ValueError, match="empty choices"):
            call_openai_api(mock_client, "Test prompt", "gpt-4")
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_api_call_with_whitespace_only_response(self):
        """Test API call handling whitespace-only response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "   \n\n   "  # Only whitespace
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(ValueError, match="whitespace"):
            call_openai_api(mock_client, "Test prompt", "gpt-4")
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_api_call_retry_on_rate_limit(self, mock_sleep):
        """Test that API call retries on rate limit with exponential backoff."""
        from openai import RateLimitError
        
        mock_client = MagicMock()
        
        # First call fails with rate limit, second succeeds
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Success after retry"
        
        mock_client.chat.completions.create.side_effect = [
            RateLimitError("Rate limit", response=MagicMock(), body=MagicMock()),
            mock_response
        ]
        
        result = call_openai_api(mock_client, "Test prompt", "gpt-4", max_retries=1, initial_backoff=0.01)
        
        assert result == "Success after retry"
        assert mock_client.chat.completions.create.call_count == 2
        mock_sleep.assert_called_once()  # Should have slept once
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_api_call_fallback_to_gpt35_on_gpt4_failure(self):
        """Test that API call falls back to GPT-3.5-turbo when GPT-4 fails."""
        from openai import RateLimitError
        
        mock_client = MagicMock()
        
        # GPT-4 fails, GPT-3.5 succeeds
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "GPT-3.5 response"
        
        mock_client.chat.completions.create.side_effect = [
            RateLimitError("Rate limit", response=MagicMock(), body=MagicMock()),
            mock_response
        ]
        
        result = call_openai_api(mock_client, "Test prompt", "gpt-4", max_retries=0)
        
        assert result == "GPT-3.5 response"
        # Should have tried both models
        assert mock_client.chat.completions.create.call_count == 2
        # First call should be GPT-4
        assert mock_client.chat.completions.create.call_args_list[0].kwargs['model'] == "gpt-4"
        # Second call should be GPT-3.5-turbo
        assert mock_client.chat.completions.create.call_args_list[1].kwargs['model'] == "gpt-3.5-turbo"


class TestSampleDiscoveryWorksheet:
    """Tests with sample Discovery worksheet content to verify output format."""
    
    SAMPLE_DISCOVERY_WORKSHEET = """# SLODLC Discovery Worksheet

## 1. Service

### 1.1 Service description

The Chatbot is an online service that simulates a human being with which you can talk in natural language. The task of such a service is to act in an intelligent conversation with a person on various topics.

### 1.2 Owner and Stakeholders

1. Service Owner: Daniel Burton, IT Director
2. Service Stakeholders: John Smith, Senior PM; Joe Doe, SRE

### 1.3 Service Business Context

- Who cares about this service? Sales and IT staff
- Why do they use it? Customers use Chatbot service because it is a primary way to search for the desired product
- What happens if they can't? Customers tend to come back to this online shop because of satisfaction with buying experience

## 2. Prioritize User Journeys & Expectations

### 2.1 Define The Users of the service

Primary users: Online customers shopping for products

### 2.2 Users Journeys

User Journey 1: Customer searches for product using Chatbot
User Journey 2: Customer completes purchase through Chatbot

### 2.3 User Expectations per Journey

- User Journey 1: Fast response time (< 200ms), accurate product recommendations
- User Journey 2: Reliable transaction processing, secure payment handling

## 3. Analyze Dependencies

### 3.1 Architectural dependencies

- Web Server (Ruby on Rails)
- Database: MySQL
- Payment gateway (3rd party)

## 4. Observe System Behavior

### 4.1 Data sources

- Service: Web Server
  - Metrics: Latency, Availability
  - Observability System: DataObserverOne

### 4.2 SLIs

1. Web Server Latency SLI: Proportion of HTTP GET requests that have a response in 600ms
2. Chatbot Latency SLI: Proportion of Chatbot responses that have a response in 200ms
"""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    def test_output_format_with_sample_discovery_worksheet(self):
        """Test that output format is correct with sample Discovery worksheet."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        
        # Mock a realistic OpenAI response
        mock_response.choices[0].message.content = """# Service Overview

The Chatbot service is an online service that enables natural language conversations with customers.

## SLI Definitions

### Web Server Latency SLI
- **Metric**: HTTP GET request latency
- **Target**: 600ms p95
- **Data Source**: DataObserverOne

### Chatbot Latency SLI
- **Metric**: Chatbot response time
- **Target**: 200ms p95
- **Data Source**: DataObserverOne

## SLO Targets

- Web Server Latency: 99% of requests < 600ms
- Chatbot Latency: 99% of responses < 200ms

## Error Budgets

- Monthly error budget: 1% (43.2 hours/month)
- Burn rate monitoring: Alert if burn rate > 2x

## Implementation Steps

### Step 1: Configure SLIs in Dynatrace
[Implementation details here]

## Monitoring and Alerting

- Alert when error budget burn rate exceeds 2x
- Dashboard: Real-time SLO status
"""
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create prompt from sample Discovery worksheet
        prompt = create_prompt_template(
            self.SAMPLE_DISCOVERY_WORKSHEET,
            "Dynatrace"
        )
        
        # Verify prompt includes Discovery content
        assert "Chatbot" in prompt
        assert "Service Owner" in prompt
        assert "Dynatrace" in prompt
        
        # Call API
        result = call_openai_api(mock_client, prompt, "gpt-4")
        
        # Format as document
        formatted = format_as_markdown_document(
            result,
            "Chatbot",
            "Dynatrace"
        )
        
        # Verify output format
        assert "# SLO Implementation Guide" in formatted
        assert "**Service:** Chatbot" in formatted
        assert "**Observability Platform:** Dynatrace" in formatted
        assert "**Generated:**" in formatted
        assert "SLODLC" in formatted
        
        # Verify content sections are present
        assert "Service Overview" in formatted
        assert "SLI Definitions" in formatted
        assert "SLO Targets" in formatted
        assert "Error Budgets" in formatted
        assert "Implementation Steps" in formatted
        assert "Monitoring and Alerting" in formatted
    
    def test_prompt_construction_with_sample_discovery(self):
        """Test prompt construction with sample Discovery worksheet."""
        prompt = create_prompt_template(
            self.SAMPLE_DISCOVERY_WORKSHEET,
            "Grafana"
        )
        
        # Verify all key elements are in prompt
        assert "SLODLC" in prompt
        assert "Grafana" in prompt
        assert "Chatbot" in prompt
        assert "Service Owner" in prompt
        assert "User Journeys" in prompt
        assert "SLI Definitions" in prompt
        assert "SLO Targets" in prompt
        assert "Error Budgets" in prompt
        assert "Implementation Steps" in prompt
        assert "Monitoring and Alerting" in prompt
    
    def test_token_estimation_with_sample_discovery(self):
        """Test token estimation with sample Discovery worksheet."""
        tokens = estimate_tokens(self.SAMPLE_DISCOVERY_WORKSHEET, "gpt-4")
        
        assert isinstance(tokens, int)
        assert tokens > 0
        # Sample worksheet should be well under limit
        assert tokens < 7000
    
    def test_token_limit_check_with_sample_discovery(self):
        """Test token limit checking with sample Discovery worksheet."""
        exceeds, tokens, limit = check_token_limit(
            self.SAMPLE_DISCOVERY_WORKSHEET,
            "Splunk",
            "gpt-4"
        )
        
        assert not exceeds  # Sample should not exceed limit
        assert tokens < limit
        assert limit == 7000  # GPT-4 limit

