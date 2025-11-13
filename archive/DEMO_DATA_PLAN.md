# Demo Organization Setup Plan
**Organization:** Phenotype or Argis-Org
**Target:** ~200 entities of realistic demo data
**Purpose:** Interactive query and action demonstrations

---

## 📊 **DEMO DATA STRUCTURE (200 entities)**

### **Organization Level (1)**
- **Phenotype** (or create new Argis-Org)
  - Type: Healthcare/Genomics research organization
  - Status: Active

### **Projects (5) - 20 entities**
1. **Patient Genomics Platform**
   - Description: Core genomics analysis system
   - Status: Active
   - Team: 4 members

2. **Clinical Trial Management**
   - Description: Multi-site clinical trial coordination
   - Status: Active
   - Team: 3 members

3. **Biomarker Discovery**
   - Description: Novel biomarker identification pipeline
   - Status: Planning
   - Team: 2 members

4. **Data Integration Hub**
   - Description: Cross-platform data harmonization
   - Status: Active
   - Team: 3 members

5. **Regulatory Compliance System**
   - Description: HIPAA/GDPR compliance automation
   - Status: Active
   - Team: 2 members

### **Documents (15) - 15 entities**

**Patient Genomics Platform (4 docs):**
1. System Requirements Document
2. Architecture Design Document
3. API Documentation
4. User Guide

**Clinical Trial Management (3 docs):**
5. Trial Protocol Requirements
6. Data Collection Standards
7. Compliance Checklist

**Biomarker Discovery (3 docs):**
8. Research Requirements
9. Analysis Pipeline Specification
10. Validation Criteria

**Data Integration Hub (3 docs):**
11. Integration Requirements
12. Data Schema Documentation
13. ETL Process Guide

**Regulatory Compliance (2 docs):**
14. Compliance Requirements
15. Security Standards

### **Requirements (150) - 150 entities**

**Functional Requirements (90):**
- **Patient Genomics (30):**
  - Data ingestion (10 requirements)
  - Analysis pipeline (10 requirements)
  - Reporting system (10 requirements)

- **Clinical Trial (20):**
  - Patient enrollment (7 requirements)
  - Data collection (7 requirements)
  - Trial monitoring (6 requirements)

- **Biomarker Discovery (15):**
  - Sample processing (5 requirements)
  - Statistical analysis (5 requirements)
  - Validation workflow (5 requirements)

- **Data Integration (15):**
  - Data connectors (5 requirements)
  - Transformation rules (5 requirements)
  - Quality checks (5 requirements)

- **Regulatory Compliance (10):**
  - Access control (3 requirements)
  - Audit logging (3 requirements)
  - Data encryption (4 requirements)

**Non-Functional Requirements (60):**
- Performance (15)
- Security (15)
- Scalability (10)
- Reliability (10)
- Usability (10)

### **Test Cases (15) - 15 entities**
- Unit tests (5)
- Integration tests (5)
- System tests (3)
- UAT scenarios (2)

### **Properties/Metadata (15) - 15 entities**
- Configuration properties (10)
- Custom attributes (5)

**Total: ~216 entities**

---

## 🎯 **EXAMPLE QUERIES TO DEMONSTRATE**

### **Search Queries**

**1. FTS Search:**
```
Query: "genomics analysis"
Expected: Requirements and docs about genomics processing
```

**2. RAG Semantic Search:**
```
Query: "patient data privacy and security requirements"
Expected: Find HIPAA, encryption, access control requirements
```

**3. Multi-Entity Search:**
```
Query: "trial" across documents and requirements
Expected: Clinical trial related items
```

### **Analytics Queries**

**4. Aggregate Analysis:**
```
Query: Get counts across all entity types
Expected: Project count, requirement breakdown, etc.
```

**5. Filtered Search:**
```
Query: All high-priority requirements
Expected: Critical requirements list
```

**6. RAG Hybrid Search:**
```
Query: "biomarker statistical validation methods"
Expected: Mix of exact matches and semantic results
```

### **CRUD Demonstrations**

**7. Update Workflow:**
```
Action: Update requirement priority from low to critical
Demo: Audit trail tracking
```

**8. Soft Delete:**
```
Action: Delete a test requirement
Demo: Soft delete with is_deleted flag
```

**9. Relationship Navigation:**
```
Action: Find all team members on a project
Demo: Relationship listing with profiles
```

### **Complex Scenarios**

**10. Cross-Project Analysis:**
```
Query: Security requirements across all projects
Expected: Security items from all 5 projects
```

**11. Traceability:**
```
Action: Trace requirement to tests
Demo: Requirement → test coverage mapping
```

