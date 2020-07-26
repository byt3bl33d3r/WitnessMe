# WitnessMe

<p align="center">
  <img src="https://user-images.githubusercontent.com/5151193/60783062-1f637c00-a106-11e9-83de-83ef88115f74.gif" alt="WitnessMe"/>
</p>

WitnessMe is primarily a Web Inventory tool inspired by [Eyewitness](https://github.com/FortyNorthSecurity/EyeWitness), its also written to be extensible allowing you to create custom functionality that can take advantage of the headless browser it drives in the back-end.

WitnessMe uses the [Pyppeteer](https://github.com/pyppeteer/pyppeteer) library to drive Headless Chromium.

## Sponsors
[<img src="https://www.blackhillsinfosec.com/wp-content/uploads/2016/03/BHIS-logo-L-300x300.png" width="130" height="130"/>](https://www.blackhillsinfosec.com/)
[<img src="https://handbook.volkis.com.au/assets/img/Volkis_Logo_Brandpack.svg" width="130" hspace="10"/>](https://volkis.com.au)
[<img src="https://user-images.githubusercontent.com/5151193/85817125-875e0880-b743-11ea-83e9-764cd55a29c5.png" width="200" vspace="21"/>](https://qomplx.com/blog/cyber/)
[<img src="https://user-images.githubusercontent.com/5151193/86521020-9f0f4e00-be21-11ea-9256-836bc28e9d14.png" width="250" hspace="20"/>](https://ledgerops.com)
[<img src="https://user-images.githubusercontent.com/5151193/87607538-ede79e00-c6d3-11ea-9fcf-a32d314eb65e.png" width="170" hspace="20"/>](https://www.guidepointsecurity.com/)

## Table of Contents

- [WitnessMe](#witnessme)
  * [Motivation](#motivation)
  * [Installation](#Installation)
    + [Docker](#docker)
    + [Python Package](#python-package)
    + [Development Install](#development-install)
  * [Quick starts](#quick-starts)
    + [Finding F5 Load Balancers Vulnerable to CVE-2020-5902](#finding-f5-load-balancers-vulnerable-to-cve-2020-5902)
    + [Scraping Javascript Heavy Webpages](#scraping-javascript-heavy-webpages)
  * [RESTful API](#restful-api)
  * [Deploying to the Cloud](#deploying-to-the-cloud-)
    + [GCP Cloud Run](#gcp-cloud-run)
    + [AWS ElasticBeanstalk](#aws-elasticbeanstalk)
  * [Usage and Examples](#usage-and-examples)
    + [Modes of Operation](#modes-of-operation)
      * [Screenshot Mode](#screenshot-mode)
      * [Grab Mode](#grab-mode)
    + [Interacting with the Scan Database](#interacting-with-the-scan-database)
    + [Generating Reports](#generating-reports)
    + [Previewing Screenshots Directly in the Terminal](#preview-screenshots-directly-in-the-terminal)
  * [Creating Signatures](#call-for-signatures)

## Motivation

Are there are a bunch of other tools that do this? Absolutely. See the following projects for alternatives (I'm sure there are more, these are the ones I've personally tried):

- [Eyewitness](https://github.com/FortyNorthSecurity/EyeWitness)
- [GoWitness](https://github.com/sensepost/gowitness)
- [Aquatone](https://github.com/michenriksen/aquatone)

The reason why I wrote WitnessMe was that none of these projects had all of the features I wanted/needed in order for them to work well within my workflow. Additionally, some of them are prone to a decent amount of installation/dependency hell.

Here are some of the main features that make WitnessMe "stand out":

- Written in Python 3.7+
- Ability to parse extremely large Nessus and NMap XML files
- Docker compatible
- No installation/dependency hell
- Full test suite! Everything is less prone to bugs
- CSV & HTML reporting
- Provides a RESTful API! Scan stuff remotely!
- CLI interface to view and search scan results without having to view the reports.
- Signature scanning (Signatures use YAML files)
- Preview screenshots directly in the terminal (On MacOSX/ITerm2 and some Nix terminals)
- Extensibly written, allowing you to add functionality that can take advantage of headless chromium.
- Built to be deployed to the Clouds (e.g. GCP Cloud Run , AWS ElasticBeanstalk etc...)

## Installation

### Docker

Running WitnessMe from a Docker container is fully supported and is the easiest/recommended way of using the tool.

**Note: it is highly recommended to give the Docker container at least 4GB of RAM during large scans as Chromium can be a resource hog. If you keep running into "Page Crash" errors, it's because your container does not have enough memory. On Mac/Windows you can change this by clicking the Docker Task Bar Icon -> Preferences -> Resources. For Linux, refer to Docker's documentation**

Pull the image from Docker Hub:

```console
docker pull byt3bl33d3r/witnessme
```

You can then spin up a docker container, run it like the main `witnessme` script and pass it the same arguments:

```console
docker run --rm -ti $IMAGE_ID screenshot https://google.com 192.168.0.1/24
```

Alternatively, you can drop into a shell within the container and run the tools that way. This also allows you to execute the `wmdb` and `wmapi` scripts.

```console
docker run --rm -ti --entrypoint=/bin/sh $IMAGE_ID
```

### Python Package

WitnessMe is also available as a Python package (Python 3.7 or above is required). If you do install it this way it is extremely recommended to use [pipx](https://github.com/pipxproject/pipx) as it takes care of installing everything in isolated environments for you in a seamless manner.

Run the following commands:

```console
python3 -m pip install --user pipx
pipx install witnessme
```

All of the WitnessMe scripts should now be in your PATH and ready to go.

### Development Install

You really should only install WitnessMe this way if you intend to hack on the source code. You're going to Python 3.7+ and [Poetry](https://python-poetry.org/): please refer to the Poetry installation documentation in order to install it.

```console
git clone https://github.com/byt3bl33d3r/WitnessMe && cd WitnessMe
poetry install
```

## Quick Starts

### Finding F5 Load Balancers Vulnerable to CVE-2020-5902

Install WitnessMe using Docker:

```console
docker pull byt3bl33d3r/witnessme
```

Get the `$IMAGE_ID` from the `docker images` command output, then run the following command to drop into a shell inside the container. Additionally, specify the `-v` flag to mount the current directory inside the container at the path `/transfer` in order to copy the scan results back to your host machine (if so desired):

```console
docker run -it --entrypoint=/bin/sh -v $(pwd):/transfer $IMAGE_ID
```

Scan your network using WitnessMe, it can accept multiple .Nessus files, Nmap XMLs, IP ranges/CIDRs. Example:

```console
witnessme screenshot 10.0.1.0/24 192.168.0.1-20 ~/my_nessus_scan.nessus ~/my_nmap_scan.xml
```

After the scan is finished, a folder will have been created in the current directory with the results. Access the results using the `wmdb` command line utility:

```console
wmdb scan_2020_$TIME/
```

To quickly identify F5 load balancers, first perform a signature scan using the `scan` command. Then search for "BIG-IP" or "F5" using the `servers` command (this will search for the "BIG-IP" and "F5" string in the signature name, page title and server header):

![image](https://user-images.githubusercontent.com/5151193/86619581-43fc6900-bf91-11ea-9a01-ba8ce09c3f3b.png)

Additionally, you can generate an HTML or CSV report using the following commands:
```console
WMDB ≫ generate_report html
```
```console
WMDB ≫ generate_report csv
```

You can then copy the entire scan folder which will contain all of the reports and results to your host machine by copying it to the `/transfer` folder.

### Scraping Javascript Heavy Webpages

As of v1.5.0, WitnessMe has a `grab` command which allows you to quickly scrape Javascript heavy webpages by rendering the page first with Headless Chromium and then parsing the resulting HTML using the specified XPath (see [here](https://devhints.io/xpath) for an XPath cheatsheet).

Below are a few examples to get your started.

This grabs a list of all advertised domains on the `144.161.160.0/23` subnet from [Hurricane Electric's BGP Toolkit](https://bgp.he.net/):
```console
witnessme -d grab -x '//div[@id="dns"]/table//tr/td[2]/a/text()' https://bgp.he.net/net/144.161.160.0/23#_dns
```

## RESTful API

As of version 1.0, WitnessMe has a RESTful API which allows you to interact with the tool remotely.

**Note: Currently, the API does not implement any authentication mechanisms. Make sure to allow/deny access at the transport level**

To start the RESTful API for testing/development purposes run :
```console
wmapi
```

The API documentation will then be available at http://127.0.0.1:8000/docs

[Uvicorn](https://www.uvicorn.org/) should be used to enable SSL and run the API in production. See [this dockerfile](https://github.com/byt3bl33d3r/WitnessMe/blob/master/dockerfiles/Dockerfile.selfhosted) for an example.

## Deploying to the Cloud (™)

Since WitnessMe has a RESTful API now, you can deploy it to the magical cloud and perform scanning from there. This would have a number of benefits, including giving you a fresh external IP on every scan (More OPSEC safe when assessing attack surface on Red Teams).

There are a number of ways of doing this, you can obviously do it the traditional way (e.g. spin up a machine, install docker etc..).

Recently cloud service providers started offering ways of running Docker containers directly in a fully managed environment. Think of it as serverless functions (e.g. AWS Lambdas) only with Docker containers.

This would technically allow you to really quickly deploy and run WitnessMe (or really anything in a Docker container) without having to worry about underlying infrastructure and removes a lot of the security concerns that come with that.

Below are some of the ones I've tried along with the steps necessary to get it going and any issues I encountered.

### GCP Cloud Run

**Unfortunately, it seems like Cloud Run doesn't allow outbound internet access to containers, if anybody knows of a way to get around this please get in touch**

Cloud Run is by far the easiest of these services to work with.

This repository includes the `cloudbuild.yaml` file necessary to get this setup and running.

From the repositories root folder (after you authenticated and setup a project), these two commands will automatically build the Docker image, publish it to the Gcloud Container Registry and deploy a working container to Cloud Run:

```bash
gcloud builds submit --config cloudbuild.yaml
gcloud run deploy --image gcr.io/$PROJECT_ID/witnessme --platform managed
```

The output will give you a HTTPS url to invoke the WitnessMe RESTful API from :)

When you're done:

```bash
gcloud run services delete witnessme
gcloud container images delete gcr.io/$PROJECT_ID/witnessme
```

### AWS ElasticBeanstalk

TO DO

## Usage

There are 3 main utilities:

- `witnessme`: is the main CLI interface.
- `wmdb`: allows you to browse the database (created on each scan) to view results and generate reports.
- `wmapi`: provides a RESTful API to schedule, start, stop and monitor scans.

### Modes of Operations

As of v1.5.0 there are two main modes (commands) that the `witnessme` utility Supports:

- The `screenshot` command, you guessed it, screenshots webpages. This is the main functionality.
- The `grab` command allows you to scrape pages and quickly grab server headers.

```
usage: witnessme [-h] [--threads THREADS] [--timeout TIMEOUT] [-d] [-v] {screenshot,grab} ...

WitnessMe!

positional arguments:
  {screenshot,grab}

optional arguments:
  -h, --help         show this help message and exit
  --threads THREADS  Number of concurrent browser tab(s) to open
                     [WARNING: This can cause huge RAM consumption if set to high values] (default: 15)
  --timeout TIMEOUT  Timeout for each connection attempt in seconds (default: 15)
  -d, --debug        Enable debug output (default: False)
  -v, --version      show program's version number and exit
```

#### Screenshot Mode

```console
$ witnessme screenshot --help
usage: witnessme screenshot [-h] [-p PORTS [PORTS ...]] target [target ...]

positional arguments:
  target                The target IP(s), range(s), CIDR(s) or hostname(s), NMap XML file(s), .Nessus file(s)

optional arguments:
  -h, --help            show this help message and exit
  -p PORTS [PORTS ...], --ports PORTS [PORTS ...]
                        Ports to scan if IP Range/CIDR is provided
```

Can accept a mix of .Nessus file(s), Nmap XML file(s), files containing URLs and/or IPs, IP addresses/ranges/CIDRs and URLs or alternatively read from stdin.

*Note: WitnessMe detects .Nessus and NMap files by their extension so make sure Nessus files have a `.nessus` extension and NMap scans have a `.xml` extension*

Long story short, should be able to handle anything you throw at it:

```console
witnessme screenshot 192.168.1.0/24 192.168.1.10-20 https://bing.com ~/my_nessus_scan.nessus ~/my_nmap_scan.xml ~/myfilewithURLSandIPs
```

```console
$ cat my_domain_list.txt | witnessme screenshot -
```

If an IP address/range/CIDR is specified as a target, WitnessMe will attempt to screenshot HTTP & HTTPS pages on ports 80, 8080, 443, 8443 by default. This is customizable with the `--port` argument.

Once a scan is completed, a folder with all the screenshots and a database will be in the current directory, point `wmdb` to the folder in order to see the results.

```console
wmdb scan_2019_11_05_021237/
```
#### Grab Mode

```console
$ witnessme grab --help
usage: witnessme grab [-h] [-x XPATH | -l] target [target ...]

positional arguments:
  target                The target IP(s), range(s), CIDR(s) or hostname(s), NMap XML file(s), .Nessus file(s)

optional arguments:
  -h, --help            show this help message and exit
  -x XPATH, --xpath XPATH
                        XPath to use
  -l, --links           Get all links
```

The `grab` subcommand allows you to render Javascript heavy webpages and scrape their content using XPaths. See this [section](#scraping-javascript-heavy-webpages) for some examples.

### Interacting with the Scan Database

Once a scan is completed (using the `screenshot` mode), a folder with all the screenshots and a database will be in the current directory, point `wmdb` to the folder in order to see the results.

```console
wmdb scan_2019_11_05_021237/
```
This will drop you into the WMDB CLI menu.

Pressing tab will show you the available commands and a help menu:

<p align="center">
  <img src="https://user-images.githubusercontent.com/5151193/88490790-725bdb80-cf74-11ea-8ecd-1300cf1ad534.png" alt="Tab "/>
</p>

The `servers` and `hosts` commands in the `wmdb` CLI accept 1 argument. WMCLI is smart enough to know what you're trying to do with that argument

#### Server Command

No arguments will show all discovered servers. Passing it an argument will search the `title` and `server` columns for that pattern (it's case insensitive).

For example if you wanted to search for all discovered Apache Tomcat servers:
- `servers tomcat` or `servers 'apache tomcat'`

Similarly if you wanted to find servers with a 'login' in the title:
- `servers login`

#### Hosts Command

No arguments will show all discovered hosts. Passing it an argument will search the `IP` and `Hostname` columns for that pattern (it's case insensitive). If the value corresponds to a Host ID it will show you the host information and all of the servers discovered on that host which is extremely useful for reporting purposes and/or when targeting specific hosts.

#### Signature Scan

You can perform a signature scan on all discovered services using the `scan` command.

### Generating Reports

You can use the `generate_report` command in the `wmdb` cli to generate reports in HTML or CSV format. To generate a HTML report simply run `generate_report` without any arguments. Here's an example of what it'll look like:

![image](https://user-images.githubusercontent.com/5151193/86676611-2c44d500-bfd1-11ea-87fd-faf874a2dcf2.png)

To generate a CSV report:

```console
WMDB ≫ generate_report csv
```

The reports will then be available in the scan folder.

### Preview Screenshots Directly in the Terminal

**Note: this feature will only work if you're on MacOSX and using ITerm2**

You can preview screenshots directly in the terminal using the `show` command:

<p align="center">
  <img src="https://user-images.githubusercontent.com/5151193/68194496-5e012a00-ff72-11e9-9ccd-6a50aa384f3e.png" alt="ScreenPreview"/>
</p>

## Writing Signatures

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