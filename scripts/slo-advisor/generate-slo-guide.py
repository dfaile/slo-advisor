#!/usr/bin/env python3
"""
Generate SLO Implementation Guide from SLODLC Discovery worksheet.

This script processes a Discovery worksheet and generates a comprehensive
SLO Implementation Guide using OpenAI's API.
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

# Try to import tiktoken for accurate token counting, fallback to estimation
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent))

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package is not installed. Please install it with: pip install openai")
    sys.exit(1)

from utils import (
    read_file_content,
    sanitize_input,
    generate_error_document
)


def generate_output_filename(service_name: str, is_error: bool = False) -> str:
    """
    Generate output filename following the naming convention.
    
    Args:
        service_name: Name of the service
        is_error: Whether this is an error document (default: False)
        
    Returns:
        Filename following the convention: {service-name}-slo-implementation-guide.md
        or {service-name}-slo-implementation-guide-ERROR.md for errors
    """
    import re
    
    # Sanitize service name for filename (alphanumeric, hyphens, underscores only)
    sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '-', service_name)
    # Remove multiple consecutive hyphens
    sanitized_name = re.sub(r'-+', '-', sanitized_name)
    # Remove leading/trailing hyphens
    sanitized_name = sanitized_name.strip('-')
    
    # Ensure we have a valid name
    if not sanitized_name:
        sanitized_name = "service"
    
    # Convert to lowercase for consistency
    sanitized_name = sanitized_name.lower()
    
    if is_error:
        return f"{sanitized_name}-slo-implementation-guide-ERROR.md"
    else:
        return f"{sanitized_name}-slo-implementation-guide.md"


# Token limits for different models (approximate, leaving room for prompt template and response)
MODEL_TOKEN_LIMITS = {
    "gpt-4": 7000,  # 8K context, reserve ~1K for prompt template and response
    "gpt-4-turbo": 100000,  # 128K context, reserve ~28K
    "gpt-3.5-turbo": 14000,  # 16K context, reserve ~2K
}


def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Estimate the number of tokens in a text string.
    
    Uses tiktoken if available for accurate counting, otherwise uses character-based estimation.
    
    Args:
        text: Text to count tokens for
        model: Model name to use for token counting
        
    Returns:
        Estimated number of tokens
    """
    if HAS_TIKTOKEN:
        try:
            # Map model names to tiktoken encoding names
            encoding_map = {
                "gpt-4": "cl100k_base",
                "gpt-4-turbo": "cl100k_base",
                "gpt-3.5-turbo": "cl100k_base"
            }
            encoding_name = encoding_map.get(model, "cl100k_base")
            encoding = tiktoken.get_encoding(encoding_name)
            return len(encoding.encode(text))
        except Exception:
            # Fall back to estimation if tiktoken fails
            pass
    
    # Fallback: rough estimation (1 token ≈ 4 characters for English text)
    return len(text) // 4


def check_token_limit(discovery_content: str, observability_platform: str, 
                     model: str = "gpt-4") -> Tuple[bool, int, int]:
    """
    Check if Discovery worksheet content exceeds token limits for the model.
    
    Args:
        discovery_content: Content of the Discovery worksheet
        observability_platform: Selected observability platform
        model: OpenAI model to use
        
    Returns:
        Tuple of (exceeds_limit, discovery_tokens, limit)
    """
    # Estimate tokens in Discovery content
    discovery_tokens = estimate_tokens(discovery_content, model)
    
    # Get token limit for the model
    limit = MODEL_TOKEN_LIMITS.get(model, MODEL_TOKEN_LIMITS["gpt-4"])
    
    # Check if it exceeds the limit
    exceeds_limit = discovery_tokens > limit
    
    return exceeds_limit, discovery_tokens, limit


