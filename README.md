# WIC2005 Weeks 1–2: network 5019

This lab builds a dual-stack Mininet network inside a custom Docker image,
`netlab:1.0`. Three Linux bridges form the chain `s1 — s2 — s3`:
`h1/h2` attach to `s1`, `h3/h4` to `s2`, and `h5/h6` to `s3`.
Hosts use `10.19.0.1–6/24` and `fd00:5019::1–6/64`. Only the student ID
suffix 5019 is used in project content.

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
- A GitHub account and access to the intended repository; a public repository
  works with GitHub Free Pages. Keep real names and full student IDs out of
  public files and use an appropriate pseudonymous Git commit identity.

## Reproduce locally

Host commands below are **PowerShell**. Start by inspecting what already exists:

```powershell
Set-Location C:\WIC2005_Lab\netlab
git status --short
git log --oneline
git remote -v
docker ps -a
docker image ls netlab
```

The inspected setup has a running privileged container named `netlab`, using
`netlab:1.0` and this folder mounted at `/lab`. Reuse it:

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
The expected site is `https://JoJoChaw20.github.io/netlab/`.
Submit the verified **Pages URL**, rather than the repository URL, on Spectrum
yourself. Publication and verification remain pending until confirmed.

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
