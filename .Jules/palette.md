## 2024-04-26 - Scoped Mutation Loading States in Lists

**Learning:** When using React Query mutations inside a list of items (like a job list), using a single global `isPending` state causes all buttons in the list to show a loading state when only one item is being processed. This is confusing and bad UX.
**Action:** Always scope the disabled and loading state logic to the specific item by checking `mutation.isPending && mutation.variables === item.id` to ensure only the interacted item shows the loading state.
