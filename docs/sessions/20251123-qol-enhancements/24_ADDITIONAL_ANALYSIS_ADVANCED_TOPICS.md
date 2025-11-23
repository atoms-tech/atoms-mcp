# Additional Analysis: Advanced Topics

## Topic 1: Multi-Tenant Context Isolation

### Problem
- Agents might accidentally access wrong workspace/organization
- Context leakage between sessions
- Cross-tenant data exposure risk

### Solution: Strict Context Validation

```python
class SessionContext:
    async def set_context(self, context_type: str, entity_id: str):
        """Set context with strict validation."""
        
        # 1. Validate entity exists in current workspace
        if context_type == "project":
            project = await self._get_project(entity_id)
            if project["workspace_id"] != self.workspace_id:
                raise ValueError("Project not in current workspace")
        
        # 2. Validate permissions
        if not await self._has_permission(context_type, entity_id):
            raise PermissionError("No permission to access this context")
        
        # 3. Set context
        self._context_vars[context_type].set(entity_id)
        await self._persist_to_session(context_type, entity_id)
```

### Benefits
- ✅ Prevents cross-tenant data access
- ✅ Validates permissions before setting context
- ✅ Audit trail of context changes
- ✅ Multi-tenant safe

---

## Topic 2: Context Versioning & Rollback

### Problem
- No way to revert context changes
- No history of context changes
- Difficult to debug context-related issues

### Solution: Context Versioning

```python
class SessionContext:
    _context_history = []
    
    async def set_context(self, context_type: str, entity_id: str):
        """Set context with versioning."""
        
        # 1. Save current state
        current_state = await self.get_context()
        self._context_history.append({
            "timestamp": datetime.now(),
            "action": "set",
            "context_type": context_type,
            "old_value": current_state.get(context_type),
            "new_value": entity_id
        })
        
        # 2. Set new context
        self._context_vars[context_type].set(entity_id)
        await self._persist_to_session(context_type, entity_id)
    
    async def rollback_context(self, steps: int = 1):
        """Rollback context to previous state."""
        
        if len(self._context_history) < steps:
            raise ValueError("Not enough history to rollback")
        
        # Get previous state
        previous_state = self._context_history[-steps]["old_value"]
        context_type = self._context_history[-steps]["context_type"]
        
        # Restore
        self._context_vars[context_type].set(previous_state)
        await self._persist_to_session(context_type, previous_state)
```

### Benefits
- ✅ Full context history
- ✅ Rollback capability
- ✅ Audit trail
- ✅ Debugging support

---

## Topic 3: Lazy Context Resolution

### Problem
- Context resolution adds latency
- Unnecessary context lookups
- Performance impact on high-volume operations

### Solution: Lazy Resolution with Caching

```python
class SessionContext:
    _context_cache = {}
    _cache_ttl = 300  # 5 minutes
    
    async def resolve_context(self, context_type: str) -> Optional[str]:
        """Lazy context resolution with caching."""
        
        cache_key = f"{self.session_id}:{context_type}"
        
        # 1. Check cache
        if cache_key in self._context_cache:
            cached_value, timestamp = self._context_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return cached_value
        
        # 2. Resolve from context vars
        try:
            value = self._context_vars[context_type].get()
            self._context_cache[cache_key] = (value, time.time())
            return value
        except LookupError:
            pass
        
        # 3. Load from session storage
        value = await self._load_from_session(context_type)
        if value:
            self._context_cache[cache_key] = (value, time.time())
        
        return value
    
    async def invalidate_cache(self, context_type: str = None):
        """Invalidate cache on context change."""
        
        if context_type:
            cache_key = f"{self.session_id}:{context_type}"
            if cache_key in self._context_cache:
                del self._context_cache[cache_key]
        else:
            # Clear all cache for this session
            self._context_cache.clear()
```

### Benefits
- ✅ Reduced latency
- ✅ Fewer database lookups
- ✅ Automatic cache invalidation
- ✅ TTL-based expiration

---

## Topic 4: Context Composition & Hierarchies

