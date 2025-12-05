# Libspec Extension Proposals

These proposals address schema gaps discovered while specifying real libraries.

## Proposals

| # | Title | Status | Addresses |
|---|-------|--------|-----------|
| [001](001-principle-metadata.md) | Principle Metadata Extension | Proposed | `category`, `refs`, `source` on principles |
| [002](002-method-decorators.md) | Method Decorator Support | Proposed | `@asynccontextmanager`, `@contextmanager`, etc. |
| [003](003-parameterized-cross-references.md) | Parameterized Cross-References | Proposed | `#/types/Handle[ReturnT]` syntax |
| [004](004-external-type-references.md) | External Type References | Proposed | `pydantic:BaseModel` syntax |
| [005](005-generic-param-descriptions.md) | Generic Parameter Descriptions | Proposed | `description` on generic_params |
| [006](006-maturity-proposed-stage.md) | Add "proposed" Maturity Stage | Proposed | `maturity: "proposed"` |

## Validation Gap Analysis

Using `weave.json` as a test case, here's the current validation status:

### Errors Blocking Validation

| Error | Count | Proposal |
|-------|-------|----------|
| `principles.*.category: Extra inputs not permitted` | 60 | [001](001-principle-metadata.md) |
| `principles.*.refs: Extra inputs not permitted` | 60 | [001](001-principle-metadata.md) |
| `principles.*.source: Extra inputs not permitted` | 60 | [001](001-principle-metadata.md) |
| `generic_params.*.description: Extra inputs not permitted` | ~11 | [005](005-generic-param-descriptions.md) |
| `bases: String should match pattern` (external types) | ~14 | [004](004-external-type-references.md) |
| `bases: String should match pattern` (parameterized) | ~14 | [003](003-parameterized-cross-references.md) |

### Warnings (Information Loss if Stripped)

| Warning | Count | Proposal |
|---------|-------|----------|
| Signature should start with '(' (has decorators) | ~5 | [002](002-method-decorators.md) |
| Signature should start with '(' (has async/def) | ~50 | None (cosmetic) |

### Info (Content Completeness)

| Info | Count | Notes |
|------|-------|-------|
| `maturity: "proposed"` invalid | 641 | [006](006-maturity-proposed-stage.md) - using "specified" as workaround |

## Implementation Priority

1. **High**: Principle metadata (001) - blocks all principles
2. **High**: External type refs (004) - blocks inheritance documentation
3. **Medium**: Generic param descriptions (005) - loses documentation
4. **Medium**: Method decorators (002) - loses semantic behavior
5. **Low**: Parameterized cross-refs (003) - loses precision
6. **Low**: Proposed maturity (006) - workaround exists

## Test Case

The `weave` library spec (`specs/weave.json` in the threads repo) serves as a comprehensive test case for these proposals. Once implemented, it should validate cleanly.
