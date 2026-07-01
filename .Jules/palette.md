
## 2024-05-18 - Auth Form Accessibility
**Learning:** Found custom login/registration form fields missing proper label associations (`htmlFor`/`id`) and `autoComplete` attributes, breaking screen reader experience and frustrating password managers.
**Action:** When creating forms, always pair `<label htmlFor="id">` with `<input id="id">` and include relevant `autoComplete` attributes (especially for sensitive inputs like passwords where `current-password` and `new-password` are essential for UX).
