# Documentation Gaps to Address

Based on the new documentation guidelines in `AGENTS.md`, here are items that should be retroactively documented:

## README.md Updates Needed

### 1. Standard Mode Documentation
**Status:** Partially documented  
**Issue:** Standard mode is mentioned but not clearly explained  
**Action:** Add a dedicated section explaining:
- What standard mode optimizes for (MetaTFT trait scores as primary objective)
- How it differs from bronze mode (trait-first vs bronze-first)
- When to use standard mode vs bronze mode
- That standard mode still respects quality anchors and validity gates

**Location:** Add after "Ryze mode" section, before "Itemization mode"

### 2. `seed_verticals` Config Option
**Status:** Not documented in README  
**Issue:** Config option exists and is used but not mentioned in user-facing docs  
**Action:** Document in the "Configuring runs with `config.json`" section:
- What vertical seeding does (pre-seeds beam with trait-vertical teams)
- Why it's useful (helps reach far breakpoints like Void 9)
- Default value (true)

### 3. `must_have_itemized_tank` Clarification
**Status:** Mentioned but could be clearer  
**Issue:** The description is brief and doesn't explain the "itemized" part  
**Action:** Expand explanation:
- Clarify that it requires a champion with tank items from MetaTFT data
- Explain what happens if no tank champions are identified (all quality units count)
- Note that this is separate from quality tank requirements

### 4. API Rate Limiting Details
**Status:** Environment variables mentioned but not explained  
**Issue:** Rate limiting exists but users don't know what it does  
**Action:** Add to API Documentation section:
- Explain that all endpoints are rate-limited
- Default limits (100 requests per 60 seconds)
- How to configure via environment variables
- What happens when rate limit is exceeded (429 status)

### 5. API Logging and Middleware
**Status:** Not documented  
**Issue:** Request logging middleware exists but not mentioned  
**Action:** Add to API Documentation section:
- Explain request/response logging
- Log format options (JSON or simple)
- How to configure via environment variables

## docs/ Updates Needed

### 1. Standard Mode Algorithm Documentation
**Status:** Not documented  
**Issue:** Standard mode behavior is not explained in technical docs  
**Action:** Create `docs/standard_mode.md` or add section to `docs/bronze_for_life.md`:
- Explain that standard mode uses MetaTFT trait scores as primary objective
- Document that it still uses the same sort key structure but with trait_stats enabled
- Note that bronze scoring and quality anchors still apply
- Explain how trait_stats influence ranking when enabled

### 2. Architecture Split Documentation
**Status:** Partially outdated  
**Issue:** `docs/repo_overview.md` mentions `solver.py` but the code was split  
**Action:** Update `docs/repo_overview.md`:
- Note that solver logic is split across:
  - `beam_search.py` - Core beam search algorithm
  - `scoring.py` - Scoring and evaluation functions
  - `team_builder.py` - Team building and requirement checking
- Update references to reflect the new structure
- `solver.py` now just re-exports for backward compatibility

### 3. Quality Threshold Calculation Details
**Status:** Partially documented  
**Issue:** The "7th-best unit" detail is mentioned but calculation method unclear  
**Action:** Expand in `docs/bronze_for_life.md`:
- Explain that quality threshold = power of 7th-best unit (or 6th if fewer than 7 units)
- Clarify that this is calculated from sorted power list of playable champions
- Note that tank quality threshold may be lower (minimum of carry threshold and max tank power)

### 4. Sort Key Ordering for Standard Mode
**Status:** Not documented  
**Issue:** Sort key structure is documented for bronze but not explained for standard  
**Action:** Add to `docs/bronze_for_life.md` or create standard mode doc:
- Document that sort key structure is the same for both modes
- Explain that in standard mode, `trait_score` is non-zero (from trait_stats)
- Note that bronze_score still dominates in bronze mode, trait_score in standard mode
- Clarify the exact sort key tuple structure

### 5. Vertical Seeding Algorithm
**Status:** Not documented  
**Issue:** `seed_verticals` feature exists but algorithm not explained  
**Action:** Add to `docs/repo_overview.md` or create new section:
- Explain how vertical seeds are generated
- Document that it creates initial beam states targeting highest breakpoints
- Note when this is most useful (far-off breakpoints)

### 6. Emblem Selection Algorithm
**Status:** Partially documented  
**Issue:** Emblem selection logic exists but greedy algorithm not explained  
**Action:** Expand in `docs/bronze_for_life.md`:
- Document that `choose_best_emblems` uses a greedy selection algorithm
- Explain it evaluates each candidate emblem and picks the best
- Note it respects validity gates and quality requirements

## Priority Recommendations

### High Priority (User-Facing)
1. **Standard Mode Documentation** - Users need to understand when to use it
2. **`seed_verticals` Config Option** - Users should know about this feature
3. **API Rate Limiting** - Users hitting limits need to understand why

### Medium Priority (Technical Clarity)
4. **Standard Mode Algorithm** - Developers need to understand the differences
5. **Architecture Split** - Developers need accurate code structure info
6. **Quality Threshold Details** - Important for understanding behavior

### Low Priority (Implementation Details)
7. **Vertical Seeding Algorithm** - Nice to have for deep understanding
8. **Emblem Selection Algorithm** - Implementation detail, less critical
9. **Sort Key Ordering** - Already partially documented
