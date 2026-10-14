## 2024-05-19 - Scope React Query Mutations in Lists
**Learning:** When using React Query mutations inside a list of items (e.g., job lists), checking `mutation.isPending` causes a global loading state that visually disables all items and creates confusing feedback for the user.
**Action:** Always scope loading and disabled states to the specific item by checking `mutation.variables === item.id` to avoid triggering global loading indicators across all list items.
