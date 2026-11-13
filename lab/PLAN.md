# Lab Plan: Packet Tracer Test Network

Goal: build one enterprise network in two versions.
- `lab/vulnerable/`: deliberately misconfigured. This is the audit target.
- `lab/hardened/`: the same network after fixes. Used for before/after scoring.

Keep the topology small (6 network devices) so every config is easy to export and parse.

## 1. Topology

```
                         [R-ISP]
                        /        \
                  (WAN-1)        (WAN-2)
                      /            \
   [DMZ-WEB]--g0/2--[R-HQ]        [R-BR]--[SW-BR]--[PC-BR1] [PC-BR2]
                      |g0/0
                  [CORE-SW] (L3 switch, inter-VLAN routing)
                   /      \
          [ACC-SW1]        [SRV-SW? or direct]
        PC-STAFF1 PC-GUEST1     SRV-DHCP/DNS, SRV-SYSLOG/TFTP
        IoT device(s)
```

Simplification: attach servers to ACC-SW1 in the Servers VLAN. Final device count:

| Device | Model (Packet Tracer) | Role |
|---|---|---|
| R-HQ | 2911 router | HQ edge router, DMZ gateway, OSPF |
| CORE-SW | 3650-24PS (multilayer) | SVIs for inter-VLAN routing |
| ACC-SW1 | 2960 switch | Access switch for all HQ endpoints |
| R-BR | 2911 router | Branch router |
| SW-BR | 2960 switch | Branch access switch |
| R-ISP | 2911 router | Simulated internet (no hardening needed) |

Endpoints: PC-STAFF1, PC-GUEST1, IoT device (e.g. a camera or sensor), SRV-DHCP-DNS, SRV-SYSLOG-TFTP, DMZ-WEB, PC-BR1, PC-BR2, and a PC-ATTACKER used for demos.

## 2. VLAN and IP plan

| Network | VLAN | Subnet | Gateway |
|---|---|---|---|
| HQ Staff | 10 | 10.1.10.0/24 | 10.1.10.1 (CORE-SW SVI) |
| HQ Servers | 20 | 10.1.20.0/24 | 10.1.20.1 |
| HQ Guests | 30 | 10.1.30.0/24 | 10.1.30.1 |
| HQ IoT | 40 | 10.1.40.0/24 | 10.1.40.1 |
| HQ Management | 99 | 10.1.99.0/24 | 10.1.99.1 |
| CORE-SW to R-HQ link | routed | 10.1.0.0/30 | .1 CORE-SW, .2 R-HQ |
| DMZ | n/a | 172.16.1.0/24 | 172.16.1.1 (R-HQ g0/2) |
| Branch Staff | 10 | 10.2.10.0/24 | 10.2.10.1 (R-BR) |
| Branch Mgmt | 99 | 10.2.99.0/24 | 10.2.99.1 |
| R-HQ to R-ISP | routed | 203.0.113.0/30 | .1 R-HQ, .2 R-ISP |
| R-BR to R-ISP | routed | 198.51.100.0/30 | .1 R-BR, .2 R-ISP |

Fixed addresses: SRV-DHCP-DNS 10.1.20.10, SRV-SYSLOG-TFTP 10.1.20.20, DMZ-WEB 172.16.1.10. Device management IPs are in VLAN 99.

Routing: OSPF area 0 between CORE-SW, R-HQ, R-BR and R-ISP (or static routes if you prefer to start simple). Add a default route toward R-ISP.

## 3. Build order

1. Place devices and cable them.
2. Configure VLANs, trunks, SVIs, DHCP, and routing. **Confirm end-to-end connectivity (ping between sites, DHCP works) before planting any misconfiguration.**
3. Save this as `lab/netsentinel-base.pkt`.
4. Plant the misconfigurations below, and save as `lab/netsentinel-vulnerable.pkt`.
5. Export the configs to `lab/vulnerable/<device>.cfg`.
6. Apply the fixes, save as `lab/netsentinel-hardened.pkt`, and export to `lab/hardened/<device>.cfg`.

## 4. Seeded misconfigurations

