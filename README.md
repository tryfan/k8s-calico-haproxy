# k8s-calico-haproxy

## Setup
Make a MKS cluster

Create u20 base VM for haproxy, login, sudo to root

## Configure HAProxy VM
Install up to date haproxy
```
add-apt-repository -y ppa:vbernat/haproxy-2.4
apt update
apt install -y haproxy
systemctl stop haproxy
systemctl disable haproxy
# to enable binding to privileged ports:
setcap cap_net_bind_service=+ep /usr/sbin/haproxy
```

Get haproxy ingress controller
```
wget https://github.com/haproxytech/kubernetes-ingress/releases/download/v1.6.2/haproxy-ingress-controller_1.6.2_Linux_x86_64.tar.gz 1>/dev/null 2>/dev/null
mkdir ingress-controller
tar -xzvf haproxy-ingress-controller_1.6.2_Linux_x86_64.tar.gz -C ./ingress-controller
cp ./ingress-controller/haproxy-ingress-controller /usr/local/bin/
```

Get systemd service file and copy
```
wget https://raw.githubusercontent.com/haproxytechblog/ingress-controller-external-example/master/haproxy-ingress.service
cp haproxy-ingress.service /etc/systemd/system/
```

Get kube config and copy to /root/.kube/config
```
mkdir -p /root/.kube
vi /root/.kube/config
```

Enable and start the ingress proxy
```
systemctl enable haproxy-ingress
systemctl start haproxy-ingress
```

Get and install bird routing daemon
```
add-apt-repository -y ppa:cz.nic-labs/bird
apt update
apt install bird2
```

Clone the following repo to get a couple of utils
```
git clone https://github.com/tryfan/k8s-calico-haproxy
cd k8s-calico-haproxy
```

Make a python venv to run utils
```
apt install virtualenv
virtualenv venv
source venv/bin/activate
```

Run make-bird-conf.py to create a bird.conf file and put it in /etc/bird/bird.conf
```
pip install -r requirements
python make-bird-conf.py $(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}') > /etc/bird/bird.conf
```

Restart bird to grab new config
```
systemctl restart bird
```

Grab calicoctl to apply bgp config to k8s
```
curl -o calicoctl -O -L  "https://github.com/projectcalico/calicoctl/releases/download/v3.17.1/calicoctl"
chmod +x calicoctl
```
Make the calico BGP config
```
python make-calicobgp-yml.py $(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}') > calicobgp.yml
```

Apply bgp config
```
./calicoctl apply -f calicobgp.yml
```

Check to see if stuff works

This should show one peer 
```
./calicoctl get bgppeer
```
This should show as many established bgp sessions as you have masters and workers and two # more for kernel and device
```
birdc show protocols
```

## Test app

The `tlskey.yml` file contains a self signed key for demo purposes, just apply that into the default namespace.

The `www.yml` file contains 5 replicas of the `jmalloc/echo-server` container.  On lines 48, 51, and 69, replace the IP address in the DNS name with your haproxy ip address.  Once you apply this file, you should be able to reach both `http://www.<ip>.nip.io` and `https://www.<ip>.nip.io`