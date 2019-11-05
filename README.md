# WitnessMe

<p align="center">
  <img src="https://user-images.githubusercontent.com/5151193/60783062-1f637c00-a106-11e9-83de-83ef88115f74.gif" alt="WitnessMe"/>
</p>

My take on a Web Inventory tool, heavily inspired by [Eyewitness](https://github.com/FortyNorthSecurity/EyeWitness). Takes screenshots of webpages using [Pyppeteer](https://github.com/miyakogi/pyppeteer) (headless Chrome/Chromium).

Supports Python >= 3.7, uses Asyncio and has some extra bells & whistles that makes life easier.

## Why & what problems does this solve

- Python >= 3.7
- No dependency/installation hell, works on a variety of *nix flavors
- Asyncio provides Mad Max level speeds
- Headless chrome/chromium is just straight up gangsta

## Installation

```bash
git clone https://github.com/byt3bl33d3r/WitnessMe && cd WitnessMe
pip3 install --user pipenv && pipenv install --three
pipenv shell # Enter the virtualenv
```

## Usage & Examples

`witnessme.py` is what takes the screenshots, `wmdb.py` allows you to browse the database created on each scan.

```
usage: witnessme.py [-h] [-p PORTS [PORTS ...]] [--threads THREADS]
                    [--timeout TIMEOUT]
                    target [target ...]

positional arguments:
  target                The target IP(s), range(s), CIDR(s) or hostname(s)

optional arguments:
  -h, --help            show this help message and exit
  -p PORTS [PORTS ...], --ports PORTS [PORTS ...]
                        Ports to scan if IP Range/CIDR is provided (default:
                        [80, 8080, 443, 8443])
  --threads THREADS     Number of concurrent threads (default: 25)
  --timeout TIMEOUT     Timeout for each connection attempt in seconds
                        (default: 35)
```

Can accept a mix of .Nessus file(s), Nmap XML file(s) and IP addresses/ranges/CIDRs as targets:

```bash
python witnessme.py 192.168.1.0/24 192.168.1.10-20 ~/my_nessus_scan.nessus ~/my_nmap_scan.xml
```
*Note: as of writing, WitnessMe detects files by their extension so make sure Nessus files have a `.nessus` extension, NMap scans have a `.xml` extension etc..*   

If an IP address/range/CIDR is specified as a target, WitnessMe will attempt to screenshot HTTP & HTTPS pages on ports 80, 8080, 443, 8443 by default. This is customizable with the `--port` argument.

Once a scan is completed, a folder with all the screenshots and a database will be in the current directory, point `wmdb.py` to the database in order to see the results.

```bash
python wmdb.py scan_2019_11_05_021237/witnessme.db
```

Pressing tab will show you the available commands and a help menu:

<p align="center">
  <img src="https://user-images.githubusercontent.com/5151193/68194972-3fe7f980-ff73-11e9-8b63-b75df6e47977.png" alt="ScreenPreview"/>
</p>

## Preview Screenshots Directly in the Terminal (ITerm2 on MacOSX)

If you're using ITerm2 on MacOSX, you can preview screenshots directly in the terminal using the `show` command:

<p align="center">
  <img src="https://user-images.githubusercontent.com/5151193/68194496-5e012a00-ff72-11e9-9ccd-6a50aa384f3e.png" alt="ScreenPreview"/>
</p>


## To Do

1. ~~Store server info to a database~~
2. HTML report generation
3. ~~Cmdline script to search database~~
4. Support NMap & .nessus files as input *(Almost there, still some bugs but usable)*
5. Web server categorization & signature support
6. Accept URLs as targets (cmdline, files, stdin) *(Accepts files)*
