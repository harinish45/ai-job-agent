## 2026-05-09 - Scope Loading States in Lists Properly
**Learning:** When using React Query mutations inside a list of items (like job listings or applications), a single mutation state affects all items if not scoped. This results in all buttons showing loading/disabled states globally across the UI when any single one is clicked.
**Action:** Always scope loading and disabled states to the specific item by checking `mutation.variables === item.id` to provide targeted feedback and prevent unintended global disabled states.
