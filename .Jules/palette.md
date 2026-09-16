## 2024-05-15 - Scope loading states for list items
**Learning:** When using React Query mutations inside a list of items, using the global mutation `isPending` state will cause all items in the list to show a loading state when only one is clicked.
**Action:** Always scope loading and disabled states to the specific list item by checking `mutation.variables === item.id` to avoid triggering global loading indicators across all list items.