**12. Change Tracking:**
```
Query: Recently updated requirements
Demo: Audit trail and version history
```

---

## 📝 **REALISTIC DATA EXAMPLES**

### **Sample Requirements**

**High Priority - Security:**
```json
{
  "name": "Patient Data Encryption at Rest",
  "description": "All patient genomic data must be encrypted using AES-256 when stored in databases or file systems",
  "priority": "critical",
  "status": "approved",
  "format": "incose",
  "level": "system",
  "external_id": "SEC-001"
}
```

**Medium Priority - Functional:**
```json
{
  "name": "Variant Calling Pipeline Integration",
  "description": "System shall integrate GATK variant calling pipeline with configurable parameters for sensitivity vs specificity",
  "priority": "high",
  "status": "active",
  "format": "incose",
  "level": "component",
  "external_id": "GEN-015"
}
```

**Low Priority - Performance:**
```json
{
  "name": "API Response Time SLA",
  "description": "All read API endpoints must return results within 200ms for 95th percentile requests",
  "priority": "medium",
  "status": "active",
  "format": "incose",
  "level": "system",
  "external_id": "PERF-008"
}
```

---

## 🔄 **DEMO WORKFLOW SCRIPT**

### **Step 1: Setup**
1. Authenticate with MCP
2. Check for Phenotype org (or create Argis-Org)
3. Set workspace context

### **Step 2: Create Projects**
```javascript
for each project in [5 projects]:
  - Create project with workflow_tool
  - Add team members (relationships)
  - Create initial documents
```

### **Step 3: Populate Requirements**
```javascript
for each document:
  - Create 8-12 requirements
  - Vary priority (30% high, 50% medium, 20% low)
  - Vary status (70% active, 20% approved, 10% draft)
  - Add realistic descriptions
```

### **Step 4: Add Tests & Properties**
```javascript
- Create test cases linked to requirements
- Add custom properties for configuration
```

### **Step 5: Verification**
```javascript
- Run aggregate query (should show ~200 entities)
- Test search across all types
- Verify relationships
```

---

## 🎬 **DEMO SCENARIOS**

### **Scenario 1: Product Manager Workflow**
```
User Story: "As a PM, I want to find all high-priority security requirements across projects"

Actions:
1. Search: "security" with filter priority=high
2. Show results grouped by project
3. Demonstrate audit trail
```

### **Scenario 2: Developer Workflow**
```
User Story: "As a developer, I need to find API integration requirements"

Actions:
1. RAG semantic search: "API integration endpoints"
2. Find related test cases
3. Show traceability links
```

### **Scenario 3: Compliance Officer Workflow**
```
User Story: "As a compliance officer, I need all HIPAA-related requirements"

Actions:
1. Multi-entity search: "HIPAA" across docs + requirements
2. Filter by status (approved only)
3. Generate compliance report (aggregate)
```

### **Scenario 4: QA Engineer Workflow**
```
User Story: "As a QA engineer, I want to see test coverage for genomics features"

Actions:
1. Find all genomics requirements
2. Check which have linked tests
3. Identify gaps in coverage
```

### **Scenario 5: Technical Writer Workflow**
```
User Story: "As a tech writer, I need to find all user-facing features"

Actions:
1. Search documents for "user guide" content
2. RAG search: "user interface requirements"
3. Export structured documentation
```

---

## 📋 **DATA GENERATION CHECKLIST**

- [ ] Verify Phenotype org exists or create Argis-Org
- [ ] Set workspace context
- [ ] Create 5 projects with descriptions
- [ ] Create 15 documents (3 per project)
- [ ] Generate 150 requirements with variety:
  - [ ] 30% critical/high priority
  - [ ] 50% medium priority
  - [ ] 20% low priority
  - [ ] Mix of statuses (active, approved, draft)
  - [ ] Realistic healthcare/genomics content
- [ ] Create 15 test cases
- [ ] Add 15 properties/metadata
- [ ] Add team member relationships
- [ ] Verify total count ~200 entities
- [ ] Test sample queries
- [ ] Document demo scenarios

---

## 🎯 **SUCCESS CRITERIA**

1. ✅ ~200 entities created
2. ✅ Realistic healthcare/genomics domain data
3. ✅ Variety in priorities, statuses, types
4. ✅ Cross-project data for complex queries
5. ✅ Relationships established (project members, requirement tests)
6. ✅ All entity types represented
7. ✅ Searchable with semantic meaning
8. ✅ Demonstrates full MCP functionality

---

**Ready to execute after authentication** ✅
