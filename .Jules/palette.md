## 2024-05-16 - Scoped Loading States in Lists
**Learning:** When using React Query mutations inside a list of items, using generic `mutation.isPending` causes a global loading state, confusingly disabling or showing spinners on *all* list items instead of just the interacted one.
**Action:** Always scope loading and disabled states to the specific item by checking `mutation.variables === item.id` to provide precise, localized UX feedback.
