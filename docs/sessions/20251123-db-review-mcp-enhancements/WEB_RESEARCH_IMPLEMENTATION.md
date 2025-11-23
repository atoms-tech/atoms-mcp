# Web Research Implementation Guide - Extend Wider & Deeper

## Phase 1: Quick Wins (2-3 days)

### 1.1: Add MCP Resources for Templates

```python
# tools/resources.py - ADD

@mcp.resource("templates/entity/{entity_type}")
async def get_entity_template(entity_type: str) -> str:
    """Get template for entity creation."""
    templates = {
        "requirement": {
            "name": "Requirement name",
            "description": "Detailed description",
            "status": "draft",
            "priority": "high",
            "type": "functional"
        },
        "test": {
            "name": "Test name",
            "description": "Test description",
            "status": "draft",
            "type": "unit"
        }
    }
    return json.dumps(templates.get(entity_type, {}), indent=2)

@mcp.resource("templates/workflow/{workflow_name}")
async def get_workflow_template(workflow_name: str) -> str:
    """Get template for workflow execution."""
    workflows = {
        "setup_project": {
            "name": "Project name",
            "description": "Project description",
            "organization_id": "org-id"
        }
    }
    return json.dumps(workflows.get(workflow_name, {}), indent=2)
```

### 1.2: Add MCP Prompts for Workflows

```python
# tools/prompts.py - ADD

@mcp.prompt("workflow/setup_project")
async def prompt_setup_project() -> str:
    """Prompt for setting up a new project."""
    return """
    You are helping set up a new project. Gather:
    1. Project name
    2. Project description
    3. Organization ID
    4. Initial document structure
    
    Then call entity_tool with operation='create' for the project.
    """

@mcp.prompt("search/semantic")
async def prompt_semantic_search() -> str:
    """Prompt for semantic search."""
    return """
    You are performing semantic search. Provide:
    1. Search query (natural language)
    2. Entity types to search
    3. Limit (default 10)
    
    Then call data_query with query_type='semantic_search'.
    """
```

### 1.3: Implement BM25 Ranking

```python
# services/search/bm25_ranking.py - NEW

from rank_bm25 import BM25Okapi

class BM25Ranker:
    """BM25 ranking for PostgreSQL full-text search."""
    
    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
    
    async def rank_results(self, query, results):
        """Rank search results using BM25."""
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Create BM25 ranker
        corpus = [r.get("text", "").split() for r in results]
        bm25 = BM25Okapi(corpus)
        
        # Score results
        scores = bm25.get_scores(query_tokens)
        
        # Sort by score
        ranked = sorted(
            zip(results, scores),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [r for r, _ in ranked]
```

---

## Phase 2: Medium Effort (3-5 days)

### 2.1: Upstash Vector Integration

```python
# infrastructure/upstash_vector.py - NEW

from upstash_vector import Index

class UpstashVectorAdapter:
    """Adapter for Upstash Vector database."""
    
    def __init__(self, url: str, token: str):
        self.index = Index(url=url, token=token)
    
    async def upsert_embedding(self, id: str, vector: List[float], metadata: dict):
        """Upsert embedding with metadata."""
        await self.index.upsert(
            vectors=[(id, vector, metadata)]
        )
    
    async def query(self, vector: List[float], top_k: int = 10, filter: dict = None):
        """Query with optional metadata filtering."""
        results = await self.index.query(
            vector=vector,
            top_k=top_k,
            filter=filter
        )
        return results
    
    async def hybrid_search(self, query: str, vector: List[float], top_k: int = 10):
        """Hybrid search combining semantic and keyword."""
        # Semantic search
        semantic_results = await self.query(vector, top_k)
        
        # Keyword search (via PostgreSQL)
        keyword_results = await self._keyword_search(query, top_k)
        
        # Combine and rank
        return self._combine_results(semantic_results, keyword_results)
```

### 2.2: Immutable Audit Trails

```python
# infrastructure/audit_trail.py - NEW

import hashlib
from datetime import datetime

class ImmutableAuditTrail:
    """Immutable audit trail with blockchain-style hashing."""
    
    async def log_event(self, event_type: str, entity_type: str, 
                       entity_id: str, changes: dict, user_id: str):
        """Log event with hash chain."""
        # Get previous hash
        prev_hash = await self._get_previous_hash()
        
        # Create event record
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "changes": changes,
            "user_id": user_id,
            "previous_hash": prev_hash
        }
        
        # Calculate hash
        event_hash = hashlib.sha256(
            json.dumps(event, sort_keys=True).encode()
        ).hexdigest()
        
        # Store in database
        await self.db.insert("audit_trail", {
            **event,
            "hash": event_hash
        })
        
        return event_hash
```

### 2.3: Entity Linking

