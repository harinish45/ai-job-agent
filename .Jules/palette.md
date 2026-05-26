## 2024-05-26 - Scoped Mutation Loading States in List Views
**Learning:** When using global React Query mutations (like `useMutation`) inside a mapping of items (such as a job list), relying solely on `mutation.isPending` will cause all items in the list to show a loading state or become disabled simultaneously when any single item triggers the mutation.
**Action:** Always scope loading and disabled states to the specific item being interacted with by checking `mutation.isPending && mutation.variables === item.id` to provide accurate, isolated feedback for only the interacted element.
