# pulumi-practice

### Learning Pulumi by doing. Mostly Python.

This repo contains infrastructure code for AWS, built with Python-flavored Pulumi. Each subdirectory contains a standalone stack. As an experiment, each of these stacks is a separate release. We'll see if that works, or if not, where it breaks.

## Get ready

I'm assuming you're on Mac or Linux. Windows may work too.

The instructions at [aws-py-webserver](https://github.com/pulumi/examples/tree/master/aws-py-webserver) should get you most of the way there, while walking you thru your first AWS infrastructure deployment.

If you skipped that, here's the full list:

* An AWS account. ([sign up](https://aws.amazon.com/))
* Python v3.6 or later. ([option 1 (recommended)](https://docs.python-guide.org/starting/installation/) or [option 2](https://www.python.org/downloads/))
  * Note: If you go with option one, you can stop after doing the initial install. Since v3.3, Python has shipped with [venv](https://docs.python.org/3/library/venv.html) which is what we'll use to create and manage virtual environments.
* pip3, but note that it should have been included with Python v3.6 or later. Link provided just in case, but chances are good you won't need it. ([install](https://pip.pypa.io/en/stable/installing/))
* A Pulumi account ([sign up](https://app.pulumi.com/welcome))
* The Pulumi CLI ([install](https://pulumi.io/quickstart/))
* AWS credentials ([configure](https://pulumi.io/quickstart/aws/setup.html))
* An SSH key pair ([create](https://help.github.com/en/articles/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent#generating-a-new-ssh-key))

## Get set

The action is in the project subdirectories. Each subdirectory is intended to be self-contained. If you find that's not the case, feel free to open an issue.

Let's use the infrastructure project `vpc-with-ec2` to walk thru the rest of the steps. You'll set up a virtual environment with `venv`, fetch `Pulumi` dependency libraries, then deploy the stack.

### Set up a virtual environment

```bash
➜ cd pulumi-practiceinfrastructure/vpc-with-ec2/

➜ python3 -m venv venv

➜ source venv/bin/activate
```

### Fetch `Pulumi` dependency libraries

Here's everything we just created, including `requirements.txt`.

```bash
➜ ls
Pulumi.dev.yaml  Pulumi.yaml      __main__.py      requirements.txt venv
```

`pip install` is all we need.

```bash
➜ pip install -r requirements.txt
Collecting pulumi>=0.16.4 (from -r requirements.txt (line 1))
  Downloading https://files.pythonhosted.org/packages/bd/60/93682c12996d2aca11081cb88473562d14b860ce0aa820f2de7f7414d2e7/pulumi-0.16.17-py2.py3-none-any.whl (130kB)
    100% |████████████████████████████████| 133kB 1.2MB/s
Collecting pulumi_aws>=0.16.2 (from -r requirements.txt (line 2))
  Using cached https://files.pythonhosted.org/packages/0c/24/fee18eba45725b711cb3566e164a7d77dea6949c28b526c8c91b389151d7/pulumi_aws-0.16.10.tar.gz
Collecting protobuf>=3.6.0 (from pulumi>=0.16.4->-r requirements.txt (line 1))
  Using cached https://files.pythonhosted.org/packages/18/e7/785830a65d1f1faba7dccfa8314f7afded1db8cc2860218226ba4b3f6150/protobuf-3.6.1-cp37-cp37m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl
Collecting grpcio>=1.9.1 (from pulumi>=0.16.4->-r requirements.txt (line 1))
  Using cached https://files.pythonhosted.org/packages/df/33/c0561fe7c5e235325255f46c08bd3d07f2c80824feb22d057328eff1f8b7/grpcio-1.19.0-cp37-cp37m-macosx_10_9_x86_64.whl
Requirement already satisfied: setuptools in ./venv/lib/python3.7/site-packages (from protobuf>=3.6.0->pulumi>=0.16.4->-r requirements.txt (line 1)) (40.6.2)
Collecting six>=1.9 (from protobuf>=3.6.0->pulumi>=0.16.4->-r requirements.txt (line 1))
  Using cached https://files.pythonhosted.org/packages/73/fb/00a976f728d0d1fecfe898238ce23f502a721c0ac0ecfedb80e0d88c64e9/six-1.12.0-py2.py3-none-any.whl
Installing collected packages: six, protobuf, grpcio, pulumi, pulumi-aws
  Running setup.py install for pulumi-aws ... done
Successfully installed grpcio-1.19.0 protobuf-3.6.1 pulumi-0.16.17 pulumi-aws-0.16.10 six-1.12.0
You are using pip version 18.1, however version 19.0.3 is available.
You should consider upgrading via the 'pip install --upgrade pip' command.
```

### Deploy the stack

TODO
