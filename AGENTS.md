# Repository-wide agent guidelines

## Scope

- This file applies to the entire repository and all AI-assisted changes.

## Exceptions & Overrides

- If a user request directly contradicts this document:
    1. The agent MUST pause and call out the conflict explicitly
    2. The agent MUST ask whether this is a one-off exception or a new rule
    3. The agent MUST NOT silently violate existing guidelines
- If an exception is approved, the agent should:
    - Propose an update to this file explaining why the exception exists
    - Scope the exception narrowly (what changes, what does not)

## Invariants (Do Not Break)

- Bronze-for-Life scoring must remain deterministic
- The same input config must always produce the same team
- Removing a bronze trait must always be a conscious tradeoff, not a side-effect
- Adding unit quality must never invalidate mandatory board structure

## Non-Goals

- This project does NOT aim to maximize winrate
- This project does NOT aim to auto-play TFT or simulate fights
- This project does NOT aim to perfectly mirror MetaTFT rankings

## Intent Clarity

- Do not infer unstated goals
- Do not generalize a specific request into a broader redesign
- If intent is ambiguous, ask before acting

## Entry Points

- **Bronze for Life CLI:** Run via `python -m bfl.bronze_for_life`
- **Tutorial:** See `examples/bronze_for_life_tutorial.py` for a walkthrough of CLI usage

## Configuration

- Configuration files live in `config.json` and `schemas/config_schema.json`
- Configuration helpers are in `bfl/config_loader.py`
- Do NOT rename or remove config keys without updating the schema and tutorial

## UI Workflow

1. Create/activate a Python venv and install FastAPI dependencies
2. Run `npm install` in the `frontend` directory
3. Start the API with:
   `uvicorn ui_api.main:app --reload --port 8000`
4. Run frontend tests with `npm test` (in `frontend/` directory) before committing changes
5. Verify frontend test coverage meets the 90% minimum requirement with `npm run test:coverage`

## Data Awareness

- Check `data/en_us.json` and the MetaTFT text files
  (`data/metatft_units.txt`, `data/metatft_traits.txt`) when making data-related changes
- Do not hardcode trait or unit names that already exist in these files

---

## Bronze for Life — Core Philosophy

Bronze-for-Life mode is **not a standard optimization problem**.

Agents must respect the following intent:

- Bronze traits have **diminishing returns**
    - The first ~6 bronze traits are mandatory
    - Additional bronze traits are beneficial but not absolute
- Bronze count must **never be treated as a linear objective**

## Decision Hierarchy for Bronze for life algorithm

When tradeoffs occur, prefer decisions in this order:

1. Preserve Bronze-for-Life invariants
2. Preserve mandatory board structure
3. Preserve bronze count thresholds
4. Improve unit quality
5. Use trait statistics as tie-breakers only
6. Micro-optimize scoring

### Mandatory Board Structure

- A valid Bronze-for-Life team must include:
    - At least one **high-quality tank**
    - At least one **high-quality damage carry**
- A “quality” unit must activate **at least one of its traits**
- It is acceptable to lose a bronze trait to add a top-tier or high-winrate unit

### Trait Statistics

- Trait statistics are **tie-breakers only** in Bronze-for-Life
- Trait stats must not outweigh:
    - Bronze count thresholds
    - Mandatory quality units
- Traits may be upgraded beyond bronze only if their stats are excellent
  (e.g., average placement ≲ 4.2)

### Emblems

- Emblems may be used to preserve bronze count while improving unit quality
- Emblem-only bronze traits should not be overly rewarded

---

## Architecture Constraints

- Bronze-for-Life logic and Standard mode logic must remain conceptually distinct
- Do NOT merge or unify scoring objectives unless explicitly requested
- Beam search structure should not be rewritten unless explicitly instructed
- Prefer small, localized changes over global refactors

## Coding Conventions

- Follow both Python and TypeScript standards as appropriate
- Prefer explicit, readable logic over clever optimizations
- Avoid introducing new dependencies unless necessary

## Pre-Commit Requirements

All code must pass pre-commit hooks before committing. The following standards are enforced:

### Code Formatting (Black)
- **Line length:** Maximum 100 characters per line
- Black will auto-format code, but agents should write code that follows this limit
- Run `black --line-length=100` to format code before committing

### File Standards
- Files must end with a newline character
- No trailing whitespace allowed
- YAML, JSON, and TOML files must be valid
- No merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
- Large files (>500KB) will be blocked

### Type Checking (MyPy)
- MyPy runs with relaxed settings to allow gradual typing
- Current settings: `--ignore-missing-imports`, `--no-strict-optional`, `--allow-untyped-calls`, `--allow-untyped-defs`
- Several error codes are disabled (assignment, index, attr-defined, operator, call-arg, var-annotated, arg-type, call-overload)
- While strict typing is not enforced, agents should still write type-safe code when possible

