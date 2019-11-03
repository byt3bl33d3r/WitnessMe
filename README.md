# WitnessMe

<p align="center">
  <img src="https://user-images.githubusercontent.com/5151193/60783062-1f637c00-a106-11e9-83de-83ef88115f74.gif" alt="WitnessMe"/>
</p>

Barebones re-implementation of [Eyewitness](https://github.com/FortyNorthSecurity/EyeWitness) in Python 3.7 that uses Asyncio and [Pyppeteer](https://github.com/miyakogi/pyppeteer) (headless chrome/chromium).

Depending on how mature this project gets, I might submit this as a PR to the original Eyewitness repository in order to update the project.

## Why & what problems does this solve

- Python >= 3.7
- No dependency/installation hell (currently uses only 2 third party packages)
- Asyncio provides Mad Max level speeds
- Headless chrome/chromium is just straight up gangsta

## Usage & Examples

```bash
usage: witnessme.py [-h] [-p PORTS [PORTS ...]] [--threads THREADS]
                    target [target ...]

positional arguments:
  target                The target IP(s), range(s), CIDR(s) or hostname(s)

optional arguments:
  -h, --help            show this help message and exit
  -p PORTS [PORTS ...], --ports PORTS [PORTS ...]
                        Ports (default: [80, 8080, 443, 8443])
  --threads THREADS     Number of concurrent threads (default: 25)
```

- Scan an entire subnet and take a screenshot of every HTTP & HTTPS webpage:

```bash
python witnessme.py 192.168.1.0/24
```

## To Do

1. ~~Store server info to a database~~
2. HTML report generation
3. Cmdline script to search database
4. Support NMap & .nessus files as input
5. Web server categorization & signature support
6. Accept URLs as targets (cmdline and files)
