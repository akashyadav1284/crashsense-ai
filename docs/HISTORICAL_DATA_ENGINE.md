# CRASHSENSE AI - Historical Data Engine Specification

## 1. System Objective
The Historical Data Engine guarantees that empirical datasets used for statistical research and model calibration are isolated, validated, non-fabricated, and deduplicated.

### Isolation Matrix
Datasets are strictly isolated along 4 dimensions:
1. `platform_id`: (e.g. `1xbet`, `bcgame`, `spribe`, `historical_import`)
2. `provider_id`: (e.g. `spribe`, `bc_originals`, `inhouse`)
3. `game_id`: (e.g. `aviator`, `crash`, `spaceman`)
4. `room_id`: (e.g. `standard`, `highroller`, `vip`)

Unrelated operator and provider datasets are never automatically merged or co-mingled.

---

## 2. Validation Engine Rules
- **Non-positive Multipliers**: Strict schema rejection for multipliers $\le 0.00$.
- **NaN / Infinity Filter**: Floats must be finite numbers.
- **Future Timestamps**: Records reporting timestamps $> \text{UTC Now}$ trigger warnings and quality score penalties.
- **Deduplication Key**: Compound primary key prevents identical round insertion.
- **Provably Fair Seed Lineage**: Preserved in raw `provenance` metadata.
