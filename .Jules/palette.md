## 2024-05-30 - Prevent Global Loading States in Lists
**Learning:** When using React Query mutations inside a list of items (e.g., job lists), a simple `mutation.isPending` check will trigger loading states on *all* items simultaneously, leading to confusing UI and visual noise.
**Action:** Always scope loading and disabled states to the specific item being interacted with by checking `mutation.variables === item.id` (e.g., `matchMutation.isPending && matchMutation.variables === job.id`).
