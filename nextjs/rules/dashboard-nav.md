## Dashboard pages ↔ user dropdown (every Next.js project with a dashboard)

Trevor 2026-11-10: any page added to an admin (or employee) dashboard's side nav must also appear in
the logged-in user dropdown menu, with the same label, icon and order. Removing or renaming one does the same
to the other. Applies to every Next.js project (under `~/Developer/repos/nextjs/`) with a dashboard and a database; widen it when another stack gets a dashboard.

- **One list, two menus.** The side nav and the dropdown both render from one shared nav config
  (label, icon, view/href, sub-items, roles). Never hardcode the items twice. If a project still has two
  hardcoded lists, the first job that touches either one moves them to the shared config.
- **Role-gated pages** stay gated in both menus (an admin-only page never shows in the employee dropdown).
- **Specs and reviews check it.** A spec that adds, removes or renames a dashboard page lists the dropdown
  as a touched file; a code/UI review fails the round if the two menus don't match.
