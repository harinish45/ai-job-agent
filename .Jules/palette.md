## 2024-07-03 - Dropdown Menu Keyboard Accessibility
**Learning:** In the ApplicationTracker component, the status update dropdown relies purely on CSS `:hover` state (`group-hover:block`) to be visible. This makes the actions completely inaccessible to keyboard users, as the inner buttons cannot be reached or seen when focusing the trigger button.
**Action:** Adding `group-focus-within:block` alongside `group-hover:block` makes the menu visible when the trigger button or any of its children receive keyboard focus, ensuring full accessibility.
