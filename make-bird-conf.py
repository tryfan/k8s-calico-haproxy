from kubernetes import client, config, dynamic
import sys
from pprint import pprint

from kubernetes.client import api_client
# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config(config_file="/root/.kube/cconfig")

if len(sys.argv) != 2:
    print("supply only the IP of haproxy lb")
    quit()
proxyip = sys.argv[1]

node_detail={}

def print_filter(node):
    print(node)
    print("""filter k8s_%s {
        if ( net ~ [ %s """ % 
        (node.name, node.cidr))

v1 = client.CoreV1Api()
customs = dynamic.DynamicClient(api_client.ApiClient(configuration=config.load_kube_config(config_file="kube.cfg")))

nodes = v1.list_node()
for node in nodes.items:
    # print(node)
    # print(node.metadata.annotations['projectcalico.org/IPv4Address'])
    node_detail[node.metadata.name] = {'name': node.metadata.name, 'ipv4': node.metadata.annotations['projectcalico.org/IPv4Address'].rstrip('/')}
# pprint(nodes['items']['metadata'])
# print(node_detail)

# blocks = v1.

aff_api = customs.resources.get(
    api_version="crd.projectcalico.org/v1",
    kind="BlockAffinity"
    )
affinities = (aff_api.get())
# print(affinities['metadata'])
for item in affinities['items']:
    # print(item['spec'])
    node_detail[item.spec.node].update({'cidr': item.spec.cidr})

# print(node_detail)

print("""router id %s;

log syslog all;

filter all_routes {
  accept;
}
""" % (proxyip)
)

for entry in node_detail:
    # print_filter(entry)
    # print(node_detail[entry])
    split_ipv4 = node_detail[entry]['ipv4'].split('/')
    filter_name = "k8s_%s" % node_detail[entry]['name']
    filter_name = filter_name.replace('-','')
    # print(split_ipv4[0])
    print(
"""filter %s {
    if ( net ~ [ %s ] ) then accept;
    reject;
}
protocol bgp {
    local %s as 65000;
    neighbor %s as 65000;
    direct;
    ipv4 {
        import filter %s;
        export none;
    };
}
""" % (filter_name, node_detail[entry]['cidr'], proxyip, split_ipv4[0], filter_name))

print("""
protocol kernel {
    scan time 60;
    ipv4 {
        export filter all_routes;   # Actually insert routes into the kernel routing table
    };
}

protocol device {
    scan time 60;
}
""")