# Research & Design Decisions

## Summary

- **Feature**: `llm-passport-crosscheck`
- **Discovery Scope**: Complex Integration
- **Key Findings**:
  - Claude and Gemini vision APIs use similar patterns (base64 images + text prompts) with structured JSON output support
  - Existing PassportExtractionService provides clean integration points for extending with LLM-based extraction
  - Python asyncio provides robust patterns for parallel execution with timeout handling via TaskGroup (Python 3.11+)

## Research Log

### Vision LLM API Investigation

- **Context**: Requirements 1.4 specifies support for Claude and Gemini as vision LLM providers for visual zone extraction
- **Sources Consulted**:
  - [Claude Vision Documentation](https://platform.claude.com/docs/en/build-with-claude/vision)
  - [Google Gen AI SDK](https://googleapis.github.io/python-genai/)
  - [Gemini Vision Documentation](https://ai.google.dev/gemini-api/docs/vision)

- **Findings**:
  - **Claude API**:
    - SDK: `anthropic` package
    - Image formats: JPEG, PNG, GIF, WebP
    - Max image size: 5MB per image (API), up to 100 images per request
    - Image transmission: base64-encoded or URL reference
    - Response: Text content via Messages API
    - Model: `claude-sonnet-4-5` recommended for vision tasks
    - Token cost: ~1,600 tokens for 1.15 megapixel images

  - **Gemini API**:
    - SDK: `google-genai` package (new unified SDK, replaces deprecated `google-generativeai`)
    - Image formats: PNG, JPEG, WEBP, HEIC, HEIF
    - Image transmission: `Part.from_bytes()` for inline, Files API for larger files
    - Model: `gemini-3-flash-preview` for fast inference
    - Token cost: 258 tokens for images <= 384px, tiles larger images at 768x768

- **Implications**:
  - Both APIs support structured JSON output via response schema specification
  - Provider abstraction layer needed to normalize API differences
  - Common image preprocessing (resize, format conversion) can optimize costs

### Parallel Execution Pattern Investigation

- **Context**: Requirement 1.1 specifies parallel extraction from both MRZ and vision LLM
- **Sources Consulted**:
  - [Python asyncio documentation](https://docs.python.org/3/library/asyncio-task.html)
  - [asyncio.gather() timeout patterns](https://superfastpython.com/asyncio-gather-timeout/)
  - [TaskGroup in Python 3.11+](https://www.dataleadsfuture.com/why-taskgroup-and-timeout-are-so-crucial-in-python-3-11-asyncio/)

- **Findings**:
  - `asyncio.gather()` with `return_exceptions=True` allows continuing when one source fails
  - `asyncio.timeout()` context manager provides clean timeout handling
  - TaskGroup (Python 3.11+) offers stronger cancellation guarantees but project targets 3.12+
  - For sync callers, `asyncio.run()` or event loop management required

- **Implications**:
  - Use asyncio.gather for parallel MRZ + LLM extraction
  - Wrap in asyncio.timeout() for configurable timeouts (Requirement 4.5, 4.6)
  - return_exceptions=True enables fallback handling (Requirement 4)

### Existing Architecture Analysis

- **Context**: Feature extends existing passport extraction service
- **Sources Consulted**: Codebase analysis via Grep/Read

- **Findings**:
  - **PassportExtractionService**: Framework-agnostic orchestration layer with dependency injection
  - **MRZExtractor**: Wraps PassportEye, returns `RawMRZData`
  - **MRZValidator**: ICAO 9303 check digit validation
  - **PassportData**: Core data model with optional fields, confidence, source tracking
  - **Exception hierarchy**: `TryAlmaError` -> `ProcessingError` -> `PassportExtractionError`

- **Implications**:
  - New CrossCheckService can follow same patterns as existing services
  - Can reuse MRZExtractor directly for MRZ source
  - PassportData model needs extension for cross-check metadata
  - Exception hierarchy extensible for LLM-specific errors

### Confidence Scoring Algorithm Research

- **Context**: Requirements 3.1-3.5 specify confidence scoring methodology
- **Sources Consulted**: Domain analysis

- **Findings**:
  - Field-level confidence: 1.0 when sources agree, reduced when they disagree
  - Single-source confidence: 0.5-0.7 range per requirements
  - Document-level: Weighted average of field confidences
  - Weighting factors: Critical fields (passport number, DOB) weighted higher

- **Implications**:
  - Configurable confidence thresholds (Requirement 7.3)
  - Weighted average calculation needs defined field weights
  - Discrepancy severity affects confidence reduction amount

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Service Layer Extension | Add CrossCheckService alongside existing PassportExtractionService | Follows existing patterns, minimal architectural change | May duplicate some orchestration logic | Selected approach |
| Strategy Pattern for Providers | Abstract LLM providers behind common interface | Clean provider switching, testable | Additional abstraction layer | Part of selected approach |
| Event-Driven Pipeline | Pub/sub for extraction stages | Decoupled stages, observable | Overly complex for current needs | Rejected |

## Design Decisions

### Decision: Provider Abstraction with Protocol

- **Context**: Need to support Claude and Gemini with potential for future providers
- **Alternatives Considered**:
  1. Concrete classes with switch/case selection
  2. Abstract base class with inheritance
  3. Protocol-based interface (structural subtyping)
- **Selected Approach**: Protocol-based interface (`VisionLLMProvider` Protocol)
- **Rationale**: Aligns with Python typing best practices, enables duck typing, cleaner testing
- **Trade-offs**: Slightly more setup than concrete classes, but better extensibility
- **Follow-up**: Ensure both Claude and Gemini implementations pass protocol check

### Decision: Async-First Design with Sync Wrapper

- **Context**: LLM APIs are I/O-bound, parallel execution benefits from async
- **Alternatives Considered**:
  1. Fully synchronous with threading
  2. Fully async throughout
  3. Async core with sync public API wrapper
- **Selected Approach**: Async core with sync wrapper for backward compatibility
- **Rationale**: Existing service is sync; async core enables parallel LLM calls
- **Trade-offs**: Dual interface adds complexity, but maintains compatibility
- **Follow-up**: Document async usage pattern for advanced users

### Decision: Field Normalization Before Comparison

- **Context**: MRZ and visual zone may have different formats for same data
- **Alternatives Considered**:
  1. Direct string comparison
  2. Normalization then comparison
  3. Fuzzy matching with Levenshtein distance
- **Selected Approach**: Normalization (case, whitespace, diacritics) then exact comparison
- **Rationale**: Per Requirement 2.2, handles format differences without false positives
- **Trade-offs**: May miss slight OCR errors; could add fuzzy matching later
- **Follow-up**: Consider configurable fuzzy threshold for edge cases

### Decision: Discrepancy Severity Classification

- **Context**: Requirement 5.5 requires severity levels for discrepancies
- **Alternatives Considered**:
  1. Binary match/mismatch
  2. Three-level severity (critical/warning/informational)
  3. Numeric severity score
- **Selected Approach**: Three-level enumerated severity
- **Rationale**: Clear categorization, actionable for downstream consumers
- **Trade-offs**: Subjective classification boundaries
- **Follow-up**: Define clear rules for each severity level in implementation

## Risks & Mitigations

- **Risk 1: LLM API latency varies significantly** - Mitigation: Configurable timeouts per source (Req 4.5, 4.6), fallback handling when timeout occurs
- **Risk 2: LLM extraction accuracy varies by passport format** - Mitigation: Structured prompts with explicit field requests, cross-validation catches errors
- **Risk 3: API rate limits and costs** - Mitigation: Document rate limit considerations, support provider switching
- **Risk 4: API key management complexity** - Mitigation: Environment variable pattern, clear configuration errors

## References

- [Claude Vision Documentation](https://platform.claude.com/docs/en/build-with-claude/vision) - Python SDK patterns, image limits, supported formats
- [Google Gen AI SDK](https://github.com/googleapis/python-genai) - New unified SDK for Gemini
- [Gemini Vision Docs](https://ai.google.dev/gemini-api/docs/vision) - Image understanding capabilities
- [Python asyncio Tasks](https://docs.python.org/3/library/asyncio-task.html) - gather(), timeout(), TaskGroup patterns
- [Existing passport-data-extraction-cli design](/.kiro/specs/passport-data-extraction-cli/design.md) - Architecture patterns to follow