def chunk_discovery_content(discovery_content: str, max_tokens: int, 
                           model: str = "gpt-4") -> list[str]:
    """
    Chunk Discovery worksheet content to fit within token limits.
    
    Attempts to split on section boundaries (markdown headers) to preserve context.
    
    Args:
        discovery_content: Full Discovery worksheet content
        max_tokens: Maximum tokens per chunk
        model: Model name for token estimation
        
    Returns:
        List of content chunks
    """
    # Try to split on markdown headers (## or ###) to preserve section context
    import re
    
    # Split by major sections (## headers)
    sections = re.split(r'\n(##\s+.+?)\n', discovery_content)
    
    chunks = []
    current_chunk = ""
    current_tokens = 0
    
    i = 0
    while i < len(sections):
        section = sections[i]
        
        # If this is a header, include it with the next section
        if section.startswith('##'):
            if i + 1 < len(sections):
                section_with_header = section + '\n' + sections[i + 1]
                section_tokens = estimate_tokens(section_with_header, model)
                
                # If section alone exceeds limit, split it further
                if section_tokens > max_tokens:
                    # Split by subsections (### headers) or paragraphs
                    subsections = re.split(r'\n(###\s+.+?)\n', section_with_header)
                    for j in range(0, len(subsections), 2):
                        if j + 1 < len(subsections):
                            subsec = subsections[j] + '\n' + subsections[j + 1]
                        else:
                            subsec = subsections[j]
                        
                        subsec_tokens = estimate_tokens(subsec, model)
                        if current_tokens + subsec_tokens > max_tokens and current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = subsec
                            current_tokens = subsec_tokens
                        else:
                            current_chunk += '\n\n' + subsec if current_chunk else subsec
                            current_tokens += subsec_tokens
                else:
                    # Check if adding this section would exceed limit
                    if current_tokens + section_tokens > max_tokens and current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = section_with_header
                        current_tokens = section_tokens
                    else:
                        current_chunk += '\n\n' + section_with_header if current_chunk else section_with_header
                        current_tokens += section_tokens
                
                i += 2
                continue
            else:
                # Last section is a header, add to current chunk
                section_tokens = estimate_tokens(section, model)
                if current_tokens + section_tokens > max_tokens and current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = section
                    current_tokens = section_tokens
                else:
                    current_chunk += '\n\n' + section if current_chunk else section
                    current_tokens += section_tokens
                i += 1
        else:
            # Regular content
            section_tokens = estimate_tokens(section, model)
            if current_tokens + section_tokens > max_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = section
                current_tokens = section_tokens
            else:
                current_chunk += '\n\n' + section if current_chunk else section
                current_tokens += section_tokens
            i += 1
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks if chunks else [discovery_content]


def format_as_markdown_document(content: str, service_name: str, 
                                observability_platform: str) -> str:
    """
    Format OpenAI response as a complete Markdown document.
    
    Adds document header, metadata, and ensures proper Markdown formatting.
    
    Args:
        content: Raw content from OpenAI API response
        service_name: Name of the service
        observability_platform: Selected observability platform
        
    Returns:
        Formatted Markdown document as string
    """
    from datetime import datetime
    
    # Get current timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Create document header
    header = f"""# SLO Implementation Guide

**Service:** {service_name}  
**Observability Platform:** {observability_platform}  
**Generated:** {timestamp}  
**Methodology:** SLODLC (SLO Development Lifecycle)

---

"""
    
    # Clean up the content (remove any leading/trailing whitespace)
    cleaned_content = content.strip()
    
    # Ensure content starts with a heading if it doesn't already
    if not cleaned_content.startswith('#'):
        # Check if first line looks like it should be a heading
        first_line = cleaned_content.split('\n')[0] if cleaned_content else ""
        if first_line and len(first_line) < 100 and not first_line.startswith('#'):
            # Add a main heading if content doesn't have one
            cleaned_content = f"# {first_line}\n\n{cleaned_content[len(first_line):].lstrip()}"
    
    # Combine header and content
    formatted_document = header + cleaned_content
    
    # Ensure document ends with a newline
    if not formatted_document.endswith('\n'):
        formatted_document += '\n'
    
    return formatted_document


