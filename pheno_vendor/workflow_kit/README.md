# Workflow-Kit

Workflow orchestration with saga pattern for Python applications.

## Features

- **Saga Pattern**: Distributed transactions with automatic compensation
- **Workflow Engine**: Sequential workflow execution
- **State Machine**: FSM for state management
- **Scheduler**: Background job scheduling
- **Metrics**: Workflow execution tracking

## Installation

```bash
pip install workflow-kit

# With scheduler
pip install workflow-kit[scheduler]

# With TUI monitoring
pip install workflow-kit[tui]

# All features
pip install workflow-kit[all]
```

## Quick Start

### Saga Pattern

```python
from workflow_kit import Saga, SagaExecutor

# Define saga
saga = Saga("process_order")

saga.add_step(
    name="reserve_inventory",
    action=lambda ctx: inventory.reserve(ctx["order_id"]),
    compensation=lambda ctx: inventory.release(ctx["order_id"])
)

saga.add_step(
    name="charge_payment",
    action=lambda ctx: payment.charge(ctx["amount"]),
    compensation=lambda ctx: payment.refund(ctx["transaction_id"])
)

# Execute with automatic compensation on failure
executor = SagaExecutor()
result = await executor.execute(saga, {
    "order_id": "123",
    "amount": 100
})
```

### Workflow

```python
from workflow_kit import Workflow, WorkflowEngine

workflow = Workflow("data_pipeline")

workflow.add_step("fetch", fetch_data)
workflow.add_step("transform", transform_data)
workflow.add_step("save", save_data)

engine = WorkflowEngine()
execution = await engine.execute(workflow, {"input": "data"})
```

### Scheduler

```python
from workflow_kit.scheduling import WorkflowScheduler

scheduler = WorkflowScheduler()

# Schedule every 5 minutes
scheduler.schedule_interval(
    "cleanup",
    cleanup_handler,
    minutes=5
)

await scheduler.start()
```

### State Machine

```python
from workflow_kit import StateMachine

sm = StateMachine(initial_state="draft")

sm.add_state("draft")
sm.add_state("submitted")
sm.add_state("approved")

sm.add_transition("draft", "submitted", "submit")
sm.add_transition("submitted", "approved", "approve")

sm.trigger("submit")
print(sm.current_state)  # "submitted"
```

## Documentation

See `/examples` for complete examples.
