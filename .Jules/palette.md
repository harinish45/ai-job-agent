## 2026-06-01 - Scope Loading States in Lists
**Learning:** When using React Query mutations inside a list of items, relying on `mutation.isPending` will cause all items in the list to show a loading/disabled state simultaneously.
**Action:** Always scope loading and disabled states to the specific item by checking `mutation.variables === item.id`.
