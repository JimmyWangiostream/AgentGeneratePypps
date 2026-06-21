---
type: source
title: "CustomerReq — Customer-Specific Requirements"
tags: [customerreq, requirements, constraint]
ingested: 2026-06-21
updated: 2026-06-21
entities: [write-booster, lun]
concepts: []
---

# CustomerReq — Customer-Specific Requirements

Customer-defined behavioral rules that override Spec defaults when there is a conflict. Per conflict Rule 1, CustomerReq always wins over Spec.

## Rules Defined

### WriteBooster LUN Constraint *(overrides Spec — see [[conflicts]])*

When setting WriteBooster-related Attributes or Flags:

- LUN **must** be a Normal LUN
- LUN **must not** be a Boot LUN
- LUN index **must** be in range 0~7

If any condition is violated, device shall respond with **`invalid INDEX`**.

This overrides the Spec, which does not impose these restrictions at the attribute-write level.

## Where This Fits

Touches: [[write-booster]], [[lun]]
