# SLO Advisor

Automatically generate SLO Implementation Guides from completed SLODLC Discovery worksheets using AI.

## Overview

SLO Advisor is a Backstage software template that streamlines the creation of SLO (Service Level Objective) Implementation Guides. After teams complete the Discovery phase of the SLODLC (SLO Development Lifecycle) process, this tool automatically generates comprehensive, actionable SLO Implementation Guides tailored to their observability platform.

## Problem Statement

Currently, teams must manually create SLO Implementation Guides after completing the Discovery phase of the SLODLC process. This is time-consuming, error-prone, and inconsistent. Automating this step accelerates SLO adoption and ensures consistent, high-quality implementation guides across all teams.

## Solution

SLO Advisor integrates a Backstage software template with a GitHub Action workflow that:
- Accepts uploaded SLODLC Discovery worksheets (Markdown format)
- Processes the content through OpenAI's API
- Generates comprehensive SLO Implementation Guides
- Commits the guides to a repository for version control and team collaboration

## Features

### Discovery Worksheet Upload

- **Markdown File Support**: Upload completed SLODLC Discovery worksheets in Markdown format (`.md` files only)
- **File Validation**: Comprehensive validation ensures:
  - File extension is `.md`
  - File size is within limits (max 5MB)
  - Content is text-based (not binary)
  - No malicious patterns (script tags, executable code, etc.)
- **Security Checks**: Automatic detection and blocking of potentially dangerous content

### Observability Platform Selection

- **Pre-configured Platforms**: Choose from popular observability platforms:
  - Dynatrace
  - Grafana
  - LogicMonitor
  - Splunk
- **Custom Platform Support**: Select "Other" option to specify a custom observability platform
- **Platform-Specific Generation**: Guides are tailored to the selected platform with:
  - Platform-specific configuration examples
  - Platform-specific syntax and best practices
  - Integration instructions for the chosen platform

### Automated SLO Guide Generation

- **AI-Powered Generation**: Uses OpenAI's GPT-4 (with automatic fallback to GPT-3.5-turbo) to generate comprehensive guides
- **Comprehensive Content**: Generated guides include all required sections:
  - Service Overview
  - SLI Definitions
  - SLO Targets
  - Error Budgets
  - Implementation Steps (platform-specific)
  - Monitoring and Alerting
  - Validation and Testing
  - Maintenance and Review
- **Intelligent Processing**:
  - Token limit checking and automatic chunking for large Discovery worksheets
  - Input sanitization to prevent prompt injection attacks
  - Retry logic with exponential backoff for transient API failures
  - Automatic model fallback on errors
- **Error Handling**: Comprehensive error handling with:
  - Clear error messages
  - Error document generation on failures
  - Automatic error document commits to repository

### Version Control Integration

- **Automatic Commits**: Generated guides are automatically committed to your repository
- **Descriptive Commit Messages**: Clear commit messages identify the service and guide type
- **File Naming Convention**: Consistent naming: `{service-name}-slo-implementation-guide.md`
- **Error Document Tracking**: Failed generations create error documents: `{service-name}-slo-implementation-guide-ERROR.md`

## Key Components

- **Backstage Template** (`template.yaml`): Software template with form fields for Discovery worksheet upload and platform selection
- **GitHub Action Workflow** (`.github/workflows/generate-slo-guide.yml`): Automated workflow that processes submissions and generates guides
- **Validation Scripts** (`scripts/slo-advisor/validate-discovery-worksheet.py`): Validates uploaded files for security and format compliance
- **Generation Scripts** (`scripts/slo-advisor/generate-slo-guide.py`): Handles OpenAI API integration and document generation

## Technology Stack

- **Backstage**: Software template framework
- **GitHub Actions**: Workflow automation
- **Python**: Scripting and validation
- **OpenAI API**: AI-powered document generation
- **Markdown**: Document format

## Installation and Setup

### Prerequisites

- Backstage instance (v1.0 or later)
- GitHub repository with Actions enabled
- OpenAI API key
- Python 3.8+ (for local development and testing)

### Backstage Template Integration

1. **Add Template to Backstage**

   Copy the `template.yaml` file to your Backstage templates directory:
   ```bash
   cp template.yaml <your-backstage-instance>/templates/slo-discovery-template.yaml
   ```

   Or if using a remote template repository, ensure `template.yaml` is accessible via your Backstage configuration.

