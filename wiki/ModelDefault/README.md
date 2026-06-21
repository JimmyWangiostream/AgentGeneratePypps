# ModelDefault — Command Parameter Defaults

When a TC flow lacks specific details, use these model-generated default values derived from analyzing `Spec/` and `Script/`.

## Priority

**ModelDefault is used ONLY when:**
1. TC flow doesn't specify a detail
2. UserPrompt/ doesn't specify an alternative

If both are silent → use ModelDefault
If UserPrompt specifies → use UserPrompt instead

## Directory Structure

- **`data_operations.md`** — Default parameters for read/write operations
- **`initialization.md`** — Default device initialization parameters  
- **`power_management.md`** — Default power cycle and reset parameters
- **`hardware_settings.md`** — Default hardware settings and configurations
- **`descriptor_operations.md`** — Default attribute/flag/descriptor operations
- **`vendor_commands.md`** — Default vendor command parameters
- **`error_handling.md`** — Default error detection and recovery behavior

## How to Use

When implementing a TC flow step that lacks detail:
1. Check if **UserPrompt/** has guidance → use it
2. Otherwise, find the relevant category above
3. Apply the default values specified

All defaults are based on:
- Common patterns observed in existing Pattern Code (`Script/`)
- UFS specification best practices (`Spec/`)
- Device capabilities and constraints

