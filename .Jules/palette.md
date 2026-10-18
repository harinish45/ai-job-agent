## 2024-06-11 - Scoping React Query Mutations in Lists
**Learning:** When using React Query mutations inside a list of items (like a job list), using a global `mutation.isPending` will cause all items in the list to show a loading state when any single item is clicked. This creates a confusing user experience where actions on one item appear to affect all others.
**Action:** Always scope loading and disabled states to the specific item being interacted with by checking `mutation.variables === item.id` (e.g., `disabled={mutation.isPending && mutation.variables === item.id}`).
