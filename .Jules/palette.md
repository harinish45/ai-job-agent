## 2024-06-10 - Scope Loading States in Lists
 **Learning:** Using a single `useMutation` in a list component causes all items to show the loading state simultaneously when an action is triggered on any one item. This is confusing and degrades the UX.
 **Action:** Always scope loading and disabled states to the specific item by checking `mutation.variables === item.id` when using `useMutation` inside a list mapping.
