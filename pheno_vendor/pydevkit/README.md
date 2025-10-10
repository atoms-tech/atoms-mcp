# PyDevKit

**Comprehensive Python utilities library with zero external dependencies**

PyDevKit is a production-ready collection of 40+ utility modules extracted from real-world applications, providing essential infrastructure for building robust Python applications without external dependencies.

## Features

### 🌐 HTTP Utilities
- **HTTPClient**: Zero-dependency HTTP client with connection pooling
- **Retry Logic**: Exponential backoff with jitter
- **Header Management**: Smart header handling with user-agent generation
- **Authentication**: Bearer, Basic, and API key auth helpers

### ⚙️ Configuration Management
- **ConfigManager**: Hierarchical config with multiple sources
- **EnvLoader**: Type-safe environment variable loading
- **Validation**: Schema-based config validation
- **Encryption**: Config value encryption (optional cryptography support)

### 🔐 Security
- **Password Hashing**: PBKDF2-based secure password hashing
- **JWT**: Zero-dependency JWT creation and verification
- **Encryption**: Simple encryption utilities
- **PII Scanner**: Detect and redact personally identifiable information
- **HMAC Signing**: Message authentication codes

### 📊 Data Structures
- **LRUCache**: O(1) least-recently-used cache
- **PriorityQueue**: Heap-based priority queue
- **BloomFilter**: Probabilistic membership testing
- **CircularBuffer**: Fixed-size ring buffer
- **Trie**: Prefix tree for efficient string operations

### 🔤 String Utilities
- **Slugify**: URL-friendly slug generation
- **Sanitization**: HTML sanitization and tag stripping
- **Templating**: Simple string interpolation
- **Text Formatting**: Truncate, wrap, pad strings
- **Case Conversion**: camelCase, snake_case, kebab-case

### 📅 Date/Time Utilities
- **Parsing**: Parse dates, times, and durations from strings
- **Formatting**: Format as ISO, relative time, humanized durations
- **Timezones**: UTC conversion and timezone handling

### 📁 File System Utilities
- **Path Handling**: Safe path joining with traversal protection
- **Temp Files**: Context managers for temporary files/directories
- **File Locks**: Cross-process file locking

### ⚡ Async Utilities
- **EventBus**: Async event-driven architecture
- **TaskQueue**: Concurrent task processing with worker pools
- **Semaphores**: Rate limiting and concurrency control

### ✅ Validation
- **Common Validators**: Email, URL, phone, IP validation
- **Custom Validators**: Build validation rules
- **Schema Validation**: Complex data validation

### 🎯 Functional Programming
- **Composition**: compose() and pipe() functions
- **Currying**: Automatic function currying
- **Memoization**: Function result caching
- **Partial Application**: Partial function application

### ⏱️ Rate Limiting
- **Token Bucket**: Simple rate limiter
- **Sliding Window**: Advanced rate limiting
- **Per-user/endpoint**: Granular rate control

### 🔍 Tracing & Observability
- **Correlation IDs**: Distributed request tracing
- **Structured Logging**: Rich, queryable logs
- **Metrics**: Performance monitoring

## Installation

```bash
pip install pydevkit
```

### Optional Dependencies

```bash
# For cryptography features
pip install pydevkit[crypto]

# For YAML support
pip install pydevkit[yaml]

# Development tools
pip install pydevkit[dev]
```

## Quick Start

### HTTP Client

```python
from pydevkit import HTTPClient, exponential_backoff

# Simple HTTP client
client = HTTPClient(base_url="https://api.example.com")
response = client.get("/users/1")
user = response.json()

# With retry logic
@exponential_backoff(max_attempts=3)
def fetch_data():
    return client.get("/data").json()
```

### Configuration

```python
from pydevkit import ConfigManager, EnvLoader

# Hierarchical configuration
config = ConfigManager()
config.load_from_file("config.json")
config.load_from_env(prefix="APP_")

db_url = config.get("database.url")

# Type-safe environment variables
env = EnvLoader(prefix="APP_")
port = env.get_int("PORT", default=8000)
debug = env.get_bool("DEBUG", default=False)
```

### Security

```python
from pydevkit import hash_password, verify_password, create_jwt, PIIScanner

# Password hashing
hashed = hash_password("my_password")
is_valid = verify_password("my_password", hashed)

# JWT tokens
token = create_jwt(
    payload={"user_id": 123},
    secret="my-secret",
    expires_in=3600
)

# PII detection
scanner = PIIScanner()
text = "Contact john@example.com or 555-123-4567"
redacted = scanner.redact(text)  # "Contact [EMAIL] or [PHONE]"
```

### Data Structures

```python
from pydevkit import LRUCache, PriorityQueue, BloomFilter

# LRU Cache
cache = LRUCache(capacity=100)
cache.set("key", "value")
value = cache.get("key")

# Priority Queue
pq = PriorityQueue()
pq.push("urgent", priority=1)
pq.push("normal", priority=5)
item = pq.pop()  # Returns "urgent"

# Bloom Filter
bf = BloomFilter(size=1000)
bf.add("item")
"item" in bf  # True
```

### String Utilities