def create_prompt_template(discovery_content: str, observability_platform: str) -> str:
    """
    Create prompt template for OpenAI API to generate SLO Implementation Guide.
    
    Args:
        discovery_content: Content of the SLODLC Discovery worksheet
        observability_platform: Selected observability platform
        
    Returns:
        Complete prompt string for OpenAI API
    """
    prompt = """You are an SLO (Service Level Objective) expert specializing in the SLODLC (SLO Development Lifecycle) methodology. Your task is to generate a comprehensive SLO Implementation Guide based on a completed SLODLC Discovery worksheet.

## Context

The SLODLC (SLO Development Lifecycle) is a structured approach for implementing Service Level Objectives. After completing the Discovery phase, teams need a detailed Implementation Guide that translates the Discovery findings into actionable steps for configuring SLIs (Service Level Indicators) and SLOs in their observability platform.

## Observability Platform

The SLO Implementation Guide should be tailored for: **{observability_platform}**

Please provide platform-specific instructions, configuration examples, and best practices relevant to this observability platform.

## Discovery Worksheet Content

Below is the completed SLODLC Discovery worksheet:

```
{discovery_content}
```

## Instructions

Generate a comprehensive SLO Implementation Guide that matches the format and structure of professional SLO implementation documentation. The guide should be practical, actionable, and specific to the service described in the Discovery worksheet.

## Required Sections

Your SLO Implementation Guide MUST include the following sections:

1. **Service Overview**
   - Service name and description
   - Key stakeholders and owners
   - Business context and importance

2. **SLI Definitions**
   - Specific SLIs identified from the Discovery worksheet
   - SLI calculation methods
   - Data sources and metrics
   - Measurement approach

3. **SLO Targets**
   - Specific SLO targets (e.g., 99.9% availability, p95 latency < 200ms)
   - Target justification based on Discovery findings
   - Time windows (e.g., 30-day rolling window)

4. **Error Budgets**
   - Error budget calculations
   - Error budget policies
   - Burn rate considerations

5. **Implementation Steps**
   - Step-by-step instructions for configuring SLIs in {observability_platform}
   - Step-by-step instructions for configuring SLOs in {observability_platform}
   - Platform-specific configuration examples
   - Integration with existing monitoring

6. **Monitoring and Alerting**
   - Alerting rules based on error budget burn rate
   - Dashboard configuration recommendations
   - Notification channels
   - Escalation procedures

7. **Validation and Testing**
   - How to validate SLI/SLO configuration
   - Testing procedures
   - Verification steps

8. **Maintenance and Review**
   - Periodic review schedule
   - Update procedures
   - Continuous improvement recommendations

## Output Format

- Format the output as well-structured Markdown
- Use clear headings and subheadings
- Include code blocks for configuration examples
- Use tables where appropriate for clarity
- Ensure the document is professional and ready for use by engineering teams

## Important Notes

- Base all recommendations on the actual content of the Discovery worksheet
- Provide specific, actionable guidance rather than generic advice
- Include {observability_platform}-specific syntax and examples
- Ensure all SLI/SLO definitions are measurable and achievable
- Consider the service's dependencies and constraints mentioned in the Discovery worksheet

Begin generating the SLO Implementation Guide now.
""".format(
        observability_platform=observability_platform,
        discovery_content=discovery_content
    )
    
    return prompt


def initialize_openai_client() -> OpenAI:
    """
    Initialize OpenAI API client using API key from environment variable.
    
    Returns:
        Initialized OpenAI client
        
    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set
    """
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it before running this script."
        )
    
    if not api_key.strip():
        raise ValueError(
            "OPENAI_API_KEY environment variable is empty. "
            "Please provide a valid API key."
        )
    
    client = OpenAI(api_key=api_key)
    return client