Each row becomes a rule in `rules/`. If a command isn't accepted by your Packet Tracer version, note it here and drop that rule from the lab.

| ID | Where | Vulnerable | Hardened |
|---|---|---|---|
| MGMT-001 | all devices | `line vty 0 4` / `transport input telnet` / `password cisco` / `login` | `ip domain-name lab.local`, `crypto key generate rsa modulus 2048`, `ip ssh version 2`, `username admin secret <strong>`, `line vty 0 4`, `transport input ssh`, `login local` |
| MGMT-002 | all devices | `enable password cisco`, no `service password-encryption` | `enable secret <strong>`, `service password-encryption` |
| MGMT-003 | all devices | `exec-timeout 0 0` on console and VTY | `exec-timeout 5 0` |
| MGMT-004 | all devices | no banner | `banner motd #Authorized access only#` |
| MGMT-005 | R-HQ, CORE-SW | `ip http server` enabled | `no ip http server` |
| MGMT-006 | all devices | VTY open to any source | `access-list 10 permit 10.1.99.0 0.0.0.255`, then `access-class 10 in` on VTY |
| MGMT-007 | all devices | no AAA | `aaa new-model`, `aaa authentication login default local` |
| SNMP-001 | R-HQ, CORE-SW | `snmp-server community public RO`, `snmp-server community private RW` | remove both (or use SNMPv3) |
| LOG-001 | all devices | no logging, no NTP, no timestamps | `service timestamps log datetime msec`, `logging host 10.1.20.20`, `ntp server <ip>` |
| L2-001 | ACC-SW1, SW-BR | access ports with no port security | `switchport port-security`, `switchport port-security maximum 2`, `switchport port-security violation shutdown` |
| L2-002 | ACC-SW1, SW-BR | no PortFast or BPDU guard | `spanning-tree portfast default`, `spanning-tree portfast bpduguard default` |
| L2-003 | ACC-SW1, SW-BR | unused ports up and in VLAN 1 | `shutdown` and `switchport access vlan 999` on unused ports |
| L2-004 | trunks | `switchport mode dynamic desirable`, native VLAN 1, all VLANs allowed | `switchport mode trunk`, `switchport nonegotiate`, `switchport trunk native vlan 999`, `switchport trunk allowed vlan 10,20,30,40,99` |
| L2-005 | ACC-SW1 | no DHCP snooping or DAI | `ip dhcp snooping`, `ip dhcp snooping vlan 10,30,40`, trust uplinks, `ip arp inspection vlan 10,30,40` |
| ACL-001 | CORE-SW or R-HQ | guest VLAN allowed everywhere (`permit ip any any`) | extended ACL on VLAN 30 SVI: deny guest to 10.0.0.0/8, permit internet |
| ACL-002 | R-HQ g0/2 | DMZ can reach internal networks (no ACL) | ACL on DMZ interface: deny DMZ to 10.1.0.0/16, permit established and needed ports |
| RT-001 | OSPF devices | no OSPF authentication | `ip ospf authentication message-digest`, `ip ospf message-digest-key 1 md5 <key>` |

Several issues appear on several devices, which is good: the parser and rules must handle each device individually.

## 5. Exporting configs

Do **not** rely on a TFTP server inside Packet Tracer. Files stored there stay inside the simulation and are awkward to get out.

Reliable method, per device:
1. Open the device CLI, run `enable`, `terminal length 0`, `show running-config`.
2. Select all the output, copy it, and paste it into `lab/vulnerable/<device>.cfg`.
3. Remove the `Building configuration...` and `Current configuration` header lines at the top if they appear.

Also check the device's **Config** tab, which may let you export the startup config as a file in your version.

Name files by device: `R-HQ.cfg`, `CORE-SW.cfg`, `ACC-SW1.cfg`, `R-BR.cfg`, `SW-BR.cfg`, `R-ISP.cfg`.

## 6. Done criteria

- [ ] Base network works end to end
- [ ] 17 misconfigurations planted and logged in the table
- [ ] 6 vulnerable configs exported
- [ ] Hardened version built, with 6 configs exported
- [ ] `.pkt` files and configs committed
