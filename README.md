# AI Agent Hub

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-pytest-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Style](https://img.shields.io/badge/style-PEP8-informational)

A production-quality, modular AI agent framework in Python featuring lifecycle-driven agents, dynamic tool registration, hybrid memory (short-term + ChromaDB long-term), and multi-agent orchestration.

## Why this project

`AI Agent Hub` demonstrates strong engineering practices for real-world autonomous systems:

- Clear architecture with separation of concerns
- Async-first design for I/O-bound operations
- Extensible tools and agents with plugin-style registration
- Streamed lifecycle events for observability
- Exportable conversation history for auditing
- Built-in metrics for performance and reliability tracking

## Architecture

```text
+---------------------------------------------------------------+
|                          AI Agent Hub                         |
+---------------------------------------------------------------+
|  CLI (Typer)                                                  |
|   - run-agent / orchestrate / list-tools / metrics            |
+-----------------------------+---------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|                         AgentHub Facade                       |
|  - ToolRegistry                                                |
|  - MemoryManager                                               |
|  - Built-in Agents (Research, Code, Planner)                  |
|  - MultiAgentCoordinator                                       |
+------------------+---------------------+----------------------+
                   |                     |
                   v                     v
+------------------------+     +-------------------------------+
|      ToolRegistry      |     |          MemoryManager        |
|  web_search            |     |  ShortTermMemory              |
|  file_reader/writer    |     |  ChromaLongTermMemory         |
|  python_executor       |     +-------------------------------+
|  calculator            |
|  api_caller            |
+------------------------+
                   ^
                   |
+---------------------------------------------------------------+
|                   BaseAgent Lifecycle                         |
|   initialize -> plan -> act -> observe -> reflect             |
|   (streaming events + metrics at each stage)                  |
+---------------------------------------------------------------+
```

## Features

### Core architecture

- `BaseAgent` abstract lifecycle (`initialize -> plan -> act -> observe -> reflect`)
- `ToolRegistry` with dynamic registration and execution
- `MemoryManager` combining:
  - short-term conversation history
  - long-term semantic memory with ChromaDB (plus fallback if unavailable)
- `MultiAgentCoordinator` for planner-driven delegation

### Built-in tools

- `web_search` (DuckDuckGo)
- `file_reader`
- `file_writer`
- `python_executor` (restricted sandbox)
- `calculator` (AST-safe evaluator)
- `api_caller` (generic HTTP tool)

### Built-in agents

- `ResearchAgent`: web retrieval + source citations
- `CodeAgent`: implement/review/debug workflows
- `PlannerAgent`: decomposition into subtasks for delegation

### Standout capabilities

- CLI powered by Typer
- Streaming output for lifecycle and orchestration events
- Conversation export (`json` / `markdown`)
- Agent performance metrics snapshot

## Project structure

```text
ai-agent-hub/
├── src/ai_agent_hub/
│   ├── agents/
│   ├── core/
│   ├── tools/
│   ├── cli.py
│   └── hub.py
├── tests/
├── examples/
├── .github/workflows/ci.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Quick start

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2. Run an agent

```bash
ai-agent-hub run-agent --agent planner --task "Research FastAPI and implement a starter service"
```

### 3. Run orchestration

```bash
ai-agent-hub orchestrate --task "Research async Python best practices and write starter code"
```

### 4. Stream lifecycle events

```bash
ai-agent-hub run-agent --agent research --task "LLM observability tools" --stream
```

### 5. Export conversation history

```bash
ai-agent-hub export-history --output exports/history.md --fmt markdown
```

## Configuration

Environment variables:

- `AI_AGENT_HUB_LOG_LEVEL` (default: `INFO`)
- `AI_AGENT_HUB_MEMORY_PATH` (default: `.agent_memory`)
- `AI_AGENT_HUB_DEFAULT_TIMEOUT` (default: `15`)
- `AI_AGENT_HUB_WORKSPACE` (default: current directory)

## API reference

### `AgentHub`

- `run_agent(agent_name: str, task: str)`
- `stream_agent(agent_name: str, task: str)`
- `orchestrate(task: str)`
- `stream_orchestration(task: str)`
- `export_history(output_path: Path, fmt: str)`
- `metrics_snapshot()`

### `ToolRegistry`

- `register(tool: BaseTool)`
- `unregister(tool_name: str)`
- `list_tools()`
- `execute(tool_name: str, **kwargs)`

### `BaseAgent`

Implement `plan()` and `act()`; override `observe()` / `reflect()` as needed.

## Example output

Single agent streaming:

```text
[initialize] Initialized agent context
[plan] Generated plan
[act] Executed actions
[observe] Captured observations
[reflect] Generated reflection
[complete] Run completed
```

Orchestration streaming:

```text
[orchestrator_plan] Planner generated subtasks
[delegation] Delegated subtask to research
[delegation] Delegated subtask to code
[orchestrator_complete] Multi-agent execution complete
```

## Development

```bash
ruff check src tests examples
pytest
```

CI runs lint + tests on Python 3.10/3.11/3.12.

## License

MIT (`LICENSE`).
