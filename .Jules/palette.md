## 2024-05-15 - Scope Global Mutation Loading States in Lists
**Learning:** Using global `mutation.isPending` for actions inside a list incorrectly triggers the loading state for *all* items in the list, creating a confusing user experience.
**Action:** Always scope loading and disabled states to the specific item using `mutation.variables === item.id` when using React Query mutations inside a list mapping.