### Best Practices for Agents
- Write code that will pass Black formatting (100 char line limit)
- Ensure files end with newlines
- Remove trailing whitespace
- Validate JSON/YAML syntax if creating or modifying these files
- Test that `pre-commit run --all-files` passes before considering code complete

## .gitignore Management

### When to Update .gitignore

**MUST update `.gitignore` when:**
- Creating or modifying build/compilation output directories (e.g., `dist/`, `build/`, `out/`)
- Adding test coverage tools that generate reports (e.g., `coverage/`, `htmlcov/`, `.coverage`)
- Introducing dependency management artifacts (e.g., `node_modules/`, `venv/`, `.venv/`, `__pycache__/`)
- Adding IDE/editor configuration directories (e.g., `.idea/`, `.vscode/`, `.vs/`)
- Creating temporary or cache directories (e.g., `.pytest_cache/`, `.mypy_cache/`, `.cache/`)
- Adding log files or runtime artifacts (e.g., `*.log`, `*.tmp`, `.env.local`)
- Setting up package managers that create lock files you don't want tracked (rare, but possible)
- Adding generated documentation or reports (e.g., auto-generated API docs, coverage HTML)

**SHOULD update `.gitignore` when:**
- Adding new tools or frameworks that generate artifacts
- Creating scripts that produce output files
- Setting up new development environments
- Adding configuration files that may contain secrets (e.g., `.env`, `secrets.json`)

