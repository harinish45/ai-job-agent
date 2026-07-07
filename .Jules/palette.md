## 2024-07-08 - Accessible CSS-only Dropdowns
**Learning:** CSS-only dropdowns that use `group-hover:block` for mouse interactions are completely hidden from keyboard users because they can't be tabbed into or toggled without a click.
**Action:** Always pair `group-hover:block` with `group-focus-within:block` so the dropdown opens when the trigger button or any item inside it receives focus. Ensure proper ARIA roles (`role="menu"`, `role="menuitem"`, `aria-haspopup="menu"`) and visible focus states (`focus-visible:ring-2`) are also included for screen readers.
