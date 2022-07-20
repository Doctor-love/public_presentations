---
title: "The little init system that could"
author: "Joel Rangsmo <joel@rangsmo.se>"
footer: "CC BY-SA 4.0"
description: >-
  Updated version of 2017 SEC-T Spring Pub lightning-talk that showcases less commonly known
  security features of systemd init.
keywords:
  - "systemd"
  - "sec-t"
color: "#ffffff"
class:
  - "invert"
style: |
  section.center {
    text-align: center;
  }

---
![systemd logotype](images/systemd_logo.svg)
# The little init system that could

<!--
Short introduction of me and the topic - commonly unknown security features in systemd init.
-->

---
# This talk is...
- Neither defence nor advocacy for systemd/The Lennart
- All about surrendering to reality and enjoying the spoils

<!--
All major Linux distributions use systemd init these days - many of them other systemd components
as well. This is the case, no matter if we like it or not. We should make the best of it and not
throw out the bathwater with the baby.
-->

---
![bg center 70%](diagrams/systemd_components.svg)

<!--
To be specific, this talk is about systemd init - not the other more or less decoupled components.
Many distributions choose to use these as well, but that's another topic.

Transition: Traditional UNIX init systems have heavily relied upon spaghetti shell scripts -
systemd uses something called "unit files".
-->

---
> A unit file is a plain text ini-style file that encodes information about
> **a service**, a socket, a device, a mount point, an automount point, 
> a swap file or partition, a start-up target, a watched file system path,
> a timer controlled and supervised by systemd(1)...

