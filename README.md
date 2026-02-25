# HTCondor Noun Verb Demo

This repository contains a demonstration of Andrew's proposal for the development of the noun verb CLI for HTCondor.

If you don't know what that means, this repository is probably not intended for you.

Written using Python 3.9, but should be compatible with later versions.

## Interactive demo

This repository contains a Python package that can be used to simulate the use of the proposed commands.

### Installation 

**pip**

```bash
python3 -m pip install git+https://github.com/aowen-uwmad/htcondor-noun-verb-demo.git
```

**pipx**

```bash
pipx install git+https://github.com/aowen-uwmad/htcondor-noun-verb-demo.git
```

**hatch**

```bash
git clone https://github.com/aowen-uwmad/htcondor-noun-verb-demo.git
hatch shell
```

### Interaction

Once installed, run

```
htcondor --help
```

to get started. 

> [!WARNING]
> If you install this on an HTCondor access point, this may interfere with the actual `htcondor` CLI!!

## End-to-end mockup

To see how the commands would work for an end-to-end HTCondor workflow, see [mockup.md](/mockup.md).

