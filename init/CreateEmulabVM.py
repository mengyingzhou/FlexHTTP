#!/usr/bin/env python

import geni.portal as portal
import geni.rspec.pg as RSpec
import geni.rspec.igext as IG


def RLB(r, l, b):
    return ("%dms-%.2f-%dM" % (r, l, b)).replace(".", "d")


machine = "pc3000"

# network configuration for the public access of agent and server 
rtt = 15
loss = 0.0001
band = 10000

# network configuration between client and server
args_list = [
    (30, 0.01, 10),
    (80, 0.05, 7),
    (120, 0.50, 5),
    (230, 1.00, 3),
    (300, 3.00, 1)
]


text = "pairs_with_agent" + \
    ", ".join([RLB(args[0], args[1], args[2]) for args in args_list])

rspec = RSpec.Request()
tour = IG.Tour()
tour.Description(IG.Tour.TEXT, text)
tour.Instructions(IG.Tour.MARKDOWN, text)
rspec.addTour(tour)

pc = portal.Context()

# LAN
lan = RSpec.LAN("lan")
rspec.addResource(lan)

# Agent Node
node_agent = RSpec.RawPC("agent")
node_agent.hardware_type = machine
node_agent.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU20-64-STD'
rspec.addResource(node_agent)

# Agent Interface
iface_agent = node_agent.addInterface("ifa")
iface_agent.addAddress(RSpec.IPv4Address("10.20.0.3", "255.255.255.0"))
iface_agent.latency = rtt
iface_agent.plr = loss
iface_agent.bandwidth = band
lan.addInterface(iface_agent)

ind = 4
for args in args_list:
    args_str = RLB(args[0], args[1], args[2])

    # Client Node
    node_client = RSpec.RawPC("client%s" % args_str)
    node_client.hardware_type = machine
    node_client.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU20-64-STD'
    rspec.addResource(node_client)

    # Interface: Client to Agent 
    iface_client = node_client.addInterface("ifc_agent%d" % ind)
    iface_client.addAddress(RSpec.IPv4Address(
        "10.20.0.{}".format(ind), "255.255.255.0"))
    iface_client.latency = args[0]/2
    iface_client.plr = args[1]/100
    iface_client.bandwidth = args[2]*1000
    lan.addInterface(iface_client)

    # Pair Lan
    pair_lan = RSpec.LAN("lan%d" % ind)
    rspec.addResource(pair_lan)

    # Interface: Client to Server 
    iface_client = node_client.addInterface("ifc_server%d" % ind)
    iface_client.addAddress(RSpec.IPv4Address(
        "10.10.0.2", "255.255.255.0"))
    iface_client.latency = args[0]/2
    iface_client.plr = args[1]/100
    iface_client.bandwidth = args[2]*1000
    pair_lan.addInterface(iface_client)

    # Server Node
    node_server = RSpec.RawPC("server%s" % args_str)
    node_server.hardware_type = machine
    node_server.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU20-64-STD'
    rspec.addResource(node_server)

    # Server Interface
    iface_server = node_server.addInterface("ifs%d" % ind)
    iface_server.addAddress(RSpec.IPv4Address(
        "10.10.0.1", "255.255.255.0"))
    iface_server.latency = args[0]/2
    iface_server.plr = args[1]/100
    iface_server.bandwidth = args[2]*1000
    pair_lan.addInterface(iface_server)

    ind += 1

pc.printRequestRSpec(rspec)
