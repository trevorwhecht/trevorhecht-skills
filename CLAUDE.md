# trevorhecht-skills

## Git
- The main checkout stays on `main`; scrum jobs branch from `origin/main` and squash-merge their PRs into `main`.
- An edit made in this checkout from a chat is finished in that same chat: commit and push `main`
  (`/trevskills-commitpush`). Never end a chat with uncommitted edits here; every scrum Merge refuses to run while the
  checkout is dirty. Not finishing it now? Put it on the scrum backlog and leave the files alone.
- Never `git reset`, `git rebase` or force-push.