2. **Configure Backstage Template Location**

   Update your Backstage `app-config.yaml` to include the template location:
   ```yaml
   catalog:
     locations:
       - type: url
         target: https://github.com/YOUR-ORG/slo-advisor/blob/main/template.yaml
   ```
   
   Replace `YOUR-ORG` with your GitHub organization or username.

3. **Register Template in Backstage**

   The template should appear in your Backstage "Create Component" page. If it doesn't:
   - Verify the template YAML is valid
   - Check Backstage logs for parsing errors
   - Ensure the template location is properly configured

### GitHub Action Setup

1. **Clone or Fork Repository**

   ```bash
   git clone https://github.com/YOUR-ORG/slo-advisor.git
   cd slo-advisor
   ```
   
   Replace `YOUR-ORG` with your GitHub organization or username, or use the repository URL where you've deployed this project.

2. **Install Python Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure GitHub Secrets**

   See the [GitHub Secrets Configuration](#github-secrets-configuration) section below for detailed instructions.

4. **Verify Workflow File**

   Ensure `.github/workflows/generate-slo-guide.yml` is present in your repository. The workflow will be automatically available for manual triggering via `workflow_dispatch`.

### Local Development Setup

1. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**

   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

3. **Run Tests**

   ```bash
   pytest
   ```

4. **Test Validation Script**

   ```bash
   python scripts/slo-advisor/validate-discovery-worksheet.py <path-to-worksheet.md>
   ```

5. **Test Generation Script (Mocked)**

   ```bash
   python scripts/slo-advisor/test_end_to_end.py
   ```

6. **Test Generation Script (Real API)**

   ```bash
   python scripts/slo-advisor/test_end_to_end.py --real-api
   ```

## Usage

### Using the Backstage Template

1. **Access the Template**

   - Navigate to your Backstage instance
   - Go to "Create Component" or "Software Templates"
   - Find and select "SLO Discovery Template"

2. **Fill Out the Form**

   The template form includes the following fields:

   **Discovery Worksheet**
   - Upload your completed SLODLC Discovery worksheet
   - Must be a Markdown file (`.md` extension)
   - Maximum file size: 5MB
   - File will be validated for security and format compliance

   **Observability Platform**
   - Select your observability platform from the dropdown:
     - Dynatrace
     - Grafana
     - LogicMonitor
     - Splunk
     - Other (if you select "Other", a text field will appear for you to specify your platform)

   **Service Name**
   - Enter the name of the service for which you're generating the SLO Implementation Guide
   - Must be alphanumeric with hyphens and underscores only (e.g., `my-service`, `api_gateway`)
   - This will be used in the generated guide filename

   **Repository Name/URL** (Optional)
   - Specify the repository where the generated guide should be committed
   - Default: `slo_implementation_guides`
   - Can be a repository name or full URL

3. **Submit the Form**

   - Click "Create" or "Submit" to trigger the workflow
   - The template will:
     1. Validate your Discovery worksheet
     2. Trigger the GitHub Action workflow
     3. Process the worksheet through OpenAI API
     4. Generate the SLO Implementation Guide
     5. Commit the guide to the specified repository

4. **Check Results**

   - Navigate to your repository
   - Look for a new commit with the message: "Add SLO Implementation Guide for [Service Name]"
   - The generated guide will be in the file: `{service-name}-slo-implementation-guide.md`
   - If generation failed, check for an error document: `{service-name}-slo-implementation-guide-ERROR.md`

### Manual Workflow Trigger (Alternative)

If you prefer to trigger the workflow manually without using Backstage:

1. **Go to GitHub Actions**

   - Navigate to your repository on GitHub
   - Click on the "Actions" tab
   - Select "Generate SLO Implementation Guide" workflow

2. **Run Workflow**

   - Click "Run workflow"
   - Fill in the required inputs:
     - **Discovery worksheet content**: Paste your Markdown Discovery worksheet content
     - **Observability platform**: Select or enter your platform
     - **Service name**: Enter your service name
     - **Repository name**: (Optional) Specify target repository
   - Click "Run workflow"

3. **Monitor Progress**

   - Watch the workflow execution in real-time
   - Check the logs for any errors
   - Once complete, verify the generated guide in your repository

## GitHub Secrets Configuration

### Required Secret: OPENAI_API_KEY

The workflow requires an OpenAI API key to generate SLO Implementation Guides. This key must be stored as a GitHub Secret for security.

#### Getting an OpenAI API Key

1. **Create OpenAI Account** (if you don't have one)
   - Go to [https://platform.openai.com](https://platform.openai.com)
   - Sign up or log in to your account

2. **Generate API Key**
   - Navigate to API Keys section: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Click "Create new secret key"
   - Give it a name (e.g., "SLO Advisor")
   - Copy the key immediately (you won't be able to see it again)
   - Format: `sk-...` (starts with `sk-`)

3. **Add Billing** (if required)
   - OpenAI API usage is billed per token
   - Ensure your account has billing configured
   - Monitor usage at [https://platform.openai.com/usage](https://platform.openai.com/usage)

#### Adding the Secret to GitHub

1. **Navigate to Repository Settings**
   - Go to your GitHub repository
   - Click on "Settings" (top menu)
   - In the left sidebar, click "Secrets and variables" → "Actions"

2. **Create New Secret**
   - Click "New repository secret" button
   - **Name**: Enter exactly `OPENAI_API_KEY` (case-sensitive)
   - **Secret**: Paste your OpenAI API key (the `sk-...` value)
   - Click "Add secret"

3. **Verify Secret**
   - The secret should appear in your secrets list
   - You can update it later if needed, but you cannot view the value again

#### Security Best Practices

- **Never commit the API key** to the repository
- **Never share the API key** in logs, issues, or pull requests
- **Use GitHub Secrets** exclusively for storing the key
- **Rotate the key** if it's ever exposed
- **Use organization secrets** if managing multiple repositories
- **Monitor API usage** regularly to detect unauthorized use

#### Cost Considerations

- **GPT-4**: More expensive but higher quality (~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens)
- **GPT-3.5-turbo**: More cost-effective (~$0.0015 per 1K input tokens, ~$0.002 per 1K output tokens)
- **Typical Guide Generation**: ~2000-4000 tokens per guide
- **Estimated Cost**: $0.10-$0.30 per guide (GPT-4) or $0.01-$0.02 per guide (GPT-3.5-turbo)

The workflow automatically falls back to GPT-3.5-turbo if GPT-4 is unavailable or rate-limited.

#### Troubleshooting API Key Issues

**Error: "OPENAI_API_KEY environment variable is not set"**
- Verify the secret is named exactly `OPENAI_API_KEY`
- Check that the secret exists in repository Settings → Secrets
- Ensure the workflow has access to secrets (check workflow permissions)

**Error: "Invalid OpenAI API key"**
- Verify the key starts with `sk-`
- Check that the key hasn't been revoked in OpenAI dashboard
- Ensure there are no extra spaces when copying the key
- Try regenerating the key in OpenAI dashboard

**Error: "Insufficient quota"**
- Check your OpenAI account billing status
- Verify you have available credits/quota
- Monitor usage at OpenAI dashboard

## GitHub Action Workflow Setup and Configuration

### Workflow Overview

The GitHub Action workflow (`generate-slo-guide.yml`) automates the entire SLO Implementation Guide generation process. It can be triggered either:
- Automatically from the Backstage template (via `github:actions:dispatch`)
- Manually from the GitHub Actions UI (via `workflow_dispatch`)

### Workflow Configuration Requirements

#### 1. Required GitHub Secrets

**OPENAI_API_KEY** (Required)
- **Purpose**: Authenticates with OpenAI API to generate guides
- **How to Add**:
  1. Go to repository Settings → Secrets and variables → Actions
  2. Click "New repository secret"
  3. Name: `OPENAI_API_KEY`
  4. Value: Your OpenAI API key (starts with `sk-`)
  5. Click "Add secret"
- **Security**: Never commit this key to the repository. Always use GitHub Secrets.

#### 2. Workflow Inputs

The workflow accepts the following inputs when triggered:

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `discoveryWorksheet` | string | Yes | Complete Markdown content of the Discovery worksheet |
| `observabilityPlatform` | string | Yes | Selected observability platform (Dynatrace, Grafana, LogicMonitor, Splunk, or custom) |
| `serviceName` | string | Yes | Service name for the SLO Implementation Guide |
| `repositoryName` | string | No | Target repository (defaults to current repository) |

#### 3. Workflow Steps

The workflow executes the following steps:

1. **Checkout Repository**: Checks out the repository code
2. **Set up Python**: Configures Python 3.11 environment
3. **Install Dependencies**: Installs packages from `requirements.txt`
4. **Validate Discovery Worksheet**: Validates the uploaded worksheet for:
   - File extension (`.md` only)
   - File size (max 5MB)
   - Text-based content (not binary)
   - No malicious patterns
5. **Generate SLO Implementation Guide**: 
   - Calls OpenAI API with constructed prompt
   - Handles errors with retry logic
   - Formats response as Markdown document
6. **Commit Generated Guide**: Commits the guide to the repository with descriptive message
7. **Error Handling**: On failure, generates and commits an error document

#### 4. Workflow Permissions

The workflow requires the following permissions:

- **Contents: write**: To commit generated guides to the repository
- **Actions: read**: To read workflow configuration

These are typically granted automatically, but verify in repository Settings → Actions → General → Workflow permissions.

#### 5. Repository Configuration

**Required Files in Repository**:
- `.github/workflows/generate-slo-guide.yml` - The workflow file
- `scripts/slo-advisor/validate-discovery-worksheet.py` - Validation script
- `scripts/slo-advisor/generate-slo-guide.py` - Generation script
- `scripts/slo-advisor/utils.py` - Utility functions
- `requirements.txt` - Python dependencies

**Repository Structure**:
```
slo-advisor/
├── .github/
│   └── workflows/
│       └── generate-slo-guide.yml
├── scripts/
│   └── slo-advisor/
│       ├── validate-discovery-worksheet.py
│       ├── generate-slo-guide.py
│       └── utils.py
├── requirements.txt
└── template.yaml
```

#### 6. Workflow Execution Environment

- **Runner**: `ubuntu-latest`
- **Python Version**: 3.11
- **Timeout**: Default GitHub Actions timeout (6 hours for public repos, configurable)

#### 7. Error Handling

The workflow includes comprehensive error handling:

- **Validation Failures**: Workflow stops if validation fails, preventing invalid content from being processed
- **API Failures**: On OpenAI API errors:
  - Retries with exponential backoff (up to 3 retries)
  - Falls back to GPT-3.5-turbo if GPT-4 fails
  - Generates error document if all retries fail
- **Error Documents**: Failed generations create `{service-name}-slo-implementation-guide-ERROR.md` with:
  - Error message
  - Timestamp
  - Service name
  - Error details

#### 8. Commit Configuration

The workflow automatically configures Git for commits:

- **User Email**: `action@github.com`
- **User Name**: `GitHub Action`
- **Commit Message Format**: `Add SLO Implementation Guide for {service-name}`

#### 9. Testing the Workflow

**Manual Testing**:
1. Go to Actions tab in GitHub
2. Select "Generate SLO Implementation Guide"
3. Click "Run workflow"
4. Fill in test inputs
5. Monitor execution logs

**Local Testing**:
Use the end-to-end test script:
```bash
python scripts/slo-advisor/test_end_to_end.py --real-api
```

#### 10. Troubleshooting

**Common Issues**:

- **"OPENAI_API_KEY not found"**: Ensure the secret is set in repository Settings → Secrets
- **"Workflow not found"**: Verify `.github/workflows/generate-slo-guide.yml` exists and is committed
- **"Validation failed"**: Check that the Discovery worksheet is valid Markdown and under 5MB
- **"API rate limit exceeded"**: Wait before retrying, or check your OpenAI API quota
   - **"Commit failed"**: Verify repository has write permissions enabled for GitHub Actions

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

See LICENSE file for details.

## Support

For issues, questions, or contributions:
- Open an issue in the GitHub repository
- Check the [SLODLC documentation](https://www.slodlc.com) for Discovery worksheet guidance
- Review the troubleshooting section above for common issues

## SLODLC Discovery Worksheet Format

### Overview

The SLO Advisor tool requires a completed SLODLC (SLO Development Lifecycle) Discovery worksheet in Markdown format. The Discovery worksheet is the first phase of the SLODLC methodology and captures essential information about your service, user journeys, dependencies, and system behavior.

### Official Resources

- **SLODLC Website**: [https://www.slodlc.com](https://www.slodlc.com)
- **Discovery Worksheet Example**: [https://www.slodlc.com/examples/discovery-example](https://www.slodlc.com/examples/discovery-example)
- **Discovery Worksheet Template**: [https://www.slodlc.com/templates](https://www.slodlc.com/templates) (if available)

### Required Sections

A complete Discovery worksheet should include the following sections:

1. **Service Description**
   - Service name and description
   - Service boundaries and scope
   - Dependencies outside your control
   - Impact of unreliability
   - Performance characteristics

2. **Owner and Stakeholders**
   - Service owner
   - Key stakeholders
   - Responsible teams

3. **Service Business Context**
   - Who cares about this service
   - Why they use it
   - What happens if they can't
   - Alternatives available
   - Business goals and revenue impact

4. **Service Expectations**
   - Existing SLAs and their levels
   - Who defined reliability expectations
   - Unwritten/informal expectations

5. **Pain Points**
   - Existing pain points
   - Elaboration on pain points

6. **User Journeys & Expectations**
   - Define the users of the service
   - User journeys
   - User expectations per journey
   - Prioritization

7. **Dependencies and Constraints**
   - Architectural dependencies
   - Hard vs. soft dependencies
   - Constraints that impact priorities

8. **Observe System Behavior**
   - List of outages with business impact
   - Case studies of outages
   - Data sources and retention policies
   - Existing SLIs (if any)
   - Alerting tools and policies

### Example Discovery Worksheet Structure

Here's a minimal example structure to get you started:

```markdown
# SLODLC Discovery Worksheet

## 1. Service

### 1.1 Service description
[Describe your service, its goals, and scope]

### 1.2 Owner and Stakeholders
- Service Owner: [Name, Title]
- Stakeholders: [List of stakeholders]

### 1.3 Service Business Context
- Who cares: [Who uses/cares about this service]
- Why: [Why they use it]
- Impact: [What happens if unavailable]

## 2. Prioritize User Journeys & Expectations

### 2.1 Define The Users
[Primary users of the service]

### 2.2 Users Journeys
[Key user journeys]

### 2.3 User Expectations per Journey
[Expected performance and reliability]

## 3. Analyze Dependencies

### 3.1 Architectural dependencies
[Dependencies and constraints]

## 4. Observe System Behavior

### 4.1 Data sources
[Observability systems and metrics]

### 4.2 SLIs
[Existing SLIs if any]
```

### Format Requirements

- **File Format**: Markdown (`.md` extension)
- **Encoding**: UTF-8
- **Maximum Size**: 5MB
- **Structure**: Use Markdown headers (`#`, `##`, `###`) for sections
- **Content**: Text-based only (no binary content)

### Getting Started

1. **Use the Official Template**: Download the Discovery worksheet template from [SLODLC website](https://www.slodlc.com)
2. **Review the Example**: Study the [Discovery example](https://www.slodlc.com/examples/discovery-example) to understand the expected format and level of detail
3. **Complete the Worksheet**: Fill out all relevant sections for your service
4. **Save as Markdown**: Ensure the file is saved with `.md` extension
5. **Validate Locally** (optional): Test your worksheet with the validation script:
   ```bash
   python scripts/slo-advisor/validate-discovery-worksheet.py your-worksheet.md
   ```

### Tips for Completing the Discovery Worksheet

- **Be Specific**: Include concrete examples and metrics where possible
- **Include Context**: Explain business impact and user expectations
- **Document Dependencies**: List all critical dependencies
- **Include Existing SLIs**: If you already have SLIs defined, include them
- **Describe Outages**: Document past incidents and their business impact
- **Be Honest**: Include pain points and areas for improvement

### Validation

Before uploading your Discovery worksheet, ensure it:
- ✅ Has `.md` file extension
- ✅ Is under 5MB in size
- ✅ Contains text-based content (not binary)
- ✅ Includes key sections (Service, User Journeys, Dependencies, System Behavior)
- ✅ Uses proper Markdown formatting