```python
# services/entity_linking.py - NEW

class EntityLinker:
    """Entity linking and disambiguation."""
    
    async def link_entities(self, entity_ref: str, entity_type: str):
        """Link ambiguous entity reference to actual entity."""
        # Get candidates
        candidates = await self._find_candidates(entity_ref, entity_type)
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Use embeddings for disambiguation
        ref_embedding = await self.embeddings.generate(entity_ref)
        
        # Score candidates
        scores = []
        for candidate in candidates:
            candidate_embedding = await self.embeddings.generate(
                candidate.get("name", "")
            )
            similarity = self._cosine_similarity(ref_embedding, candidate_embedding)
            scores.append((candidate, similarity))
        
        # Return best match
        return max(scores, key=lambda x: x[1])[0]
```

---

## Phase 3: Advanced (5-7 days)

### 3.1: Knowledge Graph Construction

```python
# services/knowledge_graph.py - NEW

class KnowledgeGraphBuilder:
    """Build knowledge graph from entities and relationships."""
    
    async def build_graph(self, workspace_id: str):
        """Build knowledge graph for workspace."""
        # Get all entities
        entities = await self.db.query("entities", 
                                      filters={"workspace_id": workspace_id})
        
        # Get all relationships
        relationships = await self.db.query("relationships",
                                           filters={"workspace_id": workspace_id})
        
        # Build graph
        graph = {
            "nodes": [
                {
                    "id": e["id"],
                    "type": e["entity_type"],
                    "label": e["name"],
                    "properties": e
                }
                for e in entities
            ],
            "edges": [
                {
                    "source": r["source_id"],
                    "target": r["target_id"],
                    "type": r["relationship_type"],
                    "properties": r
                }
                for r in relationships
            ]
        }
        
        return graph
```

### 3.2: Multi-Agent Orchestration

```python
# tools/multi_agent.py - NEW

class MultiAgentOrchestrator:
    """Orchestrate multiple specialized agents."""
    
    async def execute_workflow(self, workflow: str, parameters: dict):
        """Execute workflow with multiple agents."""
        agents = {
            "compliance": ComplianceAgent(),
            "analysis": AnalysisAgent(),
            "search": SearchAgent()
        }
        
        # Route to appropriate agent
        agent = agents.get(workflow.split("_")[0])
        if not agent:
            raise ValueError(f"Unknown workflow: {workflow}")
        
        # Execute
        return await agent.execute(workflow, parameters)
```

### 3.3: Upstash Workflow Integration

```python
# infrastructure/upstash_workflow.py - NEW

from upstash_workflow import Client

class UpstashWorkflowAdapter:
    """Adapter for Upstash Workflow."""
    
    def __init__(self, token: str):
        self.client = Client(token=token)
    
    async def create_workflow(self, name: str, steps: List[dict]):
        """Create long-running workflow."""
        workflow = await self.client.create_workflow(
            name=name,
            steps=steps
        )
        return workflow
    
    async def schedule_task(self, task: str, schedule: str, parameters: dict):
        """Schedule recurring task."""
        scheduled = await self.client.schedule(
            task=task,
            schedule=schedule,
            parameters=parameters
        )
        return scheduled
```

---

## 📊 IMPLEMENTATION CHECKLIST

### Phase 1 (2-3 days)
- [ ] Add MCP Resources for templates
- [ ] Add MCP Prompts for workflows
- [ ] Implement BM25 ranking
- [ ] Update data_query to use BM25
- [ ] Test all new features

### Phase 2 (3-5 days)
- [ ] Upstash Vector integration
- [ ] Immutable audit trails
- [ ] Entity linking
- [ ] Update search operations
- [ ] Test all new features

### Phase 3 (5-7 days)
- [ ] Knowledge graph construction
- [ ] Multi-agent orchestration
- [ ] Upstash Workflow integration
- [ ] Update workflow_execute
- [ ] Test all new features

---

## 🎯 EXPECTED OUTCOMES

✅ **MCP Resources & Prompts** - Better agent guidance  
✅ **BM25 Ranking** - Better search results  
✅ **Upstash Vector** - Faster semantic search  
✅ **Immutable Audit Trails** - Compliance ready  
✅ **Entity Linking** - Better disambiguation  
✅ **Knowledge Graphs** - Semantic relationships  
✅ **Multi-Agent** - Specialized workflows  
✅ **Upstash Workflow** - Long-running tasks  

---

## 📊 TOTAL EFFORT

- **Phase 1**: 2-3 days (quick wins)
- **Phase 2**: 3-5 days (medium effort)
- **Phase 3**: 5-7 days (advanced)

**TOTAL: 10-15 days (80-120 hours)**

**Combined with main plan: 37.5-42.5 days (300-340 hours)**

