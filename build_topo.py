#!/usr/bin/env python3
"""Build a Mininet network from a YAML or JSON description, then open the Mininet CLI.

Run it inside the lab container, from the folder holding your files:
    python3 build_topo.py topology.yaml
    python3 build_topo.py topology.json
"""
import ipaddress
import json
import sys

import yaml
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.nodelib import LinuxBridge


def load(path):
    """Read the network description. Same data model, two possible serialisations."""
    with open(path) as f:
        if path.endswith(".json"):
            return json.load(f)
        return yaml.safe_load(f)


def check_mine(spec):
    """Return problems with the student's own addresses (supplied — you don't need to change it).

    Every lab this semester uses addresses from your own blocks:
    IPv4 10.NN.0.0/16 and IPv6 fd00:NNNN::/32, from the last digits of your student ID.
    """
    last4 = str(spec.get("student_id_last4", ""))
    if len(last4) != 4 or not last4.isdigit():
        return ['student_id_last4 must be the last 4 digits of your student ID, in quotes, e.g. "4207"']
    v4_block = ipaddress.ip_network(f"10.{int(last4[2:])}.0.0/16")
    v6_block = ipaddress.ip_network(f"fd00:{last4}::/32")

    problems = []
    for host in spec["hosts"]:
        for key, block in (("ip", v4_block), ("ipv6", v6_block)):
            if key not in host:
                continue
            try:
                address = ipaddress.ip_interface(host[key]).ip
            except ValueError:
                problems.append(f"{host['name']}: {host[key]} isn't a valid address (still NN or NNNN?)")
                continue
            if address not in block:
                problems.append(f"{host['name']}: {address} isn't in your block {block}")
    return problems


def check(spec):
    """Reject duplicate IPv4/IPv6 addresses and unknown link endpoints."""
    problems = []
    seen_addresses = {}

    for host in spec["hosts"]:
        for field in ("ip", "ipv6"):
            if field not in host:
                problems.append(f"{host['name']}: missing {field} address")
                continue

            try:
                address = ipaddress.ip_interface(host[field]).ip
            except ValueError:
                # check_mine() already reports invalid addresses.
                continue

            if address in seen_addresses:
                previous = seen_addresses[address]
                problems.append(
                    f"{host['name']} and {previous} both use {address}"
                )
            else:
                seen_addresses[address] = host["name"]

    nodes = set(spec["switches"])
    nodes.update(host["name"] for host in spec["hosts"])

    for link in spec["links"]:
        if not isinstance(link, list) or len(link) != 2:
            problems.append(f"Invalid link: {link}; expected two node names")
            continue

        for node in link:
            if node not in nodes:
                problems.append(f"Link {link} refers to unknown node {node}")

    return problems


def build(spec):
    """Turn the description into a Mininet network: switches, then hosts, then links."""
    net = Mininet(switch=LinuxBridge, controller=None, autoSetMacs=True)
    for name in spec["switches"]:
        net.addSwitch(name)
    for host in spec["hosts"]:
        net.addHost(host["name"], ip=host["ip"])
    for a, b in spec["links"]:
        net.addLink(a, b)
    return net


def add_ipv6(net, spec):
    """Mininet only sets IPv4 addresses, so add each host's IPv6 address once the network is up."""
    for host in spec["hosts"]:
        if "ipv6" in host:
            node = net.get(host["name"])
            node.cmd(f"ip -6 addr add {host['ipv6']} dev {node.defaultIntf()}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python3 build_topo.py <topology.yaml|topology.json>")
    spec = load(sys.argv[1])

    problems = check_mine(spec) + check(spec)
    if problems:
        for p in problems:
            print("PROBLEM:", p)
        sys.exit("Fix the description and try again.")

    setLogLevel("info")
    net = build(spec)
    net.start()
    add_ipv6(net, spec)
    CLI(net)
    net.stop()
