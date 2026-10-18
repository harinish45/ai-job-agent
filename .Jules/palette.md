## 2024-05-01 - List Item Loading States
**Learning:** In lists where each item triggers a `useMutation`, using `mutation.isPending` without checking `mutation.variables` causes all items in the list to appear in a loading state simultaneously.
**Action:** Always check `mutation.variables === item.id` to isolate the loading state to the specific item being acted upon.
