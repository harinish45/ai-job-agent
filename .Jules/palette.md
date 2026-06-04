## 2024-06-04 - Fix global loading states in lists
**Learning:** When using React Query mutations inside a list of items (e.g., job items), `mutation.isPending` is a global state. Clicking an action on one item triggers loading and disabled states for all items in the list.
**Action:** Always scope loading and disabled states to the specific item by checking `mutation.variables === item.id` to avoid triggering global loading indicators across all list items.