### Problem
- Flat context structure
- No way to express hierarchies
- Difficult to manage nested contexts

### Solution: Hierarchical Context

```python
class SessionContext:
    _context_hierarchy = {
        "workspace": None,
        "organization": None,
        "project": None,
        "document": None,
        "entity_type": None
    }
    
    async def set_context_hierarchy(self, hierarchy: dict):
        """Set entire context hierarchy at once."""
        
        # Validate hierarchy
        await self._validate_hierarchy(hierarchy)
        
        # Set all contexts
        for context_type, entity_id in hierarchy.items():
            if entity_id:
                self._context_vars[context_type].set(entity_id)
                await self._persist_to_session(context_type, entity_id)
    
    async def get_context_hierarchy(self) -> dict:
        """Get entire context hierarchy."""
        
        return {
            "workspace": await self.resolve_context("workspace"),
            "organization": await self.resolve_context("organization"),
            "project": await self.resolve_context("project"),
            "document": await self.resolve_context("document"),
            "entity_type": await self.resolve_context("entity_type")
        }
    
    async def _validate_hierarchy(self, hierarchy: dict):
        """Validate hierarchy is valid."""
        
        # workspace → organization → project → document
        # Each level must exist in parent
        
        if hierarchy.get("organization"):
            org = await self._get_organization(hierarchy["organization"])
            if org["workspace_id"] != hierarchy.get("workspace"):
                raise ValueError("Organization not in workspace")
        
        if hierarchy.get("project"):
            project = await self._get_project(hierarchy["project"])
            if project["organization_id"] != hierarchy.get("organization"):
                raise ValueError("Project not in organization")
        
        if hierarchy.get("document"):
            doc = await self._get_document(hierarchy["document"])
            if doc["project_id"] != hierarchy.get("project"):
                raise ValueError("Document not in project")
```

### Benefits
- ✅ Hierarchical context
- ✅ Validation of hierarchy
- ✅ Atomic hierarchy updates
- ✅ Clear parent-child relationships

---

## Topic 5: Context Predicates & Filtering

### Problem
- No way to filter operations based on context
- Difficult to enforce context-based policies
- No context-aware authorization

### Solution: Context Predicates

```python
class SessionContext:
    async def add_predicate(self, name: str, predicate_fn):
        """Add context predicate for filtering."""
        
        self._predicates[name] = predicate_fn
    
    async def evaluate_predicate(self, name: str, entity: dict) -> bool:
        """Evaluate predicate against entity."""
        
        if name not in self._predicates:
            raise ValueError(f"Unknown predicate: {name}")
        
        predicate_fn = self._predicates[name]
        return await predicate_fn(entity, self)

# Usage
async def setup_context_predicates(context: SessionContext):
    """Setup common context predicates."""
    
    # Only entities in current project
    async def in_current_project(entity, ctx):
        project_id = await ctx.resolve_context("project")
        return entity.get("project_id") == project_id
    
    # Only active entities
    async def is_active(entity, ctx):
        return entity.get("status") == "active"
    
    # Only high priority
    async def is_high_priority(entity, ctx):
        return entity.get("priority") in ["high", "critical"]
    
    # Composite: in project AND active AND high priority
    async def high_priority_active(entity, ctx):
        return (
            await in_current_project(entity, ctx) and
            await is_active(entity, ctx) and
            await is_high_priority(entity, ctx)
        )
    
    context.add_predicate("in_current_project", in_current_project)
    context.add_predicate("is_active", is_active)
    context.add_predicate("is_high_priority", is_high_priority)
    context.add_predicate("high_priority_active", high_priority_active)

# In entity_tool
async def list_entities(entity_type: str, predicate: str = None):
    """List entities with optional predicate filtering."""
    
    entities = await entity_adapter.list(entity_type)
    
    if predicate:
        entities = [
            e for e in entities
            if await context.evaluate_predicate(predicate, e)
        ]
    
    return entities
```

### Benefits
- ✅ Context-aware filtering
- ✅ Reusable predicates
- ✅ Composite predicates
- ✅ Authorization policies

