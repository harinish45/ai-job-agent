## 2024-04-26 - Keyboard Accessible Hover Menus
**Learning:** Tailwind `group-hover:block` completely breaks keyboard navigation for dropdown menus because keyboard users cannot trigger hover states to make elements visible and focusable.
**Action:** Always pair `group-hover:block` with `group-focus-within:block` so that moving focus to the menu trigger naturally opens the menu and allows users to tab into its contents. Ensure focusable elements receive visible focus rings (`focus-visible:ring-2`).