def call_openai_api(client: OpenAI, prompt: str, model: str = "gpt-4", timeout: int = 120, 
                    max_retries: int = 3, initial_backoff: float = 1.0) -> str:
    """
    Call OpenAI API with constructed prompt to generate SLO Implementation Guide.
    
    Includes comprehensive error handling with retry logic and exponential backoff for:
    - Rate limiting
    - API failures
    - Timeouts
    - Invalid responses
    
    Args:
        client: Initialized OpenAI client
        prompt: Complete prompt string for generating the guide
        model: OpenAI model to use (default: "gpt-4", fallback: "gpt-3.5-turbo")
        timeout: Request timeout in seconds (default: 120)
        max_retries: Maximum number of retry attempts for transient failures (default: 3)
        initial_backoff: Initial backoff delay in seconds (default: 1.0)
        
    Returns:
        Generated SLO Implementation Guide content as string
        
    Raises:
        ValueError: If API key is invalid or response is invalid
        TimeoutError: If request times out after all retries
        Exception: For other API failures with descriptive messages
    """
    try:
        from openai import RateLimitError, APIError, APIConnectionError, APITimeoutError
        
        # Try GPT-4 first, fallback to GPT-3.5-turbo if not available
        models_to_try = [model, "gpt-3.5-turbo"] if model == "gpt-4" else [model]
        
        for model_name in models_to_try:
            # Retry logic with exponential backoff for transient failures
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert in SLO (Service Level Objective) implementation and the SLODLC methodology. Generate comprehensive, actionable SLO Implementation Guides."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=4000,  # Adjust based on expected output length
                    timeout=timeout
                )
                
                # Validate response structure
                if not response or not response.choices:
                    raise ValueError("OpenAI API returned invalid response structure: no choices")
                
                if len(response.choices) == 0:
                    raise ValueError("OpenAI API returned invalid response: empty choices array")
                
                # Extract the generated content
                generated_content = response.choices[0].message.content
                
                if not generated_content:
                    raise ValueError("OpenAI API returned empty content in response")
                
                if not generated_content.strip():
                    raise ValueError("OpenAI API returned only whitespace in response")
                
                    return generated_content
                        
                except RateLimitError as e:
                    last_exception = e
                    error_msg = (
                        f"Rate limit exceeded for {model_name} (attempt {attempt + 1}/{max_retries + 1}). "
                    )
                    
                    # Rate limits are transient - retry with exponential backoff
                    if attempt < max_retries:
                        backoff_time = initial_backoff * (2 ** attempt)
                        error_msg += f"Retrying in {backoff_time:.1f} seconds..."
                        print(f"Warning: {error_msg}")
                        time.sleep(backoff_time)
                        continue
                    else:
                        error_msg += "Max retries exceeded. Please wait before retrying or use a different API key."
                        # If GPT-4 rate limited after retries, try GPT-3.5-turbo
                        if model_name == "gpt-4" and "gpt-3.5-turbo" in models_to_try:
                            print(f"Warning: {error_msg} Trying gpt-3.5-turbo...")
                            break  # Break retry loop, try next model
                        else:
                            raise Exception(error_msg) from e
                            
                except APITimeoutError as e:
                    last_exception = e
                    error_msg = (
                        f"Request to {model_name} timed out (attempt {attempt + 1}/{max_retries + 1}). "
                    )
                    
                    # Timeouts are transient - retry with exponential backoff
                    if attempt < max_retries:
                        backoff_time = initial_backoff * (2 ** attempt)
                        error_msg += f"Retrying in {backoff_time:.1f} seconds..."
                        print(f"Warning: {error_msg}")
                        time.sleep(backoff_time)
                        continue
                    else:
                        error_msg += (
                            f"Max retries exceeded after {timeout} seconds. "
                            "The prompt may be too long or the API is experiencing delays."
                        )
                        # If GPT-4 times out after retries, try GPT-3.5-turbo
                        if model_name == "gpt-4" and "gpt-3.5-turbo" in models_to_try:
                            print(f"Warning: {error_msg} Trying gpt-3.5-turbo...")
                            break  # Break retry loop, try next model
                        else:
                            raise TimeoutError(error_msg) from e
                            
                except APIConnectionError as e:
                    last_exception = e
                    error_msg = (
                        f"Connection error with {model_name} (attempt {attempt + 1}/{max_retries + 1}). "
                    )
                    
                    # Connection errors are transient - retry with exponential backoff
                    if attempt < max_retries:
                        backoff_time = initial_backoff * (2 ** attempt)
                        error_msg += f"Retrying in {backoff_time:.1f} seconds..."
                        print(f"Warning: {error_msg}")
                        time.sleep(backoff_time)
                        continue
                    else:
                        error_msg += "Max retries exceeded. Please check your internet connection and try again."
                        # If GPT-4 connection fails after retries, try GPT-3.5-turbo
                        if model_name == "gpt-4" and "gpt-3.5-turbo" in models_to_try:
                            print(f"Warning: {error_msg} Trying gpt-3.5-turbo...")
                            break  # Break retry loop, try next model
                        else:
                            raise Exception(error_msg) from e
                            
                except APIError as e:
                    last_exception = e
                    error_msg = f"OpenAI API error for {model_name}: {str(e)}"
                    
                    # Check for authentication errors (not transient - don't retry)
                    if "authentication" in str(e).lower() or "api key" in str(e).lower():
                        raise ValueError(
                            "Invalid OpenAI API key. Please check your OPENAI_API_KEY environment variable."
                        ) from e
                    
                    # Some API errors are transient - retry with exponential backoff
                    # Check if error code suggests retry is appropriate (5xx errors)
                    error_str = str(e).lower()
                    is_transient = any(code in error_str for code in ['500', '502', '503', '504', '429'])
                    
                    if is_transient and attempt < max_retries:
                        backoff_time = initial_backoff * (2 ** attempt)
                        print(f"Warning: {error_msg} (attempt {attempt + 1}/{max_retries + 1}). Retrying in {backoff_time:.1f} seconds...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        # If GPT-4 API error after retries, try GPT-3.5-turbo
                        if model_name == "gpt-4" and "gpt-3.5-turbo" in models_to_try and is_transient:
                            print(f"Warning: {error_msg} Trying gpt-3.5-turbo...")
                            break  # Break retry loop, try next model
                        else:
                            raise Exception(error_msg) from e
                            
                except ValueError as e:
                    # Invalid response - don't retry
                    raise
                    
                except Exception as e:
                    last_exception = e
                    # Other unexpected errors - may be transient
                    error_msg = f"Unexpected error calling {model_name}: {str(e)}"
                    
                    # For unexpected errors, retry once with backoff
                    if attempt < max_retries:
                        backoff_time = initial_backoff * (2 ** attempt)
                        print(f"Warning: {error_msg} (attempt {attempt + 1}/{max_retries + 1}). Retrying in {backoff_time:.1f} seconds...")
                        time.sleep(backoff_time)
                        continue
                    else:
                        # If GPT-4 fails after retries, try GPT-3.5-turbo
                        if model_name == "gpt-4" and "gpt-3.5-turbo" in models_to_try:
                            print(f"Warning: {error_msg} Trying gpt-3.5-turbo...")
                            break  # Break retry loop, try next model
                        else:
                            raise Exception(error_msg) from e
            
            # If we exhausted retries for this model, continue to next model
            if last_exception and model_name != models_to_try[-1]:
                continue
        
        # If we get here, all models failed
        raise Exception("All OpenAI models failed after retries")
        
    except (ValueError, TimeoutError):
        # Re-raise these specific exceptions
        raise
    except Exception as e:
        # Wrap other exceptions
        raise Exception(f"OpenAI API call failed: {str(e)}") from e


def main():
    """
    Main function for generating SLO Implementation Guide.
    
    This function will be expanded in subsequent tasks to include:
    - Prompt template construction
    - OpenAI API integration
    - Document generation
    - Error handling
    """
    parser = argparse.ArgumentParser(
        description='Generate SLO Implementation Guide from Discovery worksheet'
    )
    parser.add_argument(
        '--discovery-worksheet',
        type=str,
        required=False,
        help='Path to the Discovery worksheet Markdown file'
    )
    parser.add_argument(
        '--observability-platform',
        type=str,
        required=False,
        help='Observability platform (Dynatrace, Grafana, LogicMonitor, Splunk, etc.)'
    )
    parser.add_argument(
        '--service-name',
        type=str,
        required=False,
        help='Service name for the SLO Implementation Guide'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        required=False,
        help='Output file path for the generated guide'
    )
    parser.add_argument(
        '--error',
        action='store_true',
        help='Generate error document instead of SLO guide'
    )
    parser.add_argument(
        '--error-message',
        type=str,
        help='Error message for error document generation'
    )
    
    args = parser.parse_args()
    
    # Handle error document generation
    if args.error:
        if not args.service_name or not args.output_file:
            print("Error: --service-name and --output-file are required for error document generation")
            sys.exit(1)
        
        error_details = args.error_message or "An error occurred during SLO Implementation Guide generation"
        error_doc = generate_error_document(
            error_details,
            args.service_name
        )
        
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(error_doc)
        
        print(f"Error document generated: {args.output_file}")
        return
    
    # Validate required arguments for normal generation
    if not args.discovery_worksheet or not args.observability_platform or not args.service_name:
        print("Error: --discovery-worksheet, --observability-platform, and --service-name are required")
        sys.exit(1)
    
    if not args.output_file:
        args.output_file = generate_output_filename(args.service_name, is_error=False)
    
    # Read Discovery worksheet content
    try:
        discovery_content = read_file_content(args.discovery_worksheet)
    except Exception as e:
        print(f"Error reading Discovery worksheet: {str(e)}")
        sys.exit(1)
    
    # Sanitize input to prevent prompt injection
    sanitized_discovery_content = sanitize_input(discovery_content)
    
    # Construct prompt from Discovery worksheet and platform selection
    prompt = create_prompt_template(
        discovery_content=sanitized_discovery_content,
        observability_platform=args.observability_platform
    )
    
    print(f"Processing Discovery worksheet for service: {args.service_name}")
    print(f"Observability platform: {args.observability_platform}")
    print(f"Output file: {args.output_file}")
    print(f"Prompt constructed ({len(prompt)} characters)")
    
    # Initialize OpenAI client
    try:
        print("\nInitializing OpenAI client...")
        client = initialize_openai_client()
        print("✓ Client initialized")
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    
    # Call OpenAI API to generate guide
    try:
        print("Calling OpenAI API to generate SLO Implementation Guide...")
        generated_content = call_openai_api(client, prompt, "gpt-4")
        print(f"✓ Guide generated ({len(generated_content)} characters)")
    except Exception as e:
        print(f"Error generating guide: {str(e)}")
        # Generate error document
        error_doc = generate_error_document(
            f"SLO Implementation Guide generation failed: {str(e)}",
            args.service_name,
            error_details=str(e)
        )
        error_filename = generate_output_filename(args.service_name, is_error=True)
        with open(error_filename, 'w', encoding='utf-8') as f:
            f.write(error_doc)
        print(f"Error document saved to: {error_filename}")
        sys.exit(1)
    
    # Format as Markdown document
    formatted_doc = format_as_markdown_document(
        generated_content,
        args.service_name,
        args.observability_platform
    )
    
    # Write to output file
    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_doc)
        print(f"\n✓ SLO Implementation Guide saved to: {args.output_file}")
    except Exception as e:
        print(f"Error writing output file: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

