# Performance & Code Quality Tools

## Overview

Comprehensive performance testing, benchmarking, and code quality analysis tools for Atoms MCP.

---

## Performance Testing

### 1. Benchmarking (pytest-benchmark)

**Purpose**: Measure and track performance of critical code paths

**Usage**:
```bash
# Run benchmarks
make benchmark

# Compare with previous runs
make benchmark-compare

# Or directly
pytest tests/performance/ --benchmark-only
```

**Example Test**:
```python
def test_server_startup_time(benchmark):
    """Benchmark server startup time."""
    def startup():
        from server import app
        return app
    
    result = benchmark(startup)
    assert result is not None
```

**Features**:
- Automatic statistical analysis
- Comparison with previous runs
- JSON output for CI/CD
- Regression detection

### 2. Memory Profiling (memory_profiler)

**Purpose**: Track memory usage and detect memory leaks

**Usage**:
```bash
# Profile memory usage
make profile-memory

# Or directly
python -m memory_profiler scripts/profile_memory.py
```

**Example**:
```python
from memory_profiler import profile

@profile
def load_server():
    from server import app
    return app
```

**Output**:
```
Line #    Mem usage    Increment  Occurrences   Line Contents
=============================================================
     5     50.0 MiB     50.0 MiB           1   @profile
     6                                         def load_server():
     7     55.2 MiB      5.2 MiB           1       from server import app
     8     55.2 MiB      0.0 MiB           1       return app
```

### 3. Load Testing (Locust)

**Purpose**: Test system performance under load

**Usage**:
```bash
# Run load test (headless)
make load-test

# Run with UI
make load-test-ui
# Then open http://localhost:8089

# Or directly
locust -f tests/load/locustfile.py --host=http://localhost:50003
```

**Example**:
```python
from locust import HttpUser, task, between

class AtomsUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(10)
    def health_check(self):
        self.client.get("/health")
    
    @task(5)
    def list_tools(self):
        self.client.post("/mcp/v1/tools/list", json={})
```

**Metrics**:
- Requests per second (RPS)
- Response times (min, max, avg, percentiles)
- Failure rate
- Concurrent users

---

## Code Quality Analysis

### 1. Complexity Analysis (Radon)

**Purpose**: Measure code complexity and maintainability

**Usage**:
```bash
# Analyze complexity
make complexity

# Check thresholds
make complexity-check
```

**Metrics**:
- **Cyclomatic Complexity** - Number of independent paths
- **Maintainability Index** - 0-100 score (higher is better)

**Grades**:
- A: 0-5 (simple)
- B: 6-10 (moderate)
- C: 11-20 (complex)
- D: 21-30 (very complex)
- F: 31+ (extremely complex)

**Thresholds**:
- Max absolute: B (10)
- Max modules: A (5)
- Max average: A (5)

### 2. Dead Code Detection (Vulture)

**Purpose**: Find unused code

**Usage**:
```bash
# Detect dead code
make dead-code

# Or directly
vulture . --min-confidence 80
```

**Finds**:
- Unused functions
- Unused classes
- Unused variables
- Unused imports
- Unreachable code

### 3. Code Duplication (Pylint)

**Purpose**: Detect duplicate code blocks

**Usage**:
```bash
# Check for duplicates
make duplication

# Or directly
pylint --disable=all --enable=duplicate-code .
```

**Benefits**:
- Identify refactoring opportunities
- Reduce maintenance burden
- Improve code reusability

### 4. Documentation Coverage (Interrogate)

**Purpose**: Measure docstring coverage

**Usage**:
```bash
# Check doc coverage
make doc-coverage

# Or directly
interrogate -v --fail-under 80 .
```

**Checks**:
- Module docstrings
- Class docstrings
- Function docstrings
- Method docstrings

**Target**: >80% coverage

### 5. Comprehensive Quality Report (Prospector)

**Purpose**: Run multiple quality tools at once

**Usage**:
```bash
# Generate quality report
make quality-report

# Or directly
prospector --profile prospector.yaml
```

**Includes**:
- Pylint
- Pyflakes
- McCabe (complexity)
- PEP8 (style)
- Bandit (security)
- MyPy (types)

---

## Dependency Analysis

### 1. Dependency Tree (pipdeptree)

**Purpose**: Visualize dependency relationships

**Usage**:
```bash
# Show tree
make deps-tree

# Or directly
pipdeptree
```

**Output**:
```
atoms-mcp==0.1.0
├── fastapi [required: >=0.104.0, installed: 0.104.1]
│   ├── pydantic [required: >=2.0.0, installed: 2.5.0]
│   └── starlette [required: >=0.27.0, installed: 0.27.0]
└── uvicorn [required: >=0.24.0, installed: 0.24.0]
```

### 2. Dependency Graph (pydeps)

**Purpose**: Generate visual dependency graph

**Usage**:
```bash
# Generate graph
make deps-graph

# Or directly
pydeps . --max-bacon=2 --cluster -o dependency_graph.svg
```

**Output**: SVG graph showing module dependencies

### 3. Security Audit (pip-audit)

**Purpose**: Check for known vulnerabilities

