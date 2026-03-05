# Atoms MCP - Usage Examples & Tutorials

## Table of Contents
- [Getting Started Tutorial](#getting-started-tutorial)
- [Complete Project Setup](#complete-project-setup)
- [Requirements Management](#requirements-management)
- [Test Management](#test-management)
- [Search and Discovery](#search-and-discovery)
- [Advanced Workflows](#advanced-workflows)
- [Integration Examples](#integration-examples)
- [Troubleshooting Examples](#troubleshooting-examples)

## Getting Started Tutorial

### Step 1: Authentication Setup

```python
import requests
import json

# Configuration
BASE_URL = "https://mcp.atoms.tech"
CLIENT_ID = "your-workos-client-id"
REDIRECT_URI = "http://localhost:8000/auth/callback"

def authenticate():
    """Complete OAuth authentication flow."""
    # Step 1: Get authorization URL
    auth_response = requests.get(f"{BASE_URL}/auth/login", params={
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code"
    })
    
    auth_data = auth_response.json()
    auth_url = auth_data["auth_url"]
    
    print(f"Please visit: {auth_url}")
    print("After authentication, you'll be redirected with an authorization code.")
    
    # Step 2: Get authorization code from user
    auth_code = input("Enter the authorization code: ")
    
    # Step 3: Exchange code for token
    token_response = requests.post(f"{BASE_URL}/auth/token", {
        "code": auth_code,
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    })
    
    token_data = token_response.json()
    access_token = token_data["access_token"]
    
    print(f"Authentication successful! Token: {access_token[:20]}...")
    return access_token

# Authenticate and get token
token = authenticate()
headers = {"Authorization": f"Bearer {token}"}
```

### Step 2: Create Your First Organization

```python
def create_organization(name, description):
    """Create a new organization."""
    org_data = {
        "entity_type": "organization",
        "data": {
            "name": name,
            "description": description,
            "settings": {
                "theme": "light",
                "timezone": "UTC",
                "default_language": "en"
            }
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/entities", 
                           json=org_data, 
                           headers=headers)
    
    if response.status_code == 201:
        org = response.json()["data"]
        print(f"✅ Created organization: {org['name']} (ID: {org['id']})")
        return org
    else:
        print(f"❌ Failed to create organization: {response.text}")
        return None

# Create organization
org = create_organization(
    "My Tech Company",
    "A technology company focused on innovative solutions"
)
```

### Step 3: Create Your First Project

```python
def create_project(org_id, name, description):
    """Create a new project within an organization."""
    project_data = {
        "entity_type": "project",
        "data": {
            "organization_id": org_id,
            "name": name,
            "description": description,
            "status": "active",
            "settings": {
                "requirement_format": "EARS",
                "test_framework": "pytest",
                "version_control": "git"
            }
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/entities", 
                           json=project_data, 
                           headers=headers)
    
    if response.status_code == 201:
        project = response.json()["data"]
        print(f"✅ Created project: {project['name']} (ID: {project['id']})")
        return project
    else:
        print(f"❌ Failed to create project: {response.text}")
        return None

# Create project
project = create_project(
    org["id"],
    "E-commerce Platform",
    "A modern e-commerce platform with mobile app support"
)
```

## Complete Project Setup

### Setting Up a Software Development Project

```python
def setup_software_project(org_id, project_name):
    """Complete setup for a software development project."""
    
    # 1. Create main project
    project = create_project(org_id, project_name, 
                           "Software development project with requirements and tests")
    
    # 2. Create document structure
    documents = [
        {
            "title": "Functional Requirements",
            "content": "This document contains all functional requirements for the system.",
            "document_type": "requirement",
            "properties": {
                "category": "functional",
                "priority": "high",
                "version": "1.0"
            }
        },
        {
            "title": "Non-Functional Requirements",
            "content": "This document contains all non-functional requirements including performance, security, and usability.",
            "document_type": "requirement",
            "properties": {
                "category": "non-functional",
                "priority": "high",
                "version": "1.0"
            }
        },
        {
            "title": "Test Plan",
            "content": "Comprehensive test plan covering unit, integration, and system testing.",
            "document_type": "test",
            "properties": {
                "category": "test_plan",
                "priority": "medium",
                "version": "1.0"
            }
        }
    ]
    
    created_documents = []
    for doc_data in documents:
        doc_response = requests.post(f"{BASE_URL}/api/entities", 
                                   json={
                                       "entity_type": "document",
                                       "data": {
                                           "project_id": project["id"],
                                           **doc_data
                                       }
                                   }, 
                                   headers=headers)
        
        if doc_response.status_code == 201:
            doc = doc_response.json()["data"]
            created_documents.append(doc)
            print(f"✅ Created document: {doc['title']}")
    
    return project, created_documents

# Setup complete project
project, documents = setup_software_project(org["id"], "E-commerce Platform")
```

### Creating Requirements Hierarchy

```python
def create_requirements_hierarchy(project_id, documents):
    """Create a hierarchical structure of requirements."""
    
    # Find the functional requirements document
    func_doc = next((doc for doc in documents if doc["title"] == "Functional Requirements"), None)
    
    if not func_doc:
        print("❌ Functional requirements document not found")
        return []
    
    # High-level requirements
    high_level_requirements = [
        {
            "title": "User Management",
            "description": "System shall provide comprehensive user management capabilities",
            "format": "EARS",
            "statement": "The system SHALL provide user registration, authentication, and profile management",
            "rationale": "Users need to be able to create accounts and manage their information",
            "priority": "high",
            "status": "draft",
            "verification_method": "test"
        },
        {
            "title": "Product Catalog",
            "description": "System shall provide a comprehensive product catalog",
            "format": "EARS",
            "statement": "The system SHALL provide a searchable and filterable product catalog",
            "rationale": "Customers need to browse and find products",
            "priority": "high",
            "status": "draft",
            "verification_method": "test"
        },
        {
            "title": "Shopping Cart",
            "description": "System shall provide shopping cart functionality",
            "format": "EARS",
            "statement": "The system SHALL allow users to add, modify, and remove items from their shopping cart",
            "rationale": "Users need to manage their purchases before checkout",
            "priority": "high",
            "status": "draft",
            "verification_method": "test"
        }
    ]
    
    # Detailed requirements for User Management
    user_mgmt_requirements = [
        {
            "title": "User Registration",
            "description": "Users must be able to register for new accounts",
            "format": "EARS",
            "statement": "The system SHALL allow new users to register using email and password",
            "rationale": "New users need to create accounts to use the system",
            "priority": "high",
            "status": "draft",
            "verification_method": "test",
            "parent_requirement": "User Management"
        },
        {
            "title": "User Authentication",
            "description": "Users must be able to log in to their accounts",
            "format": "EARS",
            "statement": "The system SHALL authenticate users using email and password",
            "rationale": "Users need secure access to their accounts",
            "priority": "high",
            "status": "draft",
            "verification_method": "test",
            "parent_requirement": "User Management"
        },
        {
            "title": "Password Reset",
            "description": "Users must be able to reset forgotten passwords",
            "format": "EARS",
            "statement": "The system SHALL allow users to reset their password via email",
            "rationale": "Users may forget their passwords and need a way to regain access",
            "priority": "medium",
            "status": "draft",
            "verification_method": "test",
            "parent_requirement": "User Management"
        }
    ]
    
    # Create all requirements
    all_requirements = high_level_requirements + user_mgmt_requirements
    created_requirements = []
    
    for req_data in all_requirements:
        req_response = requests.post(f"{BASE_URL}/api/entities", 
                                   json={
                                       "entity_type": "requirement",
                                       "data": {
                                           "document_id": func_doc["id"],
                                           **req_data
                                       }
                                   }, 
                                   headers=headers)
        
        if req_response.status_code == 201:
            req = req_response.json()["data"]
            created_requirements.append(req)
            print(f"✅ Created requirement: {req['title']}")
    
    return created_requirements

# Create requirements hierarchy
requirements = create_requirements_hierarchy(project["id"], documents)
```

## Requirements Management

### EARS Format Requirements

```python
def create_ears_requirement(document_id, title, description, statement, rationale, verification):
    """Create a requirement in EARS format."""
    
    # Validate EARS statement
    if not any(word in statement.upper() for word in ["SHALL", "SHOULD", "MAY"]):
        raise ValueError("EARS statement must contain SHALL, SHOULD, or MAY")
    
    req_data = {
        "entity_type": "requirement",
        "data": {
            "document_id": document_id,
            "title": title,
            "description": description,
            "format": "EARS",
            "statement": statement,
            "rationale": rationale,
            "verification_method": verification,
            "priority": "high",
            "status": "draft"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/entities", 
                           json=req_data, 
                           headers=headers)
    
    if response.status_code == 201:
        return response.json()["data"]
    else:
        raise Exception(f"Failed to create requirement: {response.text}")

# Example EARS requirements
ears_requirements = [
    {
        "title": "Secure Payment Processing",
        "description": "The system must process payments securely",
        "statement": "The system SHALL process payments using encrypted communication and store no payment card data",
        "rationale": "Payment security is critical for customer trust and regulatory compliance",
        "verification": "security audit"
    },
    {
        "title": "Mobile Responsive Design",
        "description": "The system must work on mobile devices",
        "statement": "The system SHALL provide a responsive user interface that works on devices with screen widths from 320px to 1920px",
        "rationale": "Many users access e-commerce sites from mobile devices",
        "verification": "usability testing"
    }
]

for req in ears_requirements:
    try:
        created_req = create_ears_requirement(
            documents[0]["id"],  # Functional requirements document
            req["title"],
            req["description"],
            req["statement"],
            req["rationale"],
            req["verification"]
        )
        print(f"✅ Created EARS requirement: {created_req['title']}")
    except Exception as e:
        print(f"❌ Failed to create requirement: {e}")
```

### INCOSE Format Requirements

```python
def create_incose_requirement(document_id, req_id, text, rationale, verification):
    """Create a requirement in INCOSE format."""
    
    req_data = {
        "entity_type": "requirement",
        "data": {
            "document_id": document_id,
            "title": f"REQ-{req_id}",
            "description": text,
            "format": "INCOSE",
            "statement": text,
            "rationale": rationale,
            "verification_method": verification,
            "priority": "high",
            "status": "draft"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/entities", 
                           json=req_data, 
                           headers=headers)
    
    if response.status_code == 201:
        return response.json()["data"]
    else:
        raise Exception(f"Failed to create requirement: {response.text}")

# Example INCOSE requirements
incose_requirements = [
    {
        "id": "001",
        "text": "The system shall support up to 10,000 concurrent users",
        "rationale": "Expected peak usage during sales events",
        "verification": "load testing"
    },
    {
        "id": "002", 
        "text": "The system shall maintain 99.9% uptime",
        "rationale": "High availability is critical for e-commerce",
        "verification": "monitoring"
    }
]

for req in incose_requirements:
    try:
        created_req = create_incose_requirement(
            documents[0]["id"],  # Functional requirements document
            req["id"],
            req["text"],
            req["rationale"],
            req["verification"]
        )
        print(f"✅ Created INCOSE requirement: {created_req['title']}")
    except Exception as e:
        print(f"❌ Failed to create requirement: {e}")
```

## Test Management

### Creating Test Cases

```python
def create_test_case(document_id, title, description, test_type, steps, expected_result, requirements=None):
    """Create a test case."""
    
    test_data = {
        "entity_type": "test",
        "data": {
            "document_id": document_id,
            "title": title,
            "description": description,
            "test_type": test_type,
            "status": "draft",
            "steps": steps,
            "expected_result": expected_result,
            "requirements": requirements or []
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/entities", 
                           json=test_data, 
                           headers=headers)
    
    if response.status_code == 201:
        return response.json()["data"]
    else:
        raise Exception(f"Failed to create test case: {response.text}")

# Find the test plan document
test_doc = next((doc for doc in documents if doc["title"] == "Test Plan"), None)

if test_doc:
    # Functional test cases
    functional_tests = [
        {
            "title": "User Registration Test",
            "description": "Verify that new users can register successfully",
            "test_type": "functional",
            "steps": [
                "Navigate to registration page",
                "Enter valid email address",
                "Enter valid password (8+ characters)",
                "Confirm password",
                "Click 'Register' button"
            ],
            "expected_result": "User account is created and confirmation email is sent",
            "requirements": ["User Registration"]
        },
        {
            "title": "User Login Test",
            "description": "Verify that registered users can log in",
            "test_type": "functional", 
            "steps": [
                "Navigate to login page",
                "Enter valid email address",
                "Enter correct password",
                "Click 'Login' button"
            ],
            "expected_result": "User is logged in and redirected to dashboard",
            "requirements": ["User Authentication"]
        },
        {
            "title": "Password Reset Test",
            "description": "Verify that users can reset forgotten passwords",
            "test_type": "functional",
            "steps": [
                "Navigate to login page",
                "Click 'Forgot Password' link",
                "Enter registered email address",
                "Click 'Send Reset Email' button",
                "Check email for reset link",
                "Click reset link in email",
                "Enter new password",
                "Confirm new password",
                "Click 'Reset Password' button"
            ],
            "expected_result": "Password is reset and user can log in with new password",
            "requirements": ["Password Reset"]
        }
    ]
    
    # Performance test cases
    performance_tests = [
        {
            "title": "Concurrent User Load Test",
            "description": "Verify system performance under expected load",
            "test_type": "performance",
            "steps": [
                "Set up load testing tool (e.g., JMeter)",
                "Configure test for 10,000 concurrent users",
                "Run test for 30 minutes",
                "Monitor system performance metrics",
                "Verify response times remain under 2 seconds"
            ],
            "expected_result": "System maintains performance under expected load",
            "requirements": ["REQ-001"]
        }
    ]
    
    # Create all test cases
    all_tests = functional_tests + performance_tests
    
    for test in all_tests:
        try:
            created_test = create_test_case(
                test_doc["id"],
                test["title"],
                test["description"],
                test["test_type"],
                test["steps"],
                test["expected_result"],
                test["requirements"]
            )
            print(f"✅ Created test case: {created_test['title']}")
        except Exception as e:
            print(f"❌ Failed to create test case: {e}")
```

### Test Execution Tracking

```python
def update_test_status(test_id, status, results=None, notes=None):
    """Update test case status and results."""
    
    update_data = {
        "data": {
            "status": status,
            "results": results,
            "notes": notes,
            "executed_at": "2024-01-15T10:30:00Z"
        }
    }
    
    response = requests.put(f"{BASE_URL}/api/entities/{test_id}", 
                          json=update_data, 
                          headers=headers)
    
    if response.status_code == 200:
        return response.json()["data"]
    else:
        raise Exception(f"Failed to update test: {response.text}")

# Example test execution
def execute_test_suite():
    """Execute a test suite and track results."""
    
    # Get all test cases
    tests_response = requests.get(f"{BASE_URL}/api/entities", 
                                params={"entity_type": "test"}, 
                                headers=headers)
    
    if tests_response.status_code == 200:
        tests = tests_response.json()["data"]["items"]
        
        for test in tests:
            print(f"Executing test: {test['title']}")
            
            # Simulate test execution
            if "Registration" in test["title"]:
                # Simulate successful test
                update_test_status(test["id"], "passed", {
                    "execution_time": "2.5s",
                    "browser": "Chrome",
                    "environment": "staging"
                }, "Test passed successfully")
                print(f"✅ {test['title']} - PASSED")
                
            elif "Login" in test["title"]:
                # Simulate failed test
                update_test_status(test["id"], "failed", {
                    "execution_time": "1.2s",
                    "browser": "Chrome", 
                    "environment": "staging",
                    "error": "Login button not clickable"
                }, "Test failed due to UI issue")
                print(f"❌ {test['title']} - FAILED")
                
            else:
                # Simulate pending test
                update_test_status(test["id"], "pending")
                print(f"⏳ {test['title']} - PENDING")

# Execute test suite
execute_test_suite()
```

## Search and Discovery

### Semantic Search Examples

```python
def search_requirements(query, limit=10):
    """Search requirements using semantic search."""
    
    search_data = {
        "query": query,
        "entity_types": ["requirement"],
        "limit": limit,
        "threshold": 0.7
    }
    
    response = requests.post(f"{BASE_URL}/api/search/semantic", 
                           json=search_data, 
                           headers=headers)
    
    if response.status_code == 200:
        results = response.json()["data"]["results"]
        print(f"Found {len(results)} requirements for query: '{query}'")
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']} (Score: {result['score']:.2f})")
            print(f"   {result['content'][:100]}...")
            print()
        
        return results
    else:
        print(f"Search failed: {response.text}")
        return []

# Search examples
search_queries = [
    "user authentication security",
    "payment processing encryption",
    "mobile responsive design",
    "performance scalability",
    "password reset functionality"
]

for query in search_queries:
    print(f"🔍 Searching for: {query}")
    results = search_requirements(query, limit=5)
    print("-" * 50)
```

### Advanced Search with Filters

```python
def advanced_search(query, entity_types=None, filters=None, search_type="hybrid"):
    """Perform advanced search with multiple criteria."""
    
    search_data = {
        "query": query,
        "entity_types": entity_types or ["requirement", "test", "document"],
        "search_type": search_type,
        "limit": 20,
        "threshold": 0.6
    }
    
    if filters:
        search_data["filters"] = filters
    
    response = requests.post(f"{BASE_URL}/api/search/{search_type}", 
                           json=search_data, 
                           headers=headers)
    
    if response.status_code == 200:
        return response.json()["data"]
    else:
        print(f"Advanced search failed: {response.text}")
        return None

# Example advanced searches
advanced_searches = [
    {
        "query": "security authentication",
        "entity_types": ["requirement"],
        "filters": {"priority": "high", "status": "approved"},
        "search_type": "semantic"
    },
    {
        "query": "test case execution",
        "entity_types": ["test"],
        "filters": {"test_type": "functional", "status": "passed"},
        "search_type": "text"
    },
    {
        "query": "mobile responsive design",
        "entity_types": ["requirement", "test"],
        "filters": {"priority": "high"},
        "search_type": "hybrid"
    }
]

for search_config in advanced_searches:
    print(f"🔍 Advanced search: {search_config['query']}")
    results = advanced_search(**search_config)
    
    if results:
        print(f"Found {len(results['results'])} results")
        for result in results["results"][:3]:  # Show top 3
            print(f"  - {result['title']} ({result['entity_type']}) - Score: {result['score']:.2f}")
    print("-" * 50)
```

## Advanced Workflows

### Requirements Traceability Matrix

```python
def create_traceability_matrix(project_id):
    """Create a requirements traceability matrix."""
    
    # Get all requirements
    reqs_response = requests.get(f"{BASE_URL}/api/entities", 
                               params={"entity_type": "requirement"}, 
                               headers=headers)
    
    # Get all tests
    tests_response = requests.get(f"{BASE_URL}/api/entities", 
                                params={"entity_type": "test"}, 
                                headers=headers)
    
    if reqs_response.status_code == 200 and tests_response.status_code == 200:
        requirements = reqs_response.json()["data"]["items"]
        tests = tests_response.json()["data"]["items"]
        
        print("Requirements Traceability Matrix")
        print("=" * 80)
        print(f"{'Requirement ID':<20} {'Title':<30} {'Test Cases':<20} {'Coverage':<10}")
        print("-" * 80)
        
        for req in requirements:
            # Find tests that trace to this requirement
            traced_tests = []
            for test in tests:
                if req["title"] in test.get("requirements", []):
                    traced_tests.append(test["title"])
            
            coverage = "Complete" if traced_tests else "Missing"
            test_list = ", ".join(traced_tests[:2])  # Show first 2 tests
            if len(traced_tests) > 2:
                test_list += f" (+{len(traced_tests)-2} more)"
            
            print(f"{req['title']:<20} {req['title'][:29]:<30} {test_list:<20} {coverage:<10}")
        
        return requirements, tests
    else:
        print("Failed to retrieve requirements or tests")
        return [], []

# Create traceability matrix
requirements, tests = create_traceability_matrix(project["id"])
```

### Automated Test Generation

```python
def generate_tests_from_requirements(requirement_id):
    """Generate test cases automatically from requirements."""
    
    # Get the requirement
    req_response = requests.get(f"{BASE_URL}/api/entities/{requirement_id}", 
                              headers=headers)
    
    if req_response.status_code != 200:
        print(f"Failed to get requirement: {req_response.text}")
        return
    
    requirement = req_response.json()["data"]
    
    # Generate test cases based on requirement format
    if requirement.get("format") == "EARS":
        test_cases = generate_ears_tests(requirement)
    elif requirement.get("format") == "INCOSE":
        test_cases = generate_incose_tests(requirement)
    else:
        test_cases = generate_generic_tests(requirement)
    
    # Create test cases
    for test_case in test_cases:
        try:
            created_test = create_test_case(
                documents[1]["id"],  # Test plan document
                test_case["title"],
                test_case["description"],
                test_case["test_type"],
                test_case["steps"],
                test_case["expected_result"],
                [requirement["title"]]
            )
            print(f"✅ Generated test: {created_test['title']}")
        except Exception as e:
            print(f"❌ Failed to generate test: {e}")

def generate_ears_tests(requirement):
    """Generate test cases from EARS format requirement."""
    statement = requirement["statement"]
    title = requirement["title"]
    
    tests = []
    
    # Positive test case
    tests.append({
        "title": f"{title} - Positive Test",
        "description": f"Verify that {title.lower()} works as expected",
        "test_type": "functional",
        "steps": [
            f"Set up test environment for {title.lower()}",
            "Execute the required action",
            "Verify the expected behavior occurs"
        ],
        "expected_result": f"The system behaves according to: {statement}"
    })
    
    # Negative test case
    tests.append({
        "title": f"{title} - Negative Test", 
        "description": f"Verify that {title.lower()} handles invalid inputs gracefully",
        "test_type": "functional",
        "steps": [
            f"Set up test environment for {title.lower()}",
            "Provide invalid or edge case inputs",
            "Verify system handles errors appropriately"
        ],
        "expected_result": "System provides appropriate error messages and does not crash"
    })
    
    return tests

def generate_incose_tests(requirement):
    """Generate test cases from INCOSE format requirement."""
    # Similar implementation for INCOSE format
    pass

def generate_generic_tests(requirement):
    """Generate generic test cases."""
    # Similar implementation for generic format
    pass

# Generate tests for a specific requirement
if requirements:
    first_req = requirements[0]
    print(f"Generating tests for requirement: {first_req['title']}")
    generate_tests_from_requirements(first_req["id"])
```

## Integration Examples

### CI/CD Integration

```python
def ci_cd_integration():
    """Example CI/CD integration with Atoms MCP."""
    
    # 1. Get test results from CI system
    ci_test_results = {
        "build_id": "build-123",
        "commit_hash": "abc123def456",
        "test_results": [
            {"test_name": "User Registration Test", "status": "passed", "duration": "2.5s"},
            {"test_name": "User Login Test", "status": "failed", "duration": "1.2s", "error": "Login button not found"},
            {"test_name": "Password Reset Test", "status": "passed", "duration": "3.1s"}
        ]
    }
    
    # 2. Update test cases with CI results
    for result in ci_test_results["test_results"]:
        # Find the test case
        tests_response = requests.get(f"{BASE_URL}/api/entities", 
                                    params={"entity_type": "test"}, 
                                    headers=headers)
        
        if tests_response.status_code == 200:
            tests = tests_response.json()["data"]["items"]
            test_case = next((t for t in tests if t["title"] == result["test_name"]), None)
            
            if test_case:
                # Update test with CI results
                update_data = {
                    "data": {
                        "status": result["status"],
                        "ci_results": {
                            "build_id": ci_test_results["build_id"],
                            "commit_hash": ci_test_results["commit_hash"],
                            "execution_time": result["duration"],
                            "error": result.get("error")
                        },
                        "last_executed": "2024-01-15T10:30:00Z"
                    }
                }
                
                update_response = requests.put(f"{BASE_URL}/api/entities/{test_case['id']}", 
                                             json=update_data, 
                                             headers=headers)
                
                if update_response.status_code == 200:
                    print(f"✅ Updated {result['test_name']} with CI results")
                else:
                    print(f"❌ Failed to update {result['test_name']}: {update_response.text}")

# Run CI/CD integration
ci_cd_integration()
```

### Slack Integration

```python
def slack_integration():
    """Example Slack integration for notifications."""
    
    import json
    
    # 1. Monitor for failed tests
    tests_response = requests.get(f"{BASE_URL}/api/entities", 
                                params={"entity_type": "test", "filters": {"status": "failed"}}, 
                                headers=headers)
    
    if tests_response.status_code == 200:
        failed_tests = tests_response.json()["data"]["items"]
        
        if failed_tests:
            # Send Slack notification
            slack_message = {
                "text": f"🚨 {len(failed_tests)} test(s) failed in the latest run",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {
                                "title": test["title"],
                                "value": test.get("notes", "No additional details"),
                                "short": False
                            }
                            for test in failed_tests[:5]  # Limit to 5 tests
                        ]
                    }
                ]
            }
            
            # In a real implementation, you would send this to Slack
            print("Slack notification would be sent:")
            print(json.dumps(slack_message, indent=2))
    
    # 2. Monitor for new requirements
    reqs_response = requests.get(f"{BASE_URL}/api/entities", 
                               params={"entity_type": "requirement", "filters": {"status": "draft"}}, 
                               headers=headers)
    
    if reqs_response.status_code == 200:
        draft_requirements = reqs_response.json()["data"]["items"]
        
        if draft_requirements:
            slack_message = {
                "text": f"📝 {len(draft_requirements)} requirement(s) need review",
                "attachments": [
                    {
                        "color": "warning",
                        "fields": [
                            {
                                "title": req["title"],
                                "value": req["description"][:100] + "...",
                                "short": False
                            }
                            for req in draft_requirements[:3]  # Limit to 3 requirements
                        ]
                    }
                ]
            }
            
            print("Slack notification for requirements would be sent:")
            print(json.dumps(slack_message, indent=2))

# Run Slack integration
slack_integration()
```

## Troubleshooting Examples

### Common Issues and Solutions

```python
def troubleshoot_common_issues():
    """Examples of troubleshooting common issues."""
    
    # 1. Authentication issues
    def check_authentication():
        """Check if authentication is working."""
        response = requests.get(f"{BASE_URL}/auth/verify", headers=headers)
        
        if response.status_code == 200:
            print("✅ Authentication is working")
            user_info = response.json()["data"]
            print(f"   User: {user_info.get('email', 'Unknown')}")
            print(f"   Organization: {user_info.get('organization', 'Unknown')}")
        else:
            print("❌ Authentication failed")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
    
    # 2. API rate limiting
    def check_rate_limits():
        """Check current rate limit status."""
        response = requests.get(f"{BASE_URL}/api/entities", 
                              params={"entity_type": "organization", "limit": 1}, 
                              headers=headers)
        
        if response.status_code == 200:
            print("✅ API request successful")
            print(f"   Rate limit: {response.headers.get('X-RateLimit-Limit', 'Unknown')}")
            print(f"   Remaining: {response.headers.get('X-RateLimit-Remaining', 'Unknown')}")
            print(f"   Reset time: {response.headers.get('X-RateLimit-Reset', 'Unknown')}")
        elif response.status_code == 429:
            print("❌ Rate limit exceeded")
            retry_after = response.headers.get('X-RateLimit-Retry-After', '60')
            print(f"   Retry after: {retry_after} seconds")
        else:
            print(f"❌ API request failed: {response.status_code}")
    
    # 3. Data validation issues
    def validate_entity_data(entity_data):
        """Validate entity data before sending."""
        required_fields = {
            "organization": ["name"],
            "project": ["name", "organization_id"],
            "document": ["title", "project_id"],
            "requirement": ["title", "document_id"],
            "test": ["title", "document_id"]
        }
        
        entity_type = entity_data.get("entity_type")
        data = entity_data.get("data", {})
        
        if entity_type not in required_fields:
            print(f"❌ Unknown entity type: {entity_type}")
            return False
        
        missing_fields = []
        for field in required_fields[entity_type]:
            if field not in data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields for {entity_type}: {missing_fields}")
            return False
        
        print(f"✅ {entity_type} data validation passed")
        return True
    
    # 4. Search troubleshooting
    def troubleshoot_search(query):
        """Troubleshoot search issues."""
        print(f"🔍 Troubleshooting search for: '{query}'")
        
        # Try different search types
        search_types = ["semantic", "text", "hybrid"]
        
        for search_type in search_types:
            try:
                search_data = {
                    "query": query,
                    "entity_types": ["requirement", "test", "document"],
                    "search_type": search_type,
                    "limit": 5
                }
                
                response = requests.post(f"{BASE_URL}/api/search/{search_type}", 
                                       json=search_data, 
                                       headers=headers)
                
                if response.status_code == 200:
                    results = response.json()["data"]["results"]
                    print(f"   {search_type.capitalize()} search: {len(results)} results")
                else:
                    print(f"   {search_type.capitalize()} search failed: {response.status_code}")
                    
            except Exception as e:
                print(f"   {search_type.capitalize()} search error: {e}")
    
    # Run troubleshooting
    print("🔧 Running troubleshooting checks...")
    print()
    
    check_authentication()
    print()
    
    check_rate_limits()
    print()
    
    # Test data validation
    test_data = {
        "entity_type": "organization",
        "data": {
            "name": "Test Organization"
        }
    }
    validate_entity_data(test_data)
    print()
    
    # Test search troubleshooting
    troubleshoot_search("user authentication")

# Run troubleshooting
troubleshoot_common_issues()
```

### Performance Monitoring

```python
def monitor_performance():
    """Monitor API performance and provide recommendations."""
    
    import time
    
    # Test API response times
    endpoints = [
        ("GET /api/entities?entity_type=organization", "list_organizations"),
        ("POST /api/search/semantic", "semantic_search"),
        ("GET /api/entities?entity_type=requirement", "list_requirements")
    ]
    
    performance_results = []
    
    for endpoint, name in endpoints:
        print(f"Testing {name}...")
        
        start_time = time.time()
        
        if "GET" in endpoint:
            response = requests.get(f"{BASE_URL}{endpoint.split(' ')[1]}", headers=headers)
        elif "POST" in endpoint:
            search_data = {
                "query": "test query",
                "entity_types": ["requirement"],
                "limit": 10
            }
            response = requests.post(f"{BASE_URL}{endpoint.split(' ')[1]}", 
                                   json=search_data, 
                                   headers=headers)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        performance_results.append({
            "endpoint": name,
            "response_time": response_time,
            "status_code": response.status_code,
            "success": response.status_code == 200
        })
        
        print(f"   Response time: {response_time:.2f}s")
        print(f"   Status: {response.status_code}")
        print()
    
    # Analyze performance
    print("📊 Performance Analysis")
    print("=" * 40)
    
    for result in performance_results:
        status = "✅" if result["success"] else "❌"
        performance = "Fast" if result["response_time"] < 1.0 else "Slow" if result["response_time"] > 3.0 else "Normal"
        
        print(f"{status} {result['endpoint']:<20} {result['response_time']:.2f}s ({performance})")
    
    # Recommendations
    print("\n💡 Recommendations:")
    slow_endpoints = [r for r in performance_results if r["response_time"] > 2.0]
    
    if slow_endpoints:
        print("   - Consider caching for slow endpoints")
        print("   - Optimize database queries")
        print("   - Use pagination for large datasets")
    else:
        print("   - Performance looks good!")
    
    failed_endpoints = [r for r in performance_results if not r["success"]]
    if failed_endpoints:
        print("   - Fix failed endpoints before optimizing performance")

# Run performance monitoring
monitor_performance()
```

This comprehensive usage examples and tutorials guide provides practical, real-world examples of how to use the Atoms MCP API effectively. Each example includes complete code that can be run directly, along with explanations of what each part does and how to adapt it for your specific needs.