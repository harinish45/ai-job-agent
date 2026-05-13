## 2024-05-13 - Scope React Query Loading States in Lists
**Learning:** When using React Query mutations inside a list of items (e.g., job lists), a global `mutation.isPending` check will incorrectly trigger the loading/disabled state for every button in the list simultaneously, confusing users.
**Action:** Always scope loading and disabled states to the specific item being interacted with by checking `mutation.variables === item.id` (e.g., `disabled={mutation.isPending && mutation.variables === job.id}`).
