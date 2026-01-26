# TDoc Ontology Version History

## Version Naming Convention
`tdoc-ontology-vX.Y.Z-phaseN.ttl`

- **X**: Major version (breaking changes)
- **Y**: Minor version (new features)
- **Z**: Patch version (bug fixes)
- **phaseN**: Project phase when created

## Versions

### v2.0.0 (Phase-3) - Current
- **File**: `tdoc-ontology-v2.0.0-phase3.ttl`
- **Date**: 2026-01-19
- **Changes**:
  - Added Decision class hierarchy (Agreement, Conclusion, WorkingAssumption)
  - Added Summary and SessionNotes classes (extending Tdoc)
  - Added Role-related properties (moderatedBy, chairedBy, summaryType, roundNumber)
  - Added Decision properties (hasFFS, hasTBD, hasConsensus, sessionContext)
  - New relationships: MADE_AT, DECISION_BELONGS_TO, MODERATED_BY, CHAIRED_BY

### v1.0.0 (Phase-2) - Baseline
- **File**: `tdoc-ontology-v1.0.0-phase2.ttl`
- **Date**: 2026-01-14
- **Changes**:
  - Initial ontology design (11 classes, 44 properties)
  - Core classes: Tdoc, Meeting, Company, WorkItem, Spec, etc.
  - Basic relationships: SUBMITTED_BY, PRESENTED_AT, REFERENCES, etc.

## Active Version
The active ontology is at `../tdoc-ontology.ttl` (symlink or copy of latest version).
