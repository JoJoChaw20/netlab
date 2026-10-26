# WIC2005 Weeks 1–3

Published pages: [Week 2](https://jojochaw20.github.io/netlab/) ·
[Week 3](https://jojochaw20.github.io/netlab/week3/).
The Weeks 1–2 setup below is preserved; see [Week 3](#week-3-routed-network)
for the routed network, validation and reproduction steps.

This lab builds a dual-stack Mininet network inside a custom Docker image,
`netlab:1.0`. Three Linux bridges form the chain `s1 — s2 — s3`:
`h1/h2` attach to `s1`, `h3/h4` to `s2`, and `h5/h6` to `s3`.
Hosts use `10.19.0.1–6/24` and `fd00:5019::1–6/64`.

The chain is connected and has no forwarding loop. It makes local and remote
MAC learning easy to compare without adding routing or an SDN controller.
The host-role comments group workstations, practice servers and monitoring
workstations; they do not imply that server applications have been installed.
All hosts share one Ethernet broadcast domain and one subnet per IP version.
`topology.yaml` is the source of truth for both the running network and the
generated documentation, so links and addresses need not be maintained twice.

**GitHub Pages serves the generated documentation only. Mininet runs locally
in Docker; opening the published page does not start a network.**

## Files

| File | Purpose |
| --- | --- |
| `Dockerfile` | Ubuntu 22.04 with Mininet, Linux bridge tools, Python/PyYAML, ping and inspection tools; working directory `/lab`. |
| `topology.yaml` | Three switches, six hosts, dual-stack addresses and eight links. |
| `build_topo.py` | Loads YAML/JSON, checks address blocks, duplicate addresses and link endpoints, then builds Mininet with `LinuxBridge`, no controller and deterministic host MACs. |
| `bad.yaml` | Negative fixture with duplicate IPv4, duplicate IPv6 and an extra link to nonexistent `s9`. Never use as the working topology. |
| `make_page.py` | Uses the same loader/checks, reads answers and saved evidence, and writes `docs/index.html`. Link list and Mermaid diagram come from the topology. |
| `page.yaml` | Repository URL and seven reflection answers. |
| `evidence/check.txt` | Three validation errors from the bad fixture. |
| `evidence/pingall.txt` | Saved IPv4 all-pairs connectivity output. |
| `evidence/neigh.txt` | h1's ARP and IPv6 Neighbour Discovery entries. |
| `evidence/macs.txt` | s1's learned bridge forwarding table. |
| `evidence/dad.txt` | h2's deliberate duplicate IPv6 and IPv4 address observations. |
| `docs/index.html` | Generated static page committed for GitHub Pages. |
| `.gitignore` | Excludes Python bytecode and cache directories. |

## Prerequisites

- Windows PowerShell, Git, an editor and Docker Desktop using Linux containers
  (for example its WSL 2 backend), with the Docker engine running.
- Docker permission to run a privileged lab container and bind-mount this folder.
  Mininet needs Linux network namespaces, virtual interfaces and bridges.
- Internet for the initial image build, GitHub publishing and the Mermaid CDN
  used by the generated page. No host Python installation is required.

## Reproduce locally

Host commands below are **PowerShell**. For a new checkout, open a terminal
in the folder where you want to download the project:

```powershell
git clone https://github.com/JoJoChaw20/netlab.git
cd netlab
```

If you already have a checkout, open a terminal in that `netlab` folder instead.
Inspect the repository and Docker state before continuing:

```powershell
git status --short
git log --oneline
git remote -v
docker ps -a
docker image ls netlab
```

For a fresh setup, follow the Docker build and run commands below. If you
already have a running privileged container named `netlab`, using `netlab:1.0`
and this checkout mounted at `/lab`, reuse it:

```powershell
docker exec -it -w /lab netlab bash
```

If it exists but is stopped, run `docker start netlab` first. For a fresh setup
only, build the image and create the container (do not create a second container
with the same name):

```powershell
docker build -t netlab:1.0 .
docker run -it --name netlab --privileged --mount "type=bind,source=$($PWD.Path),target=/lab" -w /lab netlab:1.0 bash
```

Inside the container, use **Bash**:

```bash
cd /lab
python3 build_topo.py topology.yaml
```

At the **Mininet CLI** prompt:

```text
net
pingall
h1 ping -6 -c 3 fd00:5019::6
exit
```

`exit` stops the network and returns to Bash. Run only one Mininet network in
this container at a time. IPv6 addresses may need a few seconds for normal DAD
to finish before the first ping. `pingall` tests IPv4, not IPv6.

The saved IPv4 evidence reports **0% dropped (30/30 received)**. The previous
interactive IPv6 h1-to-h6 test was reported as 3/3 received, but its transcript
is not among the five saved evidence files, so the page does not present it as
a saved measurement. `neigh.txt` does contain h2's IPv6 neighbour entry on h1.

## Validation without starting a network

Inside the container, these checks inspect data only and do not repeat the
duplicate-address runtime experiment:

```bash
python3 -c "from build_topo import load,check_mine,check; s=load('topology.yaml'); p=check_mine(s)+check(s); print(p); assert not p"
python3 build_topo.py bad.yaml
echo $?
```

The good fixture should print `[]`. The bad fixture should exit with status 1
and report exactly these three problems before creating devices:

```text
PROBLEM: h2 and h1 both use 10.19.0.1
PROBLEM: h2 and h1 both use fd00:5019::1
PROBLEM: Link ['h6', 's9'] refers to unknown node s9
Fix the description and try again.
```

`check()` normalises addresses with `ipaddress.ip_interface(...).ip` so prefix
notation cannot hide a duplicate. It also rejects missing host addresses and
malformed links. `check_mine()` checks the suffix-derived allocation blocks
`10.19.0.0/16` and `fd00:5019::/32`; this topology uses the narrower /24 and /64.
The page generator calls the same checks and refuses a broken topology.

Optional YAML/JSON comparison in Bash, without changing the source YAML:

```bash
python3 -c "import yaml,json; print(json.dumps(yaml.safe_load(open('topology.yaml')),indent=2))" > /tmp/netlab-5019.json
python3 -c "from build_topo import load; assert load('topology.yaml') == load('/tmp/netlab-5019.json'); print('Equivalent data; YAML comments are not preserved')"
```

## Evidence and what it demonstrates

The committed evidence is already collected. Preserve it; there is no need to
repeat the duplicate experiment. `dad.txt` shows `fd00:5019::1` on h2 marked
`dadfailed tentative`, while IPv4 accepts `10.19.0.1` as `secondary`. This is
the observed behaviour of these Linux commands, not a claim that IPv4 systems
can never implement conflict detection. The extra addresses were runtime
changes; the working YAML retains unique addresses.

`macs.txt` maps host MACs ending `01` and `02` to s1 ports 1 and 2, and `03–06`
to port 3 toward s2. `neigh.txt` shows IPv4 neighbours learned through ARP and
h2's IPv6 entries learned through Neighbour Discovery. These are snapshots:
cache states and ageing timers change over time.

For a separate future evidence run, use a fresh output directory so the
originals remain intact. In container Bash, before starting Mininet:

```bash
export EVIDENCE_RUN="/lab/evidence-run-$(date +%Y%m%d-%H%M%S)"
mkdir "$EVIDENCE_RUN"
python3 build_topo.py bad.yaml > "$EVIDENCE_RUN/check.txt" 2>&1
python3 build_topo.py topology.yaml
```

At the Mininet prompt:

```text
pingall
h1 ping -6 -c 3 fd00:5019::6
h1 ping -6 -c 1 fd00:5019::2
h1 ip neigh > "$EVIDENCE_RUN/neigh.txt"
sh brctl showmacs s1 > "$EVIDENCE_RUN/macs.txt"
```

Copy the actual terminal ping output into that run's `pingall.txt`; do not
invent a transcript or replace the committed output merely to refresh it.
Only if intentionally repeating the course DAD demonstration in this separate
run, use these Mininet commands after the connectivity checks:

```text
h2 ip -6 addr add fd00:5019::1/64 dev h2-eth0
h2 ip addr add 10.19.0.1/24 dev h2-eth0
sh sleep 3
h2 ip -6 addr show dev h2-eth0 > "$EVIDENCE_RUN/dad.txt"
h2 ip -4 addr show dev h2-eth0 >> "$EVIDENCE_RUN/dad.txt"
h2 ip -6 addr del fd00:5019::1/64 dev h2-eth0
h2 ip addr del 10.19.0.1/24 dev h2-eth0
exit
```

## Generate and inspect the page

From host PowerShell, using the existing container:

```powershell
docker exec -w /lab netlab bash -lc 'python3 make_page.py topology.yaml'
Start-Process .\docs\index.html
Select-String -Path docs\index.html -Pattern 'TODO|Not answered yet|Missing:|YOUR_USERNAME|YOUR_REPO'
git diff --check
git status --short
```

Generation should emit `Wrote docs/index.html` without missing-evidence or
unanswered-question warnings. Confirm the page has six host rows, eight links,
three switches in its diagram, all five evidence blocks and seven answers.
Check the repository link is the confirmed GitHub repository. Mermaid loads
from an online CDN; an offline browser may show diagram text instead.
Regenerate after edits to the topology, answers, evidence or generator, and
commit the resulting HTML. Pages does not run the Python generator.

## GitHub and Pages

The confirmed repository is [JoJoChaw20/netlab](https://github.com/JoJoChaw20/netlab).
It already exists and was empty when inspected. No remote was configured in
the local checkout at the initial inspection. Use this existing repository.

For a fresh checkout without a remote, use these PowerShell commands:

```powershell
git remote -v
git branch -m main
git remote add origin https://github.com/JoJoChaw20/netlab.git
git ls-remote origin
```

Run the rename only if the current branch is not already `main`, and add
`origin` only if absent. If the remote already contains commits, fetch and
inspect them before integrating; do not force-push or replace existing history.
Update `page.yaml` to the repository's web URL and regenerate the page before
committing. Review exactly what is staged:

```powershell
git diff
git add README.md .gitignore build_topo.py make_page.py page.yaml docs/index.html evidence/check.txt
git diff --cached --stat
git commit -m "Document reproducible lab and generated network page"
git log --oneline
git push -u origin main
```

Keep existing commits and make further commits around meaningful changes.
The initial history already contained five commits; the implemented validator
and corrected `check.txt` were still uncommitted at inspection. The earlier
validation commit saved an `s9` traceback, which remains in history rather than
being rewritten. Subsequent commits record the working validator and evidence.
Use Git Credential Manager's sign-in flow if prompted; do not put access tokens
in source files or remote URLs.

On GitHub: **Settings → Pages → Build and deployment → Deploy from a branch →
main → /docs → Save**. See [GitHub's publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
Wait for the Pages deployment to finish, then open the URL GitHub displays.
Verify the repository link, addresses, diagram, evidence and answers there;
an HTTP success alone does not establish that the latest page is deployed.
The published site is [Network 5019](https://jojochaw20.github.io/netlab/).
Submit the verified **Pages URL**, rather than the repository URL, on Spectrum
yourself. On 20 October 2026, Pages was configured from `main` / `docs`, the
site returned HTTP 200, and its HTML matched the committed generated page
(allowing for Windows/Linux line endings). Check again after future changes.

## Cleanup

At the Mininet prompt, `exit` calls `net.stop()`. If a network was interrupted,
ensure no Mininet session is active before running `mn -c` in container Bash.
That cleanup removes stale Mininet interfaces and bridges, so do not run it
alongside a working network. Leave Bash with `exit`.

To stop this lab container from host PowerShell when finished:

```powershell
docker stop netlab
```

Optional removal of this stopped container and its image, only when no longer
needed:

```powershell
docker rm netlab
docker image rm netlab:1.0
```

These commands leave the bind-mounted project and evidence on the host. Do not
use a global Docker prune or remove other containers to clean up this lab.

## Week 3: routed network

`network.yaml` describes the ring `r1-r2-r3-r4-r1`, using only suffix **5019**
and its allocation block `10.19.0.0/16`. The four LANs are:

| Role | Router / host | Network | Router / host address |
| --- | --- | --- | --- |
| Admin | r1 / h1 | 10.19.10.0/24 | 10.19.10.1 / 10.19.10.10 |
| Students | r2 / h2 | 10.19.20.0/24 | 10.19.20.1 / 10.19.20.10 |
| Servers | r3 / h3 | 10.19.40.0/24 | 10.19.40.1 / 10.19.40.10 |
| Monitoring | r4 / h4 | 10.19.41.0/24 | 10.19.41.1 / 10.19.41.10 |

Router links are r1-r2 `10.19.12.0/30`, r2-r3 `10.19.23.0/30`,
r3-r4 `10.19.34.0/30`, and r1-r4 `10.19.14.0/30`.
For each named pair, the first endpoint uses `.1` and the second `.2`.
There are ten static routes; their complete next hops are in `network.yaml`.
r1 summarises `10.19.40.0/23` via r4 (`10.19.14.2`), while r2 uses the
same summary via r3 (`10.19.23.2`). This /23 covers exactly the server and
monitoring /24s, from `10.19.40.0` through `10.19.41.255`, excluding both
the admin and student LANs. The ring provides physical redundancy, but
static routes do not automatically select an alternative path.

| File | Purpose |
| --- | --- |
| `build_routed.py` | Validates the model, builds Linux routers and hosts, enables IPv4 forwarding and installs static routes. |
| `loop.yaml`, `missing.yaml` | Deliberately invalid route models; stop before any network is built. |
| `make_page3.py` | Generates LANs, links, diagram and routing tables from the model, plus saved evidence and answers. |
| `page3.yaml` | Repository URL and four answers about this design and its observations. |
| `evidence3/` | Original saved runtime output and negative-model validation output. |
| `docs/week3/index.html` | Generated Week 3 page; Week 2 remains at `docs/index.html`. |

### Reproduce Week 3 in Docker

From **PowerShell**, check the container before using it:

```powershell
Set-Location C:\WIC2005_Labs\netlab
docker ps -a --filter name=netlab-week3
docker image ls netlab
```

If `netlab-week3` is running, reuse it:

```powershell
docker exec -it -w /lab netlab-week3 bash
```

The original container uses `--rm`, so it disappears when its main process
exits. Only if it no longer exists, start a replacement with this checkout
mounted at `/lab` (build the image first on a fresh setup):

```powershell
docker build -t netlab:1.0 .
docker run --rm -it --name netlab-week3 --privileged --mount "type=bind,source=$($PWD.Path),target=/lab" -w /lab netlab:1.0 bash
```

`Dockerfile` includes `traceroute`. Inside **Bash**, first validate without
creating interfaces or changing a running network:

```bash
cd /lab
python3 -c "from build_routed import load,check_spec,check_paths; s=load('network.yaml'); p=check_spec(s) or check_paths(s); print(p); assert not p"
python3 build_routed.py loop.yaml
echo $?
python3 build_routed.py missing.yaml
echo $?
```

The valid model prints `[]`. Each invalid model exits with status 1 and
`nothing was built`: the loop fixture catches h1-to-h3 and h4-to-h3 loops
between r1 and r4; the missing-route fixture catches h2-to-h1 and h3-to-h1
at r2. `check_paths()` follows longest-prefix-match routes for all 12
directed host pairs. It validates the static model, not live interface
state or every possible runtime failure.

If no Mininet network is already active in this container, build it in Bash:

```bash
python3 build_routed.py network.yaml
```

At the **Mininet CLI**, test only the four end hosts (routers are also
Mininet hosts internally, so an unqualified `pingall` includes them):

```text
py net.ping([net.get(h) for h in ('h1', 'h2', 'h3', 'h4')])
h1 traceroute -n -I -m 8 -w 1 -q 1 h2
h1 traceroute -n -I -m 8 -w 1 -q 1 h3
h1 traceroute -n -I -m 8 -w 1 -q 1 h4
r1 ip route get 10.19.40.10
r1 ip route get 10.19.41.10
```

Use `exit` at the Mininet prompt when finished; it stops that network.
Do not run a second build or `mn -c` alongside an active Mininet session.

### Saved Week 3 evidence and failure recovery

The original evidence was committed in `d1ebd9f` (validation) and `2d1b7db`
(runtime observations). It is preserved without recreating the experiment.

| Evidence | Recorded result |
| --- | --- |
| `check.txt` | Both invalid models stop with the expected loop/missing-route problems and `nothing was built`. |
| `pingall.txt` | Four end hosts, 0% dropped, 12/12 directed tests received. |
| `routes.txt` | r1, r2, r3, r4 tables concatenated in that order: 5, 5, 6, 6 entries. |
| `traces.txt` | h1-to-h2 via r1-r2; h1-to-h3 via r1-r4-r3; h1-to-h4 via r1-r4. |
| `summary.txt` | Both server and monitoring host lookups on r1 select `10.19.14.2`. |
| `failure.txt` | After r1-r4 went down: `!N` at r1 and `Network is unreachable`. |
| `recovery.txt` | After link-up **and manual route restoration**: h1-to-h3 ping succeeds, 3/3 replies. |

All these files are under `evidence3/` and embedded in the Week 3 page.
The empty, previously committed `routes.txtstraceroute` file is also preserved;
it contains no measurements and is not included as page evidence.
The h3 trace reports r3 as `10.19.23.2`: its ICMP reply heads back toward
h1 through r2. This is compatible with the forward path through r4 to r3.

In the completed failure experiment, `link r1 r4 up` alone did **not**
restore connectivity. Interactive table inspection found r1's /23 summary
and r4's routes to the admin and student LANs missing. The link-down operation
had removed routes using the affected interfaces, and link-up did not recreate
those static entries. The following commands restored them at the Mininet CLI:

```text
r1 ip route replace 10.19.40.0/23 via 10.19.14.2
r4 ip route replace 10.19.10.0/24 via 10.19.14.1
r4 ip route replace 10.19.20.0/24 via 10.19.14.1
h1 ping -c 3 10.19.40.10
```

The intermediate table inspection and route commands were observed
interactively; they are not present in the saved failure/recovery transcripts.
Those transcripts record the failure and final successful ping. A correctly
configured dynamic protocol such as OSPF could detect the failed adjacency and
recalculate paths over the remaining ring links. Here the route design and
scripts provide the control decisions, while Linux performs forwarding.

### Collect evidence in a separate future run

There is no need to repeat the failure experiment to generate the page.
If collecting a fresh baseline later, preserve `evidence3/` and use a new
directory. In **Bash**, before building the network:

```bash
export EVIDENCE_RUN="/lab/evidence3-run-$(date +%Y%m%d-%H%M%S)"
mkdir "$EVIDENCE_RUN"
python3 build_routed.py loop.yaml > "$EVIDENCE_RUN/check.txt" 2>&1
python3 build_routed.py missing.yaml >> "$EVIDENCE_RUN/check.txt" 2>&1
python3 build_routed.py network.yaml
```

At the **Mininet CLI**:

```text
py net.ping([net.get(h) for h in ('h1', 'h2', 'h3', 'h4')])
r1 ip route > "$EVIDENCE_RUN/routes.txt"
r2 ip route >> "$EVIDENCE_RUN/routes.txt"
r3 ip route >> "$EVIDENCE_RUN/routes.txt"
r4 ip route >> "$EVIDENCE_RUN/routes.txt"
h1 traceroute -n -I -m 8 -w 1 -q 1 h2 > "$EVIDENCE_RUN/traces.txt"
h1 traceroute -n -I -m 8 -w 1 -q 1 h3 >> "$EVIDENCE_RUN/traces.txt"
h1 traceroute -n -I -m 8 -w 1 -q 1 h4 >> "$EVIDENCE_RUN/traces.txt"
r1 ip route get 10.19.40.10 > "$EVIDENCE_RUN/summary.txt"
r1 ip route get 10.19.41.10 >> "$EVIDENCE_RUN/summary.txt"
exit
```

Copy the actual four-host ping output into that run's `pingall.txt`.
Do not label copied historical failure/recovery output as a new observation.

### Generate and publish both pages

From **PowerShell**, while `netlab-week3` is running:

```powershell
docker exec -w /lab netlab-week3 python3 make_page.py topology.yaml
docker exec -w /lab netlab-week3 python3 make_page3.py network.yaml
git diff --check
git diff -- docs/index.html
Start-Process .\docs\week3\index.html
```

These generators read saved evidence and do not build a network or repeat
runtime experiments. The Week 2 HTML changes only by adding navigation.
Both generators include links between the two pages. Week 3 has four routing
tables derived from `plan(spec)` and the static routes, sorted by decreasing
prefix length with network address as the tie-breaker. Check all 22 rows,
the eight diagram links, seven evidence blocks, four answers and repository
link. No unanswered fields or template markers should remain.

Before committing, verify that the local Git name/email and authenticated
GitHub account are JoJoChaw20; use the account's verified no-reply address,
configured with `git config --local`, never a guessed email. Check each new
commit with `git log -1 --format=fuller`. Push normally to `origin main`;
do not force-push or rewrite existing history. Pages uses **main /docs**.
After deployment, verify both page URLs and compare the published HTML with
the committed output, including the rendered Mermaid diagram. The Week 3
Spectrum submission URL is **https://jojochaw20.github.io/netlab/week3/**.

## Credits and modifications

Course material and starter scripts are from Firdaus Sahran's WIC2005
[Week 1 lab](https://firdaussahran.github.io/wic2005/weeks/week-01/#tab-lab) and
[Week 2 lab and assignment](https://firdaussahran.github.io/wic2005/weeks/week-02/#tab-lab).
`build_topo.py`, `topology.yaml`, `make_page.py` and `page.yaml` originate from
the course starters. The supplied loading, address-block check, Mininet build,
IPv6 configuration and page template/evidence machinery are credited to those
starters; they are not claimed as original work.

Project modifications include the custom Dockerfile/image, suffix-specific
three-switch/six-host topology, duplicate-address and endpoint validation in
`check()`, `bad.yaml`, collected evidence, dynamic `links_section()` and
`mermaid_diagram()`, completed reflection answers, generated page and this
reproduction guide. See Git history for the recorded progression.

Week 3's `build_routed.py`, `network.yaml`, `make_page3.py` and `page3.yaml`
originate from the [Week 3 course assignment](https://firdaussahran.github.io/wic2005/weeks/week-03/#assignment--route-your-own-network).
Week 3 modifications include the four-router ring, summary routes,
`check_paths()`, negative fixtures, collected evidence, dynamic
`routing_tables_section()`, reflection answers, navigation and generated page.
