#!/usr/bin/env python3
"""
End-to-end test script for SLO Implementation Guide generation.

Tests the complete workflow:
1. Validation of Discovery worksheet
2. OpenAI API call
3. Document generation
4. File creation

Can be run with mocked API calls (for CI/CD) or real API calls (for manual testing).
"""

import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from validate_discovery_worksheet import validate_discovery_worksheet
from generate_slo_guide import (
    create_prompt_template,
    initialize_openai_client,
    call_openai_api,
    format_as_markdown_document,
    generate_output_filename,
    sanitize_input
)
from utils import read_file_content


def create_sample_discovery_worksheet() -> str:
    """Create a sample Discovery worksheet for testing."""
    return """# SLODLC Discovery Worksheet

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

## 4. Observe System Behavior

### 4.1 Data sources

- Service: Web Server
  - Metrics: Latency, Availability
  - Observability System: DataObserverOne

### 4.2 SLIs

1. Web Server Latency SLI: Proportion of HTTP GET requests that have a response in 600ms
2. Chatbot Latency SLI: Proportion of Chatbot responses that have a response in 200ms
"""


def test_end_to_end_with_mock(use_real_api: bool = False):
    """
    Test end-to-end workflow with optional real API calls.
    
    Args:
        use_real_api: If True, use real OpenAI API (requires OPENAI_API_KEY).
                     If False, use mocked API calls.
    """
    print("=" * 70)
    print("End-to-End Test: SLO Implementation Guide Generation")
    print("=" * 70)
    
    # Step 1: Create sample Discovery worksheet file
    print("\n[Step 1] Creating sample Discovery worksheet...")
    sample_content = create_sample_discovery_worksheet()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(sample_content)
        discovery_file = f.name
    
    try:
        # Step 2: Validate Discovery worksheet
        print("\n[Step 2] Validating Discovery worksheet...")
        is_valid, message = validate_discovery_worksheet(discovery_file)
        
        if not is_valid:
            print(f"❌ Validation failed: {message}")
            return False
        
        print(f"✓ Validation passed: {message}")
        
        # Step 3: Read and sanitize Discovery content
        print("\n[Step 3] Reading and sanitizing Discovery worksheet content...")
        discovery_content = read_file_content(discovery_file)
        sanitized_content = sanitize_input(discovery_content)
        print(f"✓ Content read and sanitized ({len(sanitized_content)} characters)")
        
        # Step 4: Construct prompt
        print("\n[Step 4] Constructing prompt template...")
        observability_platform = "Dynatrace"
        service_name = "chatbot"
        
        prompt = create_prompt_template(sanitized_content, observability_platform)
        print(f"✓ Prompt constructed ({len(prompt)} characters)")
        
        # Step 5: Initialize OpenAI client
        print("\n[Step 5] Initializing OpenAI client...")
        if use_real_api:
            if not os.getenv('OPENAI_API_KEY'):
                print("❌ OPENAI_API_KEY not set. Cannot use real API.")
                return False
            client = initialize_openai_client()
            print("✓ OpenAI client initialized (real API)")
        else:
            # Mock client for testing
            from unittest.mock import MagicMock
            client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = """# Service Overview

The Chatbot service enables natural language conversations with customers.

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
1. Navigate to SLO configuration
2. Create new SLO for Web Server Latency
3. Set target to 600ms p95
4. Configure data source from DataObserverOne

### Step 2: Configure Chatbot Latency SLO
1. Create new SLO for Chatbot Latency
2. Set target to 200ms p95
3. Link to Chatbot service metrics

## Monitoring and Alerting

- Alert when error budget burn rate exceeds 2x
- Dashboard: Real-time SLO status
- Notification channels: Slack, PagerDuty
"""
            client.chat.completions.create.return_value = mock_response
            print("✓ OpenAI client initialized (mocked)")
        
        # Step 6: Call OpenAI API
        print("\n[Step 6] Calling OpenAI API...")
        if use_real_api:
            try:
                generated_content = call_openai_api(client, prompt, "gpt-4")
                print(f"✓ API call successful ({len(generated_content)} characters)")
            except Exception as e:
                print(f"❌ API call failed: {str(e)}")
                return False
        else:
            generated_content = call_openai_api(client, prompt, "gpt-4")
            print(f"✓ API call successful (mocked, {len(generated_content)} characters)")
        
        # Step 7: Format as Markdown document
        print("\n[Step 7] Formatting as Markdown document...")
        formatted_doc = format_as_markdown_document(
            generated_content,
            service_name,
            observability_platform
        )
        print(f"✓ Document formatted ({len(formatted_doc)} characters)")
        
        # Step 8: Generate output filename
        print("\n[Step 8] Generating output filename...")
        output_filename = generate_output_filename(service_name, is_error=False)
        print(f"✓ Output filename: {output_filename}")
        
        # Step 9: Write to file
        print("\n[Step 9] Writing document to file...")
        output_path = Path(__file__).parent.parent.parent / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_doc)
        
        print(f"✓ Document written to: {output_path}")
        
        # Step 10: Verify file exists and has content
        print("\n[Step 10] Verifying output file...")
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"✓ File exists ({file_size} bytes)")
            
            # Verify content
            with open(output_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
            
            assert "# SLO Implementation Guide" in saved_content
            assert service_name in saved_content
            assert observability_platform in saved_content
            assert "SLI Definitions" in saved_content or "SLI" in saved_content
            
            print("✓ File content verified")
        else:
            print("❌ Output file not found")
            return False
        
        print("\n" + "=" * 70)
        print("✅ End-to-End Test PASSED")
        print("=" * 70)
        print(f"\nGenerated file: {output_path}")
        print("\nTo test with real API, run:")
        print("  OPENAI_API_KEY=your-key python scripts/slo-advisor/test_end_to_end.py --real-api")
        
        return True
        
    except Exception as e:
        print(f"\n❌ End-to-End Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if os.path.exists(discovery_file):
            os.unlink(discovery_file)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='End-to-end test for SLO Implementation Guide generation')
    parser.add_argument(
        '--real-api',
        action='store_true',
        help='Use real OpenAI API (requires OPENAI_API_KEY environment variable)'
    )
    
    args = parser.parse_args()
    
    success = test_end_to_end_with_mock(use_real_api=args.real_api)
    sys.exit(0 if success else 1)

