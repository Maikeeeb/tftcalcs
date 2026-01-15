# Available Agents

This directory contains reusable agent role definitions for AI-assisted development. Each agent has specific responsibilities, constraints, and domain knowledge.

## Quick Reference

| Agent | Focus Area | Key Responsibilities |
|-------|------------|---------------------|
| [Backend Solver Agent](backend-solver-agent.md) | Python solver logic | Bronze-for-Life algorithm, beam search, scoring |
| [Frontend UI Agent](frontend-ui-agent.md) | React/TypeScript UI | Components, Material-UI, user interactions |
| [API Agent](api-agent.md) | FastAPI endpoints | REST API, validation, error handling |
| [Testing Agent](testing-agent.md) | Test automation | pytest, Vitest, test coverage |
| [Data Agent](data-agent.md) | Data management | Data files, schemas, validation |

## Usage Pattern

Reference agents in your prompts like this:

```
Use the Frontend UI Agent defined in agents/frontend-ui-agent.md.
Improve spacing and responsiveness for the FilterPanel component.
Do not touch logic.
```

Or:

```
Use the Backend Solver Agent.
Review the bronze scoring thresholds in scoring.py.
Ensure determinism is maintained.
```

## Agent Responsibilities

### Backend Solver Agent
- Bronze-for-Life algorithm implementation
- Beam search and optimization
- Scoring functions and tradeoffs
- Deterministic algorithm guarantees

### Frontend UI Agent
- React component development
- TypeScript type safety
- Material-UI theming and components
- User interaction patterns
- Accessibility standards

### API Agent
- FastAPI endpoint design
- Request/response validation
- Error handling and logging
- Rate limiting and CORS
- API versioning

### Testing Agent
- Backend testing with pytest
- Frontend testing with Vitest/React Testing Library
- Test coverage maintenance (90% minimum)
- Integration testing
- Test data and fixtures

### Data Agent
- Data file management (`data/` directory)
- Schema validation (`schemas/` directory)
- Data consistency and integrity
- MetaTFT data parsing
- Configuration data validation

## Global Rules

All agents must follow the global rules defined in [`AGENTS.md`](../AGENTS.md), including:

- Scope and exceptions/overrides
- Non-goals
- Intent clarity
- Architecture constraints
- Coding conventions
- Pre-commit requirements
- Documentation guidelines
- Change discipline

## Agent Boundaries

Agents have clear boundaries to prevent conflicts:

- **Backend Solver Agent** does not modify UI or API code
- **Frontend UI Agent** does not modify solver logic or Python code
- **API Agent** does not modify solver logic or frontend components
- **Testing Agent** does not modify production code unless fixing bugs
- **Data Agent** does not modify solver logic or UI code

## Adding New Agents

When adding a new agent role:

1. Create a new file: `agents/<role-name>-agent.md`
2. Follow the template structure (Responsibilities, Constraints, Quality Bar, Domain-Specific Rules)
3. Update this index file
4. Ensure the agent follows global rules from `AGENTS.md`

## Agent Chaining

Agents can be chained for complex tasks:

1. **UI Agent** → Layout and visual hierarchy
2. **Component Agent** → Props cleanup and boundaries
3. **Testing Agent** → Test coverage and edge cases

Each agent does one thing well and leaves the code cleaner for the next.
