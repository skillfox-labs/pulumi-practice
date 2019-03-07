# README for branch front-rail-back-rail-refactor

As the name suggests, the branch is derived from the previous branch
`front-rail-back-rail`, with a focus on refactoring the work so far. Currently
all the configuration code sits in a single file (`__main__.py`), and it's
getting unweildy. Time to break things out into Python modules.

Edit: I don't see a logical way to break this up. It's not like I'm creating
modules. The stuff I'm doing uses existing modules. There may be a way to do
it, (sure hope I think of something,) but right now it's a distraction. Back to
adding infra features.
