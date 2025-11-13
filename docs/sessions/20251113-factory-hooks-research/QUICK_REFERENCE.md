# Factory Hooks: Quick Reference Card

**Session:** 20251113-factory-hooks-research  
**Last Updated:** November 13, 2025

---

## 🚀 Quick Start (4-8 Hours)

### 1. Enable Hooks
```bash
# Edit ~/.factory/settings.json
# Add "hooks": { ... } configuration
```

### 2. Create Structure
```bash
mkdir -p .factory/hooks/{validation,verification,security}
chmod +x .factory/hooks/**/*.{py,sh}
```

### 3. Implement 5 Foundation Hooks
1. ✅ File Size Enforcer (`validation/file_size_validator.py`)
2. ✅ Code Formatter (`verification/code_formatter.sh`)
3. ✅ Secret Detector (`security/secret_detector.py`)
4. ✅ Test Runner (`verification/test_runner.py`)
5. ✅ Coverage Enforcer (`verification/coverage_enforcer.sh`)

### 4. Test
```bash
python cli.py test run --scope unit
# Hooks should trigger automatically
```

---

## 📚 Documentation Map

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **SESSION_COMPLETION_SUMMARY.md** | Overview, status, next steps | Start here |
| **UNIFIED_IMPLEMENTATION_GUIDE.md** | Step-by-step implementation | Implementing hooks |
| **DEEP_DIVES_COMPLETE_SUMMARY.md** | Comprehensive impact analysis | Understanding value |
| **01_DEEP_DIVE_CODE_QUALITY_AUTOMATION.md** | 8 quality hooks (8,000 words) | Implementing quality hooks |
| **02_DEEP_DIVE_TESTING_AUTOMATION.md** | 5 testing hooks (7,500 words) | Implementing test hooks |
| **03_DEEP_DIVE_GIT_WORKFLOW_ENHANCEMENTS.md** | 4 git hooks (6,500 words) | Implementing git hooks |
| **04_DEEP_DIVE_SECURITY_ENFORCEMENT.md** | 3 security hooks (7,000 words) | Implementing security hooks |
| **FACTORY_HOOKS_COMPREHENSIVE_PLAN.md** | Master plan, rollout strategy | Planning deployment |

---

## 🎯 20 Hooks at a Glance

### Code Quality (8 Hooks)
| Hook | Event | File | Impact |
|------|-------|------|--------|
| File Size Enforcer | PreToolUse | `validation/file_size_validator.py` | 100% prevention |
| Code Formatter | PostToolUse | `verification/code_formatter.sh` | 100% automation |
| Import Organizer | PostToolUse | `verification/import_sorter.sh` | 100% automation |
| Type Hint Validator | PostToolUse | `verification/type_hint_validator.py` | 75% improvement |
| Docstring Enforcer | PostToolUse | `verification/docstring_enforcer.py` | 90% coverage |
| Naming Validator | PostToolUse | `verification/naming_validator.py` | 100% compliance |
| TODO Blocker | PreToolUse | `validation/todo_blocker.py` | 100% prevention |
| Line Length | PostToolUse | `verification/line_length_enforcer.sh` | 100% automation |

### Testing (5 Hooks)
| Hook | Event | File | Impact |
|------|-------|------|--------|
| Test Runner | PostToolUse | `verification/test_runner.py` | 100% automation |
| Coverage Enforcer | PostToolUse | `verification/coverage_enforcer.sh` | 100% enforcement |
| Fixture Validator | PostToolUse | `verification/test_fixture_validator.py` | 75% reduction |
| Mock Validator | PostToolUse | `verification/mock_client_validator.py` | 100% enforcement |
| Marker Validator | PostToolUse | `verification/test_marker_validator.py` | 100% compliance |

### Git Workflow (4 Hooks)
| Hook | Event | File | Impact |
|------|-------|------|--------|
| Commit Validator | PreToolUse | `validation/commit_message_validator.py` | +40% quality |
| Co-Author Injector | PreToolUse | `transformation/coauthor_injector.sh` | 100% automation |
| Branch Protection | PreToolUse | `validation/branch_protection.py` | 100% prevention |
| Forward-Only | PreToolUse | `validation/forward_only_enforcer.py` | 100% prevention |

### Security (3 Hooks)
| Hook | Event | File | Impact |
|------|-------|------|--------|
| Secret Detector | PreSessionStart, PreToolUse | `security/secret_detector.py` | 100% prevention |
| Env Validator | PostToolUse | `security/env_validator.py` | 100% enforcement |
| Destructive Blocker | PreToolUse | `security/destructive_operation_blocker.py` | 100% prevention |

---

## 💻 Atoms CLI (Required)

### Always Use atoms CLI
```bash
# ✅ CORRECT
python cli.py test run --scope unit
python cli.py lint check
python cli.py format

# ❌ INCORRECT
uv run pytest tests/unit
uv run ruff check .
uv run black .
```

### Why?
- ✅ Hook integration (automatic when enabled)
- ✅ Consistent interface
- ✅ Better error messages
- ✅ Type-safe validation
- ✅ Self-documenting

---

## 📊 Expected Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| File size violations | 3-4/month | 0 | 100% ↓ |
| Test feedback | 5-30 min | 2-60 sec | **10-30x faster** |
| Coverage <80% | ~30% files | 0% | 100% ↓ |
| Credential leaks | 2-3/year | 0 | 100% ↓ |
| Force pushes | 2-3/year | 0 | 100% ↓ |
| **Time saved** | - | **~300 hrs/year** | - |

---

## 🔧 Common Commands

### Testing Hooks
```bash
# Test file size validator
echo '{...}' | .factory/hooks/validation/file_size_validator.py

# Test all hooks
.factory/hooks/test_hooks.sh

# Measure performance
time echo '{...}' | .factory/hooks/validation/file_size_validator.py
```

### Configuration
```bash
# View current hooks
jq '.hooks' ~/.factory/settings.json

# Validate JSON
jq . ~/.factory/settings.json

# Check project directory
echo $FACTORY_PROJECT_DIR
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Hooks not running | Check `jq '.hooks' ~/.factory/settings.json` |
| Script not executable | `chmod +x .factory/hooks/**/*.{py,sh}` |
| Timeout | Increase timeout in settings.json |
| False positives | Add whitelist patterns to hook |
| Performance | Enable caching, optimize logic |

---

## 📞 Next Actions

1. **Quick Start** (4-8 hours)
   - Enable hooks in settings.json
   - Create .factory structure
   - Implement 5 foundation hooks

2. **Full Deployment** (1.5-2 weeks)
   - Follow UNIFIED_IMPLEMENTATION_GUIDE.md
   - Implement all 20 hooks in 4 phases

3. **OpenSpec Proposal** (2-3 hours)
   - Package as openspec change
   - Create proposal.md and tasks.md

---

## 🎯 Success Criteria

✅ File size validator blocks files >500 lines  
✅ Code formatter runs automatically  
✅ Secret detector blocks credentials  
✅ Test runner executes relevant tests  
✅ Coverage enforcer maintains ≥80%  
✅ Git commits follow conventional format  
✅ No accidental force pushes  
✅ Developer time saved: ~300 hrs/year  

---

**Ready to implement?** Start with **UNIFIED_IMPLEMENTATION_GUIDE.md**
