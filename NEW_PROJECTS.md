# Adding new (Pulumi) projects

Each subdirectory is intended to hold a single self-contained Pulumi project. It's a learning exercise.

## The last project

* Get the last project to a good stopping point before moving on
    * `pulumi destroy` the current stack if needed
    * commit any added files
        * !! be sure the stack still builds
    * push them to their branch on the remote
    * open PR if appropriate
    * `deactivate` the virtual environment

## The next project

* Make a new subdirectory wherever appropriate. Currently all should be directly under `pulumi-practice/infrastructure`
* Inside the new project subdirectory, do these steps in order
    * `pulumi new aws-python`
        * The project name offered will be the subdirectory name. Take it.
        * The stack name offered will be `dev`. Take it.
        * set the default region to `us-west-2`
        * NB: Pulumi will complain about a non-empty subdirectory if you create the virtual environment first.
    * `python3 -m venv venv`
    * `source venv/bin/activate`
    * Consider running `pulumi up` before going on.
        * It'll create a stack and a bucket.
        * Don't forget `pulumi destroy`
    * `git checkout -b ${subdirectory-name}`
    * `git add .gitignore Pulumi.dev.yaml Pulumi.yaml __main__.py requirements.txt`
        * Or whatever is the current set of generated files at the time.
        * Commit the generated files before making changes.
    * `git commit -m "Add Pulumi Python project ${project-name}"`
        * Swap in `${project-name}`
        * Consider using `git commit` and adding some color to the commit.

    ```text
    Add Pulumi Python project front-rail-back-rail

    This will build on vpc-with-ec2 to add a private subnet behind a NAT
    gateway. May add autoscaling to instances in both subnets.
    ```

    * `pip install -r requirements.txt`
    * `git push [-u] origin ${project-name}`
    * Consider copying the `__main__.py` or other source files from another project subdirectory.
        * If so, commit it before editing. Use a commit message like this.

    ```text
    Copy front-rail-back-rail/__main__.py
    ```

## Keep in mind

If uncommitted changes are present at the time of a `pulumi update`, there will
be a warning on the status page. All else being equal, it's good practice to
resolve uncommitted changes before making infrastructure changes. But all
things are not equal. So think about how to lower the barrier to practicing
this good repo hygiene.

## Snafus

New work may depend on the most recent work, which is not yet merged to
`master`. Just pointing it out, don't have a suggestion yet.

## "Out of band" edits

Sometimes there's an "out of band" or repo edit, like adding this file for
example. It's out of band in the sense that it's outside of the project
subdirectory, so part of the larger repo. For a minute there I thought of
maintaining a long-running `OOB` branch. That seems wrong. Long-lived branches
in general can become problematic in that they add overhead.

Instead, this repo follows [GitHub
Flow](https://guides.github.com/introduction/flow/), which says either create a
separate short-lived branch, or include the change in another short-lived
branch. All changes will get to `master` soon either way, and all future
branches will derive from `master`. Simple.
