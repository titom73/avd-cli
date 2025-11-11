# Quick Start

Get up and running with AVD CLI in minutes! This guide will walk you through generating your first network configuration.

---

## Overview

In this quick start, you'll:

1. Set up a basic AVD inventory
2. Generate configurations
3. View generated outputs

**Estimated time**: 5-10 minutes

---

## Step 1: Prepare Your Inventory

AVD CLI works with standard Ansible inventory structures. For this quick start, we'll use a minimal example.

Create a directory structure:

```bash
mkdir -p my-network/group_vars
cd my-network
```

### Create `inventory.yml`

```yaml
# my-network/inventory.yml
all:
  children:
    FABRIC:
      children:
        SPINES:
          hosts:
            spine1:
            spine2:
        LEAFS:
          hosts:
            leaf1:
            leaf2:
```

### Create `group_vars/FABRIC.yml`

```yaml
# my-network/group_vars/FABRIC.yml
---
fabric_name: MY_FABRIC

design:
  type: l3ls-evpn

mgmt_gateway: 192.168.0.1
mgmt_interface_vrf: default

# Spine configuration
spine:
  defaults:
    platform: vEOS-lab
    loopback_ipv4_pool: 192.168.255.0/24
    bgp_as: 65001
  nodes:
    - name: spine1
      id: 1
      mgmt_ip: 192.168.0.10/24
    - name: spine2
      id: 2
      mgmt_ip: 192.168.0.11/24

# Leaf configuration
l3leaf:
  defaults:
    platform: vEOS-lab
    loopback_ipv4_pool: 192.168.254.0/24
    vtep_loopback_ipv4_pool: 192.168.253.0/24
    uplink_interfaces: [Ethernet1, Ethernet2]
    uplink_switches: [spine1, spine2]
    uplink_ipv4_pool: 172.31.255.0/24
    mlag_interfaces: [Ethernet3, Ethernet4]
    mlag_peer_ipv4_pool: 10.255.252.0/24
    mlag_peer_l3_ipv4_pool: 10.255.251.0/24
    spanning_tree_mode: mstp
    spanning_tree_priority: 4096
  node_groups:
    - group: RACK1
      bgp_as: 65100
      nodes:
        - name: leaf1
          id: 1
          mgmt_ip: 192.168.0.12/24
          uplink_switch_interfaces: [Ethernet1, Ethernet1]
        - name: leaf2
          id: 2
          mgmt_ip: 192.168.0.13/24
          uplink_switch_interfaces: [Ethernet2, Ethernet2]
```

---

## Step 2: Generate Configurations

Now generate the configurations using AVD CLI:

```bash
avd-cli generate all \
  --inventory-path . \
  --output-path output \
  --workflow eos-design
```

!!! tip "Using Environment Variables"
    You can also set environment variables to avoid repeating options:
    ```bash
    export AVD_CLI_INVENTORY_PATH=.
    export AVD_CLI_OUTPUT_PATH=output
    export AVD_CLI_WORKFLOW=eos-design

    avd-cli generate all
    ```

### Expected Output

```
→ Loading inventory...
✓ Loaded 4 devices
→ Generating configurations, documentation, and tests...
→ Processing fabric: MY_FABRIC
  → Generating AVD facts...
  → Generating structured configs...
  → Generating device configurations...
  → Generating documentation...

✓ Generation complete!
                      Generated Files
┏━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Category       ┃ Count ┃ Output Path                 ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Configurations │     4 │ output/configs              │
│ Documentation  │     4 │ output/documentation        │
└────────────────┴───────┴─────────────────────────────┘
```

---

## Step 3: Explore Generated Files

Check the output directory:

```bash
tree output/
```

```
output/
├── configs/
│   ├── leaf1.cfg
│   ├── leaf2.cfg
│   ├── spine1.cfg
│   └── spine2.cfg
└── documentation/
    ├── devices/
    │   ├── leaf1.md
    │   ├── leaf2.md
    │   ├── spine1.md
    │   └── spine2.md
    └── fabric/
        └── MY_FABRIC-documentation.md
```

### View a Configuration

```bash
cat output/configs/spine1.cfg
```

You'll see a complete EOS configuration with:

- Management interface configuration
- BGP underlay configuration
- EVPN overlay configuration
- And more!

---

## Step 4: View Inventory Information

Get detailed information about your inventory:

```bash
avd-cli info --inventory-path .
```

**Output:**

