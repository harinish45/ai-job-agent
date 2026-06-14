## 2024-05-24 - Scoped Loading States in Lists
**Learning:** When using React Query mutations inside a list of items, global isPending states disable all buttons in the list. This creates a confusing experience where users think the whole app is blocked.
**Action:** Always scope loading and disabled states to the specific item by checking mutation.variables === item.id.