**Usage**:
```bash
# Audit dependencies
make deps-audit

# Or directly
pip-audit
```

**Checks**:
- Known CVEs
- Security advisories
- Outdated packages with fixes

### 4. License Compliance (pip-licenses)

**Purpose**: List dependency licenses

**Usage**:
```bash
# Show licenses
make deps-licenses

# Or directly
pip-licenses --format=markdown
```

**Output**:
```
| Name    | Version | License |
|---------|---------|---------|
| fastapi | 0.104.1 | MIT     |
| pydantic| 2.5.0   | MIT     |
```

---

## CI/CD Integration

### Performance Workflow

**File**: `.github/workflows/performance.yml`

**Jobs**:
1. **Benchmarks** - Run performance benchmarks
2. **Memory Profile** - Profile memory usage
3. **Load Test** - Run load tests
4. **Complexity** - Analyze code complexity
5. **Dependencies** - Analyze dependencies
6. **Quality Metrics** - Generate quality reports
7. **Doc Coverage** - Check documentation coverage

**Triggers**:
- Push to main/develop
- Pull requests
- Weekly schedule (Monday 00:00 UTC)
- Manual dispatch

### Code Quality Workflow

**File**: `.github/workflows/code-quality.yml`

**Jobs**:
1. **SonarCloud** - Comprehensive code analysis
2. **CodeQL** - Security analysis
3. **Dependency Review** - Check dependency changes
4. **License Check** - Verify license compliance
5. **Dead Code** - Detect unused code
6. **Duplication** - Find duplicate code
7. **Import Analysis** - Analyze import structure
8. **Type Coverage** - Check type annotation coverage
9. **Security Advanced** - Semgrep security scan

**Triggers**:
- Push to main/develop
- Pull requests
- Manual dispatch

---

## Configuration Files

### SonarCloud (`sonar-project.properties`)

```properties
sonar.projectKey=atoms-tech_atoms-mcp
sonar.organization=atoms-tech
sonar.sources=.
sonar.python.coverage.reportPaths=coverage.xml
```

### Prospector (`prospector.yaml`)

```yaml
strictness: medium
pylint:
  run: true
mccabe:
  max-complexity: 10
```

---

## Makefile Commands

### Performance
```bash
make benchmark           # Run performance benchmarks
make benchmark-compare   # Compare benchmark results
make profile-memory      # Profile memory usage
make load-test          # Run load tests (headless)
make load-test-ui       # Run load tests with UI
```

### Code Quality
```bash
make complexity         # Analyze code complexity
make complexity-check   # Check complexity thresholds
make dead-code         # Detect dead code
make duplication       # Check for code duplication
make doc-coverage      # Check documentation coverage
make quality-report    # Generate comprehensive quality report
```

### Dependencies
```bash
make deps-tree         # Show dependency tree
make deps-graph        # Generate dependency graph
make deps-audit        # Audit dependencies for vulnerabilities
make deps-licenses     # Show dependency licenses
```

---

## Best Practices

### Performance

1. **Benchmark Critical Paths**
   - Server startup
   - Request handling
   - Database queries
   - File operations

2. **Set Performance Budgets**
   - Response time < 100ms
   - Memory usage < 100MB
   - Startup time < 5s

3. **Monitor Trends**
   - Track benchmarks over time
   - Alert on regressions
   - Compare branches

### Code Quality

1. **Maintain Low Complexity**
   - Keep functions < 10 complexity
   - Refactor complex code
   - Use helper functions

2. **Remove Dead Code**
   - Run vulture regularly
   - Delete unused code
   - Don't comment out code

3. **Avoid Duplication**
   - Extract common code
   - Use inheritance/composition
   - Create utilities

4. **Document Code**
   - Maintain >80% doc coverage
   - Write clear docstrings
   - Update docs with code

### Dependencies

1. **Keep Dependencies Updated**
   - Run pip-audit weekly
   - Update vulnerable packages
   - Test after updates

2. **Minimize Dependencies**
   - Only add necessary packages
   - Review dependency tree
   - Consider alternatives

3. **Check Licenses**
   - Verify license compatibility
   - Document licenses
   - Avoid restrictive licenses

---

## Troubleshooting

### Benchmarks Failing

```bash
# Clear benchmark cache
rm -rf .benchmarks/

# Run with verbose output
pytest tests/performance/ --benchmark-only -v
```

### Memory Profiler Not Working

```bash
# Install with pip
pip install memory-profiler

# Run with python -m
python -m memory_profiler scripts/profile_memory.py
```

### Locust Connection Errors

```bash
# Start server first
./atoms start --no-tunnel &

# Wait for server to start
sleep 5

# Then run load test
make load-test
```

---

## Resources

- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [memory_profiler](https://pypi.org/project/memory-profiler/)
- [Locust](https://docs.locust.io/)
- [Radon](https://radon.readthedocs.io/)
- [Vulture](https://github.com/jendrikseipp/vulture)
- [Prospector](https://prospector.landscape.io/)
- [SonarCloud](https://sonarcloud.io/)
- [CodeQL](https://codeql.github.com/)

---

**Happy optimizing! 🚀**