**DO NOT add to `.gitignore`:**
- Source code files (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`, etc.)
- Configuration files that are meant to be shared (e.g., `package.json`, `requirements.txt`, `vite.config.ts`)
- Documentation files (`.md`, `.txt`, `.rst`)
- Test files (they should be tracked)
- Schema files or data files that are part of the project
- Build configuration files (e.g., `Dockerfile`, `Makefile`, `.github/workflows/`)

### Categories of Files to Ignore

**Build Artifacts:**
- Compiled code: `*.pyc`, `*.class`, `*.o`, `*.so`, `*.dll`
- Build outputs: `dist/`, `build/`, `out/`, `target/`, `bin/`, `obj/`
- Bundled assets: `*.bundle.js`, `*.chunk.js` (if generated)

**Dependencies:**
- Package manager directories: `node_modules/`, `venv/`, `.venv/`, `env/`, `.env/`
- Package manager lock files: Only if explicitly not wanted (usually `package-lock.json` and `requirements.txt` ARE tracked)

**IDE/Editor Files:**
- IDE directories: `.idea/`, `.vscode/` (unless project-specific settings are shared), `.vs/`, `.eclipse/`
- Editor swap files: `*.swp`, `*.swo`, `*~`, `.DS_Store`

**Test & Coverage:**
- Coverage reports: `coverage/`, `htmlcov/`, `.coverage`, `coverage.xml`, `*.cover`, `.nyc_output/`
- Test cache: `.pytest_cache/`, `.mypy_cache/`, `.hypothesis/`

**Temporary & Runtime:**
- Log files: `*.log`, `logs/`, `*.tmp`
- Environment files: `.env.local`, `.env.*.local` (but `.env.example` should be tracked)
- Cache directories: `.cache/`, `.parcel-cache/`, `.next/`, `.nuxt/`

**OS-Specific:**
- System files: `.DS_Store`, `Thumbs.db`, `desktop.ini`
- OS directories: `.Trash-*`, `*.swp`

**Generated/Compiled Assets:**
- Image files that are generated: Only if they're build artifacts (not source assets)
- Compiled stylesheets: `*.css.map` (if generated), but not source `.css` files
- Minified files: `*.min.js`, `*.min.css` (if generated)

### Best Practices

1. **Be Specific**: Prefer specific paths over broad patterns when possible
   - Good: `frontend/coverage/`, `backend/htmlcov/`
   - Less ideal: `**/coverage/` (unless you have multiple coverage directories)

2. **Group Related Entries**: Use comments to organize sections
   ```gitignore
   # Coverage reports
   htmlcov/
   .coverage
   frontend/coverage/
   ```

3. **Check Before Adding**: Verify that files you're ignoring aren't needed by other developers
   - If a file is needed for the project to work, it should be tracked
   - If a file is generated or environment-specific, it should be ignored

4. **Document Unusual Exclusions**: If you ignore something non-standard, add a comment explaining why

5. **Review Existing Patterns**: Before adding new entries, check if an existing pattern already covers it
   - Example: `**/*.log` might already cover `app.log`

6. **Test Your Changes**: After modifying `.gitignore`, verify that:
   - Previously tracked files that should be ignored are now ignored
   - Important files are still tracked
   - The repository still builds/works correctly

### Common Mistakes to Avoid

- **Ignoring source files**: Never ignore `.py`, `.ts`, `.js`, `.tsx`, `.jsx` files
- **Ignoring configuration files**: Don't ignore `package.json`, `requirements.txt`, `vite.config.ts`, etc.
- **Ignoring test files**: Test files should be tracked
- **Too broad patterns**: Avoid patterns like `**/*.json` that might ignore important config files
- **Ignoring data files**: Project data files (like `data/en_us.json`) should be tracked
- **Forgetting to commit `.gitignore` changes**: Always commit `.gitignore` updates with the changes that require them

### When Creating New Directories or Tools

When introducing new tools, build processes, or directories that generate files:

1. **Identify generated files**: Determine what files/directories the tool creates
2. **Check if they should be tracked**: Generated artifacts typically should not be
3. **Update `.gitignore` immediately**: Add exclusions before committing any generated files
4. **Verify in CI/CD**: Ensure build processes work without tracked artifacts

### Example Workflow

When adding a new tool that generates reports:
```bash
# 1. Tool generates files in reports/ directory
# 2. Before committing, add to .gitignore:
echo "reports/" >> .gitignore
# 3. Verify it works:
git status  # Should not show reports/ files
# 4. Commit both the tool setup AND .gitignore update together
```

## Documentation

- Add or update references in `/docs/` and `readme.md`
- Keep algorithm intent documented, not just behavior

## Testing

### General Testing Requirements

- **Coverage directories must be in `.gitignore`**: See ".gitignore Management" section for details
  - Backend: `htmlcov/`, `.coverage`, `coverage.xml`
  - Frontend: `frontend/coverage/`
- When setting up or modifying test coverage configuration, verify that:
  - Non-code files (images, data files, configs) are excluded from coverage
  - Coverage output directories are in `.gitignore`
  - Coverage thresholds meet project requirements (90% for frontend, 90% for backend)

### Backend Testing (Python)

- Add or update tests in `/tests/` so future updates don't accidentally harm old features
- When changing scoring behavior, add at least one test that encodes the intended tradeoff
- Tests must pass before committing code changes
- Coverage must remain at or above 90% for `bfl/` and `ui_api/` packages
- See "Pre-Commit Requirements" section for code style standards enforced by pre-commit hooks
- Run `pytest --cov` to verify coverage before submitting changes
- Integration tests in `tests/integration/` exercise the complete stack (UI → API → Solver)

### Frontend Testing (TypeScript/React)

- Frontend tests are located in `frontend/src/__tests__/`
- Test utilities and mock data are in `frontend/src/__tests__/test-utils.tsx` and `test-data.ts`
- **Coverage requirement: Frontend code must maintain at least 90% test coverage**
  - Overall coverage targets: 90% statements, 90% functions, 75% branches, 90% lines
  - Component coverage should be 90%+ for all user-facing components
- Run frontend tests with:
  - `npm test` (in `frontend/` directory) - Run all tests
  - `npm run test:coverage` - Run tests with coverage report
  - `npm test -- --watch` - Run tests in watch mode
- Coverage reports are generated in `frontend/coverage/` directory
- When adding new frontend components or features:
  - Create corresponding test files following the naming pattern `ComponentName.test.tsx`
  - Test user interactions, edge cases, and error states
  - Use React Testing Library best practices (query by role, test user behavior)
  - Mock external dependencies (API calls, browser APIs)
- Test files should be comprehensive and cover:
  - Component rendering and display
  - User interactions (clicks, form inputs, navigation)
  - Error handling and edge cases
  - Integration with other components
- See `frontend/TEST_COVERAGE_SUMMARY.md` for current test coverage status and patterns

## Anti-Patterns (Avoid)

- Linear bronze scoring (e.g., bronze_count * weight)
- Collapsing Bronze-for-Life and Standard scoring into one formula
- Replacing thresholds with continuous weights
- Adding “clever” math without tests that encode intent

## Determinism

- Beam search must remain deterministic
- Do not introduce randomness or non-seeded shuffles
- Do not depend on file ordering, dict ordering, or hash iteration

## Separation of Concerns

- Data loading must not contain scoring logic
- Scoring logic must not perform search
- Search logic must not embed configuration defaults
- UI code must not contain solver logic

## Change Discipline

- Any change that alters solver behavior must be documented
- If behavior changes, tests must change first or alongside code
- Refactors must not change outputs unless explicitly requested

## When in Doubt

- Prefer preserving existing behavior over simplification
- Prefer adding comments over rewriting logic
- Ask for clarification instead of guessing intent

## Change Scope & Blast Radius

- Prefer the smallest change that satisfies the request
- Avoid touching unrelated files or logic “while you’re there”
- Large refactors must be split into staged, reviewable steps

## Reversibility

- Prefer changes that are easy to undo
- Avoid destructive migrations or irreversible transformations
- When possible, gate new behavior behind flags or config options

## Glossary

- Bronze trait: A trait active exactly at its first breakpoint
- Quality unit: A unit with strong winrate or average placement that activates at least one trait if they have a trait
  to activate
- Fake bronze: A bronze trait composed entirely of low-quality units
- Mandatory unit: A required tank or damage carry

## Learning from Changes

- If a change reveals a missing rule or invariant:
    - Propose adding it to this document
- This file should evolve as the project’s intent becomes clearer