```
→ Loading inventory...
✓ Loaded 4 devices

           Inventory Summary
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Metric                  ┃ Value     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ Total Devices           │ 4         │
│ Total Fabrics           │ 1         │
│ Fabric: MY_FABRIC       │           │
│   - Design Type         │ l3ls-evpn │
│   - Spine Devices       │ 2         │
│   - Leaf Devices        │ 2         │
└─────────────────────────┴───────────┘

                        Devices
┏━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ Hostname ┃ Type  ┃ Platform  ┃ Management IP ┃ Fabric    ┃
┡━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ spine1   │ spine │ vEOS-lab  │ 192.168.0.10  │ MY_FABRIC │
│ spine2   │ spine │ vEOS-lab  │ 192.168.0.11  │ MY_FABRIC │
│ leaf1    │ leaf  │ vEOS-lab  │ 192.168.0.12  │ MY_FABRIC │
│ leaf2    │ leaf  │ vEOS-lab  │ 192.168.0.13  │ MY_FABRIC │
└──────────┴───────┴───────────┴───────────────┴───────────┘
```

---

## Step 5: Deploy Configurations (Optional)

Once you've generated configurations, you can deploy them to your EOS devices using the `deploy` command.

!!! warning "Prerequisites"
    - Devices must be reachable on the network
    - eAPI must be enabled on devices
    - Valid credentials in inventory (`ansible_user`, `ansible_password`)

### Dry-Run Deployment

First, validate your configurations with a dry-run:

```bash
avd-cli deploy eos --inventory-path . --dry-run --diff
```

**Output:**

```
Deployment Plan (dry-run)
  Mode: replace
  Targets: 4 devices
  Concurrency: 10 devices
  Credentials: admin / ********

⠼ Deploying to 4 devices...

                      Deployment Status
┏━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┓
┃ Hostname ┃ Status  ┃ Duration ┃ Diff (+/-) ┃ Error ┃
┡━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━┩
│ spine1   │ success │ 2.34s    │ +127 / -5  │       │
│ spine2   │ success │ 1.89s    │ +127 / -5  │       │
│ leaf1    │ success │ 3.12s    │ +245 / -12 │       │
│ leaf2    │ success │ 2.87s    │ +245 / -12 │       │
└──────────┴─────────┴──────────┴────────────┴───────┘

Summary:
  ✓ Success: 4
  ✗ Failed: 0
  ○ Skipped: 0
```

The **Diff (+/-)** column shows:
- **Green numbers** (+127): Lines added to the configuration
- **Red numbers** (-5): Lines removed from the configuration

### Live Deployment

After validating, deploy to live devices:

```bash
avd-cli deploy eos --inventory-path .
```

!!! tip "Deployment Best Practices"
    - Always run `--dry-run` first to validate changes
    - Use `--diff` to review configuration changes
    - Deploy to groups incrementally: `-l SPINES`, then `-l LEAFS`
    - Enable SSL verification in production: `--verify-ssl`

For more information, see the [Deploy Command Guide](../user-guide/commands/deploy.md).

---

## Next Steps

Congratulations! You've successfully generated and optionally deployed your first network configuration with AVD CLI. 🎉

### Learn More

- **[Basic Usage](basic-usage.md)** - Learn about all available commands
- **[Deploy Command](../user-guide/commands/deploy.md)** - Complete deployment guide
- **[User Guide](../user-guide/commands/overview.md)** - Comprehensive command reference
- **[Inventory Structure](../user-guide/inventory-structure.md)** - Deep dive into inventory organization
- **[Examples](../examples/basic.md)** - More complex examples

### Customize Your Network

Now you can customize your network by:

1. Adding more devices to your inventory
2. Configuring VLANs, SVIs, and network services
3. Defining port channels and MLAG
4. Setting up tenant networks
5. Configuring network services (VXLAN, EVPN, etc.)

Refer to the [Arista AVD documentation](https://avd.arista.com/) for detailed configuration options.

---

## Common Next Commands

```bash
# Generate only configurations
avd-cli generate configs -i . -o output

# Generate only documentation
avd-cli generate docs -i . -o output

# Deploy configurations with dry-run
avd-cli deploy eos -i . --dry-run --diff

# Deploy to specific groups
avd-cli deploy eos -i . -l SPINES

# Validate inventory before generating
avd-cli validate -i .

# Use different workflow (for existing structured configs)
avd-cli generate all -i . -o output --workflow cli-config
```

---

!!! question "Questions?"
    - Check the [FAQ](../faq.md) for common questions
    - Join the Arista AVD community
    - Open an issue on [GitHub](https://github.com/titom73/avd-cli/issues)
