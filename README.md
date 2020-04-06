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

## Call for Signatures!

If you run into a new webapp write a signature for it! It's beyond simple and they're all in YAML!

Don't believe me? Here's the AirOS signature (you can find them all in the [signatures directory](https://github.com/byt3bl33d3r/WitnessMe/tree/master/witnessme/signatures)):

```yaml
credentials:
- password: ubnt
  username: ubnt
name: AirOS
signatures:
- airos_logo.png
- form enctype="multipart/form-data" id="loginform" method="post"
- align="center" class="loginsubtable"
- function onLangChange()
# AirOS ubnt/ubnt
```

Yup that's it. Just plop it in the signatures folder and POW! Done.

## Usage & Examples

`witnessme.py` is what takes the screenshots, `wmcli.py` allows you to browse the database created on each scan.

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

Can accept a mix of .Nessus file(s), Nmap XML file(s), files containing URLs and/or IPs, IP addresses/ranges/CIDRs and URLs. Long story short, should be able to handle anything you throw at it:

```bash
python witnessme.py 192.168.1.0/24 192.168.1.10-20 https://bing.com ~/my_nessus_scan.nessus ~/my_nmap_scan.xml ~/myfilewithURLSandIPs
```

*Note: as of writing, WitnessMe detects .Nessus and NMap files by their extension so make sure Nessus files have a `.nessus` extension and NMap scans have a `.xml` extension*

If an IP address/range/CIDR is specified as a target, WitnessMe will attempt to screenshot HTTP & HTTPS pages on ports 80, 8080, 443, 8443 by default. This is customizable with the `--port` argument.

Once a scan is completed, a folder with all the screenshots and a database will be in the current directory, point `wmcli.py` to the database in order to see the results.

```bash
python wmcli.py scan_2019_11_05_021237/witnessme.db
```

Pressing tab will show you the available commands and a help menu:

<p align="center">
  <img width="534" src="https://user-images.githubusercontent.com/5151193/68552696-11d14200-03d7-11ea-828f-3c744e58df86.png" alt="ScreenPreview"/>
</p>

## Searching the Database

The `servers` and `hosts` commands in the `wmcli.py` CLI accept 1 argument. WMCLI is smart enough to know what you're trying to do with that argument

### Server Command

No arguments will show all discovered servers. Passing it an argument will search the `title` and `server` columns for that pattern (it's case insensitive).

For example if you wanted to search for all discovered Apache Tomcat servers:
- `servers tomcat` or `servers 'apache tomcat'`

Similarly if you wanted to find servers with a 'login' in the title:
- `servers login`

### Hosts Command

No arguments will show all discovered hosts. Passing it an argument will search the `IP` and `Hostname` columns for that pattern (it's case insensitive). If the value corresponds to a Host ID it will show you the host information and all of the servers discovered on that host which is extremely useful for reporting purposes and/or when targeting specific hosts.

### Signature Scan

You can perform a signature scan on all discovered services using the `scan` command.

# Preview Screenshots Directly in the Terminal (ITerm2 on MacOSX)

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
6. ~~Accept URLs as targets (cmdline, files)~~
7. Add support for previewing screenshots in *nix terminals using w3m
