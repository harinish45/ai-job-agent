
## 2024-05-14 - Scoping React Query Mutations in Lists
**Learning:** When using a single React Query mutation inside a mapped list of items, the `isLoading` or `isPending` state will apply to *all* items in the list simultaneously, confusing users.
**Action:** Scope the loading and disabled states to the specific item by checking `mutation.variables === item.id`.