---

## Topic 6: Context Observability & Metrics

### Problem
- No visibility into context usage
- Difficult to debug context issues
- No metrics on context performance

### Solution: Context Observability

```python
class SessionContext:
    _metrics = {
        "context_sets": 0,
        "context_gets": 0,
        "context_resolves": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "resolve_latency_ms": []
    }
    
    async def resolve_context(self, context_type: str) -> Optional[str]:
        """Resolve context with metrics."""
        
        start_time = time.time()
        
        # Check cache
        cache_key = f"{self.session_id}:{context_type}"
        if cache_key in self._context_cache:
            self._metrics["cache_hits"] += 1
            return self._context_cache[cache_key]
        
        self._metrics["cache_misses"] += 1
        
        # Resolve
        value = await self._resolve_from_storage(context_type)
        
        # Record metrics
        latency_ms = (time.time() - start_time) * 1000
        self._metrics["context_resolves"] += 1
        self._metrics["resolve_latency_ms"].append(latency_ms)
        
        return value
    
    def get_metrics(self) -> dict:
        """Get context metrics."""
        
        latencies = self._metrics["resolve_latency_ms"]
        
        return {
            "context_sets": self._metrics["context_sets"],
            "context_gets": self._metrics["context_gets"],
            "context_resolves": self._metrics["context_resolves"],
            "cache_hits": self._metrics["cache_hits"],
            "cache_misses": self._metrics["cache_misses"],
            "cache_hit_rate": (
                self._metrics["cache_hits"] /
                (self._metrics["cache_hits"] + self._metrics["cache_misses"])
                if (self._metrics["cache_hits"] + self._metrics["cache_misses"]) > 0
                else 0
            ),
            "avg_resolve_latency_ms": (
                sum(latencies) / len(latencies)
                if latencies else 0
            ),
            "max_resolve_latency_ms": max(latencies) if latencies else 0,
            "min_resolve_latency_ms": min(latencies) if latencies else 0
        }
```

### Benefits
- ✅ Full observability
- ✅ Performance metrics
- ✅ Cache hit rate tracking
- ✅ Latency monitoring

---

## Topic 7: Context Serialization & Persistence

### Problem
- Context lost on session restart
- No way to export/import context
- Difficult to migrate contexts

### Solution: Context Serialization

```python
class SessionContext:
    async def serialize_context(self) -> str:
        """Serialize context to JSON."""
        
        context_data = await self.get_context()
        
        return json.dumps({
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "context": context_data,
            "metrics": self.get_metrics()
        })
    
    async def deserialize_context(self, json_str: str):
        """Deserialize context from JSON."""
        
        data = json.loads(json_str)
        
        # Validate
        if data["session_id"] != self.session_id:
            raise ValueError("Session ID mismatch")
        
        # Restore context
        for context_type, entity_id in data["context"].items():
            if entity_id:
                await self.set_context(context_type, entity_id)
    
    async def export_context(self, filepath: str):
        """Export context to file."""
        
        serialized = await self.serialize_context()
        
        with open(filepath, "w") as f:
            f.write(serialized)
    
    async def import_context(self, filepath: str):
        """Import context from file."""
        
        with open(filepath, "r") as f:
            serialized = f.read()
        
        await self.deserialize_context(serialized)
```

### Benefits
- ✅ Context persistence
- ✅ Export/import capability
- ✅ Context migration
- ✅ Backup/restore

---

## Summary

These 7 advanced topics cover:
1. **Multi-tenant isolation** - Strict context validation
2. **Context versioning** - History and rollback
3. **Lazy resolution** - Performance optimization
4. **Hierarchical contexts** - Complex context structures
5. **Context predicates** - Authorization policies
6. **Observability** - Metrics and monitoring
7. **Serialization** - Persistence and migration

**Implementation Priority**:
- Phase 1: Topics 1, 2, 3 (critical)
- Phase 2: Topics 4, 5 (important)
- Phase 3: Topic 6, 7 (nice-to-have)

**Total Effort**: 10-15 days across all topics

