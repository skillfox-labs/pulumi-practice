# pulumi-practice

### Learning Pulumi by doing. Mostly Python.

This repo contains infrastructure code for AWS, with Python-flavored Pulumi. Each subdirectory contains a standalone stack. As an experiment, each of these stacks is a separate release. We'll see if that works, or if not, where it breaks.

## Get ready

I'm assuming you're on Mac or Linux. Windows may work too.

These instructions [aws-py-webserver](https://github.com/pulumi/examples/tree/master/aws-py-webserver) should get you most of what's needed, while walking you thru your first AWS infrastructure deployment.

If you skipped that, here's the full list:

* An AWS account. ([sign up](https://aws.amazon.com/))
* Python v3.6 or later. ([option 1](https://docs.python-guide.org/starting/installation/) or [option 2](https://www.python.org/downloads/))
  * Note: If you use the first link, you can stop after doing the initial install. Since v3.3, Python has shipped with [venv](https://docs.python.org/3/library/venv.html) which we'll use (KISS).
* pip3, which should be included with Python v3.6 or later. ([install](https://pip.pypa.io/en/stable/installing/))
* A Pulumi account ([sign up](https://app.pulumi.com/welcome))
* The Pulumi CLI ([install](https://pulumi.io/quickstart/))
* AWS credentials ([setup](https://pulumi.io/quickstart/aws/setup.html))
* An SSH key pair ([create](https://help.github.com/en/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#generating-a-new-ssh-key))
  * Please don't use an AWS-generated key pair. It'll be a base64 encoded blob that I believe includes the public and private keys. You won't be able to commit the public key to your `pulumi` config. More precisely, you _can_, but you _really_ don't want to.

## Get set