*[$ man systemd.unit](https://www.freedesktop.org/software/systemd/man/systemd.unit.html)*

<!--
The systemd manual basically says that everything is a unit file in systemd init.
This presentation will focus on unit files of the "service" type.
-->

---
**/etc/systemd/system/tollur.service:**

```ini
[Unit]
Description=Scriptable SMTP proxy

[Service]
Type=simple
ExecStart=/usr/bin/tollur /etc/tollur/conf.ini

[Install]
WantedBy=multi-user.target
```

<!--
Basic example of service unit file.
It specifies a description of the service, a command to execute and information in the "Install"
section which tells systemd init when the unit should be executed.

Systemd supports several methods for describing dependencies of a service, such as reliance on
network access or other services. systemd uses this information calculate startup/shutdown order
and enable optimizations such as parallel startup.
-->

---
```
$ systemctl status tollur.service 

● tollur.service - Scriptable SMTP proxy
     Loaded: loaded (/etc/systemd/system/tollur.service; vendor preset: enabled)
     Active: active (running) since Thu 2022-07-07 10:38:52 UTC; 3s ago
   Main PID: 40274 (python3)
      Tasks: 1 (limit: 3283)
     Memory: 11.8M
        CPU: 51ms
     CGroup: /system.slice/tollur.service
             └─40274 python3 /usr/bin/tollur /etc/tollur/conf.ini

Jul 07 10:38:52 base-1 systemd[1]: Started Scriptable SMTP proxy.
Jul 07 10:38:52 base-1 tollur[40274]: tollur: INFO - Listening on 127.0.0.1:9025...
```

<!--
Once started, we can query the status of the service. Based on the output, we might begin to expect
that systemd init does a little more than the traditional alternatives.

The output contains the latest log output of the command and shows that the service and any
subprocesses have been spawned in a CGroup - these a Linux resource groups that can be used to
limit usage of CPU time, memory, etc.

Transition: But this talk is suppose to be about security features provided by systemd init. Let's
have a look in the man pages again.
-->

---
> systemd.exec — Execution environment configuration
>
> Unit configuration files for **services**, sockets, mount points,
> and swap devices share a subset of configuration options which
> define the **execution environment of spawned processes**...

*[$ man systemd.exec](https://www.freedesktop.org/software/systemd/man/systemd.exec.html)*

<!--
Most settings relevant to security can be found in the execution environment section.
The following slides will show how these can be utilized to minimize your system attack surface.
-->

---
```ini
[Unit]
Description=Simple unprivileged HTTP server

[Service]
Type=simple
ExecStart=/usr/bin/python3 \
          -m http.server --directory /var/www 80

User=notroot
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
```

<!--
This example solves an age old problem on UNIX systems - binding to a port under 1024 while not
running the service as root. In this case, a simple Python HTTP server on port 80.

The Linux kernel supports a security feature called capabilities, which were introduced back in the
early 2000s. This enables us to remove certain privileges from root, such as the capability to
configure networking or arbitrarily kill other users processes. Likewise these can be given to
unprivileged users.
-->

---
```
$ systemctl status uhttpd.service

● uhttpd.service - Simple unprivileged HTTP server
     Loaded: loaded (/etc/systemd/system/uhttpd.service; vendor preset: enabled)
     Active: active (running) since Mon 2022-07-07 22:31:41 UTC; 3s ago
   Main PID: 117640 (python3)
      Tasks: 1 (limit: 3283)
     Memory: 8.3M
        CPU: 37ms
     CGroup: /system.slice/uhttpd.service
             └─117640 /usr/bin/python3 -m http.server --directory /var/www 80

Jul 07 22:31:41 base-1 systemd[1]: Started Simple unprivileged HTTP server.
```

<!--
A lame person would insert the "IT'S WORKING, IT'S WORKING!" GIF here.

Transition: This is quite a basic feature, but systemd init allows us to utilize some other neat
network related restrictions
-->

---
```ini
ExecStart=/usr/bin/bash -c 'ip --brief address show && ping 1.1.1.1'

# Create/Configure an isolated network namespace and setup a
# loopback device inside it
PrivateNetwork=true
```

```
$ systemctl status networkless_daemon.service

× networkless_daemon.service - Daemon with isolated network
[...]

Jul 07 19:13:25 base-1 systemd[1]: Started Daemon with isolated network.
Jul 07 19:13:25 base-1 bash[28390]: lo UNKNOWN 127.0.0.1/8 ::1/128
Jul 07 19:13:25 base-1 bash[28388]: ping: connect: Network is unreachable
[...]
```

<!--
We may want to run a sensitive service without any network access at all. As seen in this case, the
"PrivateNetwork" setting does exactly this.

When enabled, systemd utilizes namespaces functionality provided by the Linux kernel to isolate
the service and subprocesses access from the network. Linux namespaces are also used by container
runtimes such as Docker (or more specifically runc for the pesky nerds out there).

Network namespaces are quite neat - they can for example be used to setup service specific firewall
rules, handle tricky cases of overlapping private IP addresses (RFC 1918) and cherry pick specific
daemons to be force-routed through a VPN connection. This type of configuration is however a bit
out of scope for this presentation.

Transition: Another common thing one might to restrict is a service ability to access parts of the
file system. Back in the days, a common tool for this quest was a chroot jail, but systemd init
allows us to do some other neat things.
-->

---
```ini
ExecStart=/usr/bin/ls /etc /root/.ssh

# Prevent access to potentially juicy loot in home directories
# and selectively mount useful files into /etc as read-only
InaccessiblePaths=/root /home

TemporaryFileSystem=/etc:ro
BindReadOnlyPaths=/etc/ssl/certs /etc/resolv.conf
```

```
$ systemctl status fs_restricted_daemon.service 

[...]
Jul 07 19:40:09 base-1 ls[42849]: /usr/bin/ls:
> cannot access '/root/.ssh': No such file or directory
Jul 07 19:40:09 base-1 ls[42840]: /etc:
Jul 07 19:40:09 base-1 ls[42840]: resolv.conf
Jul 07 19:40:09 base-1 ls[42849]: ssl
[...]
```

<!--
These settings prevents access to home directories and creates a virtual FS for /etc with
specific files mount in as read-only.

Home directories often contain interesting data that most system services has no business looking
through. It would be nice if systemd init supported allowlisting instead, but what to do.

The temporary FS and bind mounting features are two examples of really neat abstractions provided
by systemd init. Sure, you can do these things manually with a wrapper shell script (utilize
Linux namespace functionality etc.) but these are in my opinion not crazy out-of-scope features
for a service manager.
-->

---
```ini
ExecStart=/usr/bin/bash -c 'modprobe 9pnet && echo loaded'

# Disable unused syscall sets (basically groupings of
# syscalls) to minimize kernel attack surface
SystemCallFilter=~@chown @debug @module
```

```
[...]
Jul 07 21:10:40 base-1 bash[84766]: /usr/bin/bash: line 1: 
> 84767 Bad system call (core dumped) modprobe 9pnet
[...]
```

<!--
We can also do some more advanced things like filtering allowed systemcalls and thereby
drastically minimize the kernels attack surface. Is there any reason why your mail server should be
able to load kernel modules or trace other processes?

The syntax may be a bit confusing - the tilde character in this case means that the items should be
excluded from the filter of allowed syscalls (it's now a deny list in other words). The project
provides predefined groups of syscalls (called "sets" in systemd init terminology), which are
prefixed with the at sign as in this example.
-->

---
<!--
_class:
  - "invert"
  - "center"
-->

**ProtectKernelTunables=
NoNewPrivileges=
LoadCredential= 
PrivateDevices=
ProtectSystem=
PrivateUsers=
ProtectProc=
ExecPaths=
[...]**

*[$ man systemd.exec](https://www.freedesktop.org/software/systemd/man/systemd.exec.html)*

<!--
There are many more settings available for restricting security. Why not take the chance to disable
privilege escalation through setuid binaries or limit access to virtual file systems such as /proc
and /dev for a service? The systemd init manual pages are highly recommended, especially the
previously mentioned section for execution environment configuration.
-->

---
![bg right 90%](qr_codes/presentation_zip.link.svg)

For presentation notes, example unit files and similar, see:   
**[talks.radartatska.se/tlistc.zip](https://talks.radartatska.se/tlistc.zip)**  
  
Credits to [Tobias Bernard](https://tobiasbernard.com/) for the
[systemd logo](http://brand.systemd.io/) (CC BY-SA 4.0).

<!--
Thanks for listening!
-->
