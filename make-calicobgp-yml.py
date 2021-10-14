import sys

if len(sys.argv) != 2:
    print("supply only the IP of haproxy lb")
    quit()
proxyip = sys.argv[1]

print("""apiVersion: projectcalico.org/v3
kind: BGPConfiguration
metadata:
 name: default
spec:
 logSeverityScreen: Info
 nodeToNodeMeshEnabled: true
 asNumber: 65000

---
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
 name: my-global-peer
spec:
 peerIP: %s
 asNumber: 65000
""" % (proxyip)
)
