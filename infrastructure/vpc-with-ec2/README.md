# VPC with EC2

## Setting up a Python virtual environment

Get where you want to work

<!-- tokenize? -->

> ➜  cd infrastructure/vpc-with-ec2/

<!-- pip install -r requirements.txt ? -->

Create the virtual environment

> ➜  python3 -m venv venv

Then activate it

> ➜  source venv/bin/activate

Deactivating is simple too

> ➜  deactivate

## Configuring Pulumi

You may want to set some persistent configurations. For instance, if you wanted to use a named profile called `work` in `~/.aws/credentials`, e.g.,

    [default]
    aws_access_key_id = AKIAOOWEICOSHEPHIXEN
    aws_secret_access_key = LtmchHzBvLGOFhTY8+Ke7baRO9LcnABbvli4ebAV

    [work]
    aws_access_key_id = AKIANOTHINGTOSEEHERE
    aws_secret_access_key = ChoOV7dee7zie4eEch+I+kai\p/at_OoUeSoochE

<!-- tokenize? -->

Add the profile to `Pulumi.<stack>.yaml` with

> ➜  pulumi config aws:profile work

## Spinning up the stack

Create it

> ➜  pulumi up

Inspect it

> ➜  pulumi stack

Tear it down

> ➜  pulumi destroy