```python
from pydevkit import slugify, sanitize_html, Template

# Slugification
slug = slugify("Hello World!")  # "hello-world"

# HTML sanitization
safe = sanitize_html("<script>alert('xss')</script>")

# Templating
template = Template("Hello, {name}!")
result = template.render(name="World")  # "Hello, World!"
```

### Validation

```python
from pydevkit import is_email, is_url, Validator

# Quick validation
if is_email("test@example.com"):
    print("Valid email")

# Custom validators
validator = Validator()
validator.add_rule(lambda x: len(x) >= 8, "Must be at least 8 characters")
validator.add_rule(lambda x: any(c.isdigit() for c in x), "Must contain digit")

is_valid, errors = validator.validate("mypassword123")
```

### Functional Programming

```python
from pydevkit import compose, pipe, curry, memoize

# Function composition
add_one = lambda x: x + 1
multiply_two = lambda x: x * 2
f = pipe(add_one, multiply_two)  # Left to right
result = f(5)  # 12

# Memoization
@memoize
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

## Module Overview

| Module | Purpose | Key Features |
|--------|---------|-------------|
| `http` | HTTP operations | Client, retries, auth, headers |
| `config` | Configuration | Env vars, YAML/JSON, validation |
| `security` | Security utilities | Hashing, JWT, encryption, PII |
| `data_structures` | Data structures | Cache, queue, bloom filter, trie |
| `strings` | String utilities | Slugify, sanitize, templating |
| `datetime` | Date/time ops | Parsing, formatting, timezones |
| `fs` | File system | Paths, temp files, locks |
| `async_utils` | Async tools | Event bus, task queue, semaphores |
| `validation` | Validators | Email, URL, phone, custom |
| `functional` | Functional programming | Compose, curry, memoize |
| `rate_limiting` | Rate limiting | Token bucket, sliding window |
| `errors` | Error handling | Structured errors, normalization |
| `tracing` | Distributed tracing | Correlation IDs |
| `monitoring` | Performance monitoring | Metrics, command runner |

## Examples

Complete examples are in the [`examples/`](examples/) directory:

- **HTTP**: [http_example.py](examples/http_example.py)
- **Configuration**: [config_example.py](examples/config_example.py)
- **Security**: [security_example.py](examples/security_example.py)
- **Data Structures**: [data_structures_example.py](examples/data_structures_example.py)
- **Strings**: [strings_example.py](examples/strings_example.py)
- **Functional**: [functional_example.py](examples/functional_example.py)

## Architecture Principles

PyDevKit follows these design principles:

1. **Zero Dependencies**: Core functionality has no external dependencies
2. **Type Hints**: Complete type annotations for IDE support
3. **Async First**: Full async/await support where applicable
4. **Testable**: Easy to mock and test
5. **Production Ready**: Battle-tested in production environments
6. **Pythonic**: Follows Python best practices and PEP standards

## Requirements

- Python 3.8+
- Optional: `cryptography` for advanced encryption
- Optional: `pyyaml` for YAML config support

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/pydevkit.git
cd pydevkit

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy pydevkit

# Linting
ruff check .
black .
```

## Performance

PyDevKit is optimized for production use:

- **LRUCache**: O(1) get/set operations
- **PriorityQueue**: O(log n) push/pop
- **BloomFilter**: O(k) membership testing (k = num_hashes)
- **HTTP Client**: Connection reuse and pooling
- **Memoization**: Automatic function result caching

## Use Cases

PyDevKit is perfect for:

- **Microservices**: Common utilities without dependency bloat
- **Data Processing**: Efficient data structures and algorithms
- **Web APIs**: HTTP clients, rate limiting, authentication
- **CLI Tools**: Configuration, validation, file operations
- **Async Applications**: Event buses, task queues, concurrency control

## Comparison with Alternatives

| Feature | PyDevKit | requests + others | Standard Library |
|---------|----------|-------------------|------------------|
| Dependencies | 0 (core) | Many | 0 |
| HTTP Client | ✅ | ✅ (better) | ✅ (basic) |
| Data Structures | ✅ | ❌ | Limited |
| Config Management | ✅ | ❌ | ❌ |
| Security Utils | ✅ | ❌ | Partial |
| Validation | ✅ | ❌ | ❌ |
| Functional | ✅ | ❌ | Partial |

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

PyDevKit was extracted from production systems including:
- [Zen MCP Server](https://github.com/kooshapari/zen-mcp-server)
- Various production applications

## Related Projects

- **KInfra**: Infrastructure management utilities
- **mcp-qa**: MCP server testing framework
- **tui-kit**: Terminal UI components
- **stream-kit**: Real-time streaming protocols

## Changelog

### v0.1.0 (2024-10-07)

Initial release with 40+ utility modules:
- HTTP utilities (client, retries, headers, auth)
- Configuration management (env, YAML/JSON, validation)
- Security utilities (hashing, encryption, JWT, PII)
- Data structures (LRU cache, priority queue, bloom filter, trie)
- String utilities (slugify, sanitize, templating)
- Date/time utilities (parsing, formatting, timezones)
- File utilities (path handling, temp files, locks)
- Async utilities (event bus, task queue, semaphores)
- Validation (email, URL, phone, custom validators)
- Functional programming (compose, pipe, curry, memoize)

## Support

- **Documentation**: [Full docs](https://pydevkit.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/yourusername/pydevkit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/pydevkit/discussions)
