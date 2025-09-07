# Tasks: WizLight Control System

**Input**: Design documents from `/specs/001-lets-create-a/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → If not found: ERROR "No implementation plan found"
   → Extract: tech stack, libraries, structure
2. Load optional design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Each file → contract test task
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests
   → Core: models, services, CLI commands
   → Integration: DB, middleware, logging
   → Polish: unit tests, performance, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All contracts have tests?
   → All entities have models?
   → All endpoints implemented?
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app**: `backend/src/`, `frontend/static/`
- Using web application structure per plan.md

## Phase 3.1: Setup
- [ ] T001 Create backend/frontend project structure per implementation plan
- [ ] T002 Initialize UV project with FastAPI, pywizlight, uvicorn dependencies
- [ ] T003 [P] Configure pytest with async support in backend/pyproject.toml

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T004 [P] Contract test GET /scan in backend/tests/contract/test_scan_get.py
- [ ] T005 [P] Contract test POST /lights/{ip}/toggle in backend/tests/contract/test_lights_toggle.py
- [ ] T006 [P] Contract test POST /lights/{ip}/brightness in backend/tests/contract/test_lights_brightness.py
- [ ] T007 [P] Contract test POST /lights/{ip}/colortemp in backend/tests/contract/test_lights_colortemp.py
- [ ] T008 [P] Contract test GET /lights/{ip}/state in backend/tests/contract/test_lights_state.py
- [ ] T009 [P] Integration test light discovery flow in backend/tests/integration/test_discovery.py
- [ ] T010 [P] Integration test light control flow in backend/tests/integration/test_control.py
- [ ] T011 [P] Integration test error scenarios in backend/tests/integration/test_error_handling.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T012 [P] LightDevice model in backend/src/models/light_device.py
- [ ] T013 [P] NetworkScan model in backend/src/models/network_scan.py
- [ ] T014 [P] LightControlRequest model in backend/src/models/control_request.py
- [ ] T015 [P] LightControlResponse model in backend/src/models/control_response.py
- [ ] T016 [P] Light discovery service in backend/src/services/discovery_service.py
- [ ] T017 [P] Light control service in backend/src/services/light_service.py
- [ ] T018 [P] CLI discovery command in backend/src/cli/discovery_cli.py
- [ ] T019 [P] CLI light control command in backend/src/cli/light_cli.py
- [ ] T020 GET /scan endpoint in backend/src/api/scan_routes.py
- [ ] T021 POST /lights/{ip}/toggle endpoint in backend/src/api/light_routes.py
- [ ] T022 POST /lights/{ip}/brightness endpoint in backend/src/api/light_routes.py  
- [ ] T023 POST /lights/{ip}/colortemp endpoint in backend/src/api/light_routes.py
- [ ] T024 GET /lights/{ip}/state endpoint in backend/src/api/light_routes.py
- [ ] T025 FastAPI app setup and routing in backend/src/api/main.py
- [ ] T026 Exception handling middleware in backend/src/api/middleware.py

## Phase 3.4: Frontend Implementation  
- [ ] T027 [P] HTML interface in frontend/static/index.html
- [ ] T028 [P] JavaScript API client in frontend/static/app.js
- [ ] T029 [P] CSS styling in frontend/static/styles.css
- [ ] T030 Static file serving setup in backend/src/api/main.py

## Phase 3.5: Integration
- [ ] T031 Error response formatting and logging setup
- [ ] T032 CORS configuration for frontend-backend communication
- [ ] T033 Request/response validation and serialization
- [ ] T034 Async timeout handling for pywizlight operations

## Phase 3.6: Polish  
- [ ] T035 [P] Unit tests for light models in backend/tests/unit/test_models.py
- [ ] T036 [P] Unit tests for services in backend/tests/unit/test_services.py
- [ ] T037 [P] Unit tests for CLI commands in backend/tests/unit/test_cli.py
- [ ] T038 Performance tests (sub-500ms response times) in backend/tests/performance/test_timing.py
- [ ] T039 [P] Frontend unit tests in frontend/tests/test_frontend.js
- [ ] T040 End-to-end workflow testing per quickstart.md scenarios
- [ ] T041 Code cleanup and remove any duplication
- [ ] T042 Update CLAUDE.md with final implementation patterns

## Dependencies
- Setup (T001-T003) before all other tasks
- Tests (T004-T011) before implementation (T012-T026)  
- Models (T012-T015) before services (T016-T017)
- Services (T016-T017) before API endpoints (T020-T025)
- Backend API (T025) before frontend integration (T030)
- Core implementation before integration (T031-T034)
- Integration before polish (T035-T042)

## Parallel Example
```bash
# Launch contract tests together (T004-T008):
Task: "Contract test GET /scan in backend/tests/contract/test_scan_get.py"  
Task: "Contract test POST /lights/{ip}/toggle in backend/tests/contract/test_lights_toggle.py"
Task: "Contract test POST /lights/{ip}/brightness in backend/tests/contract/test_lights_brightness.py"
Task: "Contract test POST /lights/{ip}/colortemp in backend/tests/contract/test_lights_colortemp.py"
Task: "Contract test GET /lights/{ip}/state in backend/tests/contract/test_lights_state.py"

# Launch model creation together (T012-T015):
Task: "LightDevice model in backend/src/models/light_device.py"
Task: "NetworkScan model in backend/src/models/network_scan.py" 
Task: "LightControlRequest model in backend/src/models/control_request.py"
Task: "LightControlResponse model in backend/src/models/control_response.py"

# Launch frontend files together (T027-T029):
Task: "HTML interface in frontend/static/index.html"
Task: "JavaScript API client in frontend/static/app.js"
Task: "CSS styling in frontend/static/styles.css"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing  
- Test with real WiZ lights when available
- Follow TDD: Red-Green-Refactor cycle
- Commit after each task completion
- Use async/await throughout for pywizlight compatibility

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts** (api-spec.yaml):
   - GET /scan → contract test task T004, endpoint task T020
   - POST /lights/{ip}/toggle → contract test T005, endpoint T021
   - POST /lights/{ip}/brightness → contract test T006, endpoint T022
   - POST /lights/{ip}/colortemp → contract test T007, endpoint T023
   - GET /lights/{ip}/state → contract test T008, endpoint T024
   
2. **From Data Model**:
   - LightDevice entity → model task T012
   - NetworkScan entity → model task T013
   - LightControlRequest entity → model task T014
   - LightControlResponse entity → model task T015
   - Discovery service → service task T016
   - Light control → service task T017
   
3. **From User Stories** (quickstart.md scenarios):
   - Light discovery scenario → integration test T009
   - Light control scenario → integration test T010
   - Error handling scenario → integration test T011
   - Full workflow → end-to-end test T040

4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Frontend → Integration → Polish
   - Dependencies prevent inappropriate parallel execution

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All contracts have corresponding tests (T004-T008 cover all endpoints)
- [x] All entities have model tasks (T012-T015 cover all data models)
- [x] All tests come before implementation (T004-T011 before T012+)
- [x] Parallel tasks truly independent (different files, no shared dependencies)
- [x] Each task specifies exact file path (all tasks include full paths)
- [x] No task modifies same file as another [P] task (verified per file)