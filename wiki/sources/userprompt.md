---
type: source
title: "UserPrompt — Test Engineer Implementation Guidance"
tags: [userprompt, guidance, convention]
ingested: 2026-06-21
updated: 2026-06-21
entities: [lun]
concepts: []
---

# UserPrompt — Test Engineer Implementation Guidance

Documents test engineer conventions for filling in implementation details when the TC flow does not specify them. Per conflict Rule 2, UserPrompt always wins over ModelDefault.

## Rules Defined

### Default LUN Selection *(overrides ModelDefault — see [[conflicts]])*

When a TC flow does not specify which LUN to use:

> **LUN = MaxCapacity Enabled LUN**
> 使用最大容量的 Enabled LUN

This overrides ModelDefault's convention of defaulting to LUN index 0 (`TestNormalLun = 0`).

**How to apply:** In Pattern Code, do not hardcode `lun=0`. Instead, query enabled LUNs and select the one with the largest logical block count.

## Where This Fits

Touches: [[lun]]
