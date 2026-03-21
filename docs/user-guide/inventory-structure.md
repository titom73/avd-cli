# Inventory Structure

Learn how to organize your AVD inventory for optimal workflow with AVD CLI.

---

## Standard Structure

AVD CLI uses **standard Ansible inventory** format — the same format used by AVD natively.
This means any inventory you already run with `arista.avd` Ansible roles works directly
with AVD CLI without modification.

```
inventory/
├── inventory.yml           # Main inventory file (hosts and groups)
├── group_vars/            # Group-level variables
│   ├── all.yml           # Global variables (inherited by all devices)
│   ├── all/              # Alternative: directory for multiple files
│   │   └── common.yml
│   ├── FABRIC.yml        # Fabric-level variables
│   ├── SPINES.yml        # Spine-specific variables
│   ├── LEAFS.yml         # Leaf-specific variables
│   └── campus_leaves/    # Group directory with multiple files
│       ├── interfaces.yml
│       ├── dot1x.yml
│       └── leaf.yml
└── host_vars/             # Host-level variables (optional)
    ├── spine1.yml        # Individual host configuration
    └── leaf1.yml
```

---

## Inventory File Structure

### EOS Design Workflow Example

The `inventory.yml` file defines the hierarchy of devices and groups.
All Ansible variables follow standard Ansible conventions:

```yaml
---
all:
  vars:
    # Global Ansible connection parameters — read by `deploy eos`
    ansible_user: arista
    ansible_password: arista123!
    ansible_network_os: arista.eos.eos    # Identifies EOS devices for `deploy eos`
    ansible_connection: httpapi
    ansible_httpapi_use_ssl: true         # HTTPS is always used (see note below)
    ansible_httpapi_validate_certs: false # SSL certificate validation
    ansible_python_interpreter: $(which python3)

  children:
    cv_servers:           # CloudVision servers (optional)
      hosts:
        cv_atd1:
          ansible_host: 192.168.0.5
          cv_collection: v3
    ATD_LAB:              # Main lab group
      children:
        ATD_FABRIC:       # Fabric group containing spines and leafs
          children:
            ATD_SPINES:   # Spine switches group
              vars:
                type: spine
              hosts:
                s1-spine1:
                  ansible_host: 192.168.0.10
                s1-spine2:
                  ansible_host: 192.168.0.11
            ATD_LEAFS:    # Leaf switches group
              vars:
                type: l3leaf
              children:
                pod1:     # Leaf sub-groups for MLAG pairs
                  hosts:
                    s1-leaf1:
                      ansible_host: 192.168.0.12
                    s1-leaf2:
                      ansible_host: 192.168.0.13
                pod2:
                  hosts:
                    s1-leaf3:
                      ansible_host: 192.168.0.14
                    s1-leaf4:
                      ansible_host: 192.168.0.15
        ATD_TENANTS_NETWORKS: # Tenant configuration group
          children:
            ATD_LEAFS:    # ATD_LEAFS referenced here too — avd-cli deduplicates
        ATD_SERVERS:         # Server configuration group
          children:
            ATD_LEAFS:    # avd-cli handles hosts appearing under multiple groups
```

!!! note "Multi-group membership"
    A device like `s1-leaf1` that belongs to multiple groups (`ATD_FABRIC`,
    `ATD_TENANTS_NETWORKS`, `ATD_SERVERS`) is resolved **once** by AVD CLI.
    Connection data from the first occurrence is used; all group memberships are
    accumulated for filtering with `--groups`.

### CLI Config Gen Workflow Example

For configuration-only generation without topology design:

```yaml
---
all:
  vars:
    ansible_user: admin
    ansible_connection: httpapi
    ansible_network_os: arista.eos.eos
    ansible_httpapi_use_ssl: true
    ansible_httpapi_validate_certs: false
  hosts:
    spine1:
      ansible_host: 192.168.73.11
    spine2:
      ansible_host: 192.168.73.12
    leaf1:
      ansible_host: 192.168.73.13
    leaf2:
      ansible_host: 192.168.73.14
```

---

## Variables Read by `deploy eos`

The following Ansible variables are read by `avd-cli deploy eos` (and by
`info` / `validate`) to establish device connections.  Variable precedence
follows standard Ansible rules: **host vars override group vars**, which
override parent group vars.

| Variable | Required | Default | Notes |
|---|---|---|---|
| `ansible_host` | **Yes** | — | IP address or FQDN of the device. Hosts without this variable are skipped with a warning. |
| `ansible_user` | **Yes** | — | eAPI username. |
| `ansible_password` | **Yes** | — | eAPI password. |
| `ansible_network_os` | No | `arista.eos.eos` | Identifies the device OS. Only `arista.eos.eos` hosts are included by `deploy eos`; any other value skips the host with a warning. Absent → treated as `arista.eos.eos` for backward compatibility. |
| `ansible_httpapi_validate_certs` | No | `false` | Whether to validate the eAPI SSL certificate chain. Set to `true` in production with valid certificates. |
| `ansible_httpapi_use_ssl` | No | `true` | Must be `true`. AVD CLI always uses HTTPS (eAPI over SSL). If set to `false`, a warning is logged and HTTPS is used anyway. |

!!! warning "HTTPS only"
    AVD CLI communicates with devices exclusively over HTTPS (eAPI over SSL).
    Setting `ansible_httpapi_use_ssl: false` is not supported and will be ignored
    with a warning.

!!! tip "ansible_connection and ansible_python_interpreter"
    These variables are parsed by Ansible during playbook execution.
    AVD CLI ignores them — include them for Ansible compatibility, they do not
    affect `avd-cli deploy eos` behaviour.

---

## Variable Inheritance Hierarchy

Variables are inherited in this specific order (last wins):

1. **`group_vars/all.yml`** - Global defaults for all devices
2. **Parent group variables** - Higher-level groups (e.g., `ATD_LAB.yml`)
3. **Fabric group variables** - Fabric-specific settings (e.g., `ATD_FABRIC.yml`)
4. **Device type groups** - Role-specific variables (e.g., `ATD_SPINES.yml`, `ATD_LEAFS.yml`)
5. **Sub-group variables** - Pod or rack-specific settings (e.g., `pod1.yml`)
6. **Host-specific variables** - Individual device overrides from `host_vars/`

### Example Inheritance Flow

For device `s1-leaf1` in the hierarchy above:

```
all.yml → ATD_LAB.yml → ATD_FABRIC.yml → ATD_LEAFS.yml → pod1.yml → host_vars/s1-leaf1.yml
```

---

## Group Variable Organization

### Single File per Group

```
group_vars/
├── all.yml              # Global settings
├── ATD_FABRIC.yml       # Fabric topology and BGP settings
├── ATD_SPINES.yml       # Spine-specific configuration
└── ATD_LEAFS.yml        # Leaf-specific configuration
```

### Directory Structure per Group

```
group_vars/
├── all/
│   ├── common.yml       # Base settings
│   └── credentials.yml  # Authentication settings
├── campus_leaves/
│   ├── interfaces.yml   # Interface profiles and network ports
│   ├── dot1x.yml       # 802.1X authentication settings
│   └── leaf.yml        # Leaf-specific topology
└── campus_spines/
    └── spines.yml       # Spine configuration
```

---

## Jinja2 Template Support

AVD CLI supports Jinja2 templating in all variable files, enabling dynamic configuration based on conditions and variables.

### Basic Jinja2 Examples

#### Conditional Values

```yaml
# Platform-dependent MTU settings
default_interface_mtu: "{% if lab_type == 'act' %}1500{% else %}{{poc_platform_mtu}}{% endif %}"
mlag_peer_link_mtu: "{% if lab_type == 'act' %}1500{% else %}9214{% endif %}"

# Environment-based VRFs
mgmt_interface_vrf: "{{default_poc_management_vrf}}"
default_poc_syslog_vrf: "{{ default_poc_management_vrf }}"
```

#### Variable References

```yaml
# Reference other variables
default_poc_management_vrf: MGMT
default_poc_syslog_server: "192.168.0.201"
default_poc_sflow_vrf: "{{ default_poc_management_vrf }}"
default_poc_radius_vrf: "{{ default_poc_management_vrf }}"
```

#### Complex Logic

```yaml
# Feature flags with conditions
lab_type: "act"
has_poe: False
has_storm_control: False

# Dynamic platform settings
poc_platform_mtu: 1500
platform_settings:
  mtu: "{% if lab_type == 'act' %}1500{% else %}{{poc_platform_mtu}}{% endif %}"
  features:
    poe: "{{ has_poe }}"
    storm_control: "{{ has_storm_control }}"
```

### Advanced Jinja2 Usage

#### Switch-Specific Configuration

```yaml
network_ports:
  - switches:
      - "leaf-1a"
      - "leaf-1b"
      - "leaf-2a"
    switch_ports:
      - Ethernet10-15
    description: 802.1x Standard Port - EAPoL with Multi Host
    profile: PP-DOT1X
    native_vlan: 666
    structured_config:
      switchport:
        phone:
          trunk: untagged
          vlan: 667

  - platforms:           # Platform-based selection
      - '720XP'
    switch_ports:
      - Ethernet1-10
    description: 802.1x Standard Port - EAPoL with Multi Host
    profile: PP-DOT1X
    native_vlan: 666
```

#### Custom Structured Configuration

```yaml
# Prefix for custom configuration sections
custom_structured_configuration_prefix:
  - "custom_inband_"
  - "custom_structured_"

# Dynamic fabric tags
default_cv_tags_campus: CAMPUS_AVD
cv_tags:
  - "{{ default_cv_tags_campus }}"
  - "FABRIC_{{ fabric_name | upper }}"
```

---

## Best Practices

### 1. Group Organization

- Use hierarchical groups that reflect your network topology
- Separate fabric configuration from tenant/service configuration
- Group devices by role (spine, leaf, border-leaf, etc.)

### 2. Variable Structure

- Keep global settings in `group_vars/all.yml`
- Use fabric-specific files for topology and underlay settings
- Separate tenant/service configuration into dedicated groups

### 3. Jinja2 Usage

- Use Jinja2 for environment-specific values (lab vs production)
- Reference variables to avoid duplication
- Keep complex logic in dedicated variable files

### 4. File Organization

- Use single files for simple groups
- Use directories for complex groups with multiple configuration aspects
- Name files descriptively (e.g., `interfaces.yml`, `routing.yml`)

### 5. Host Variables

- Use `host_vars/` sparingly for device-specific overrides
- Prefer group variables for consistent configuration
- Document any host-specific exceptions

---

## Validation

AVD CLI automatically validates your inventory structure:

```bash
# Validate inventory structure
avd-cli info --inventory ./inventory

# Check variable inheritance
avd-cli info --inventory ./inventory --format yaml
```

See the complete [User Guide](commands/overview.md) for more commands and options.

```
inventory/
├── inventory.yml           # Main inventory file (hosts and groups)
├── group_vars/            # Group-level variables
│   ├── all.yml           # Global variables (inherited by all devices)
│   ├── all/              # Alternative: directory for multiple files
│   │   └── common.yml
│   ├── FABRIC.yml        # Fabric-level variables
│   ├── SPINES.yml        # Spine-specific variables
│   ├── LEAFS.yml         # Leaf-specific variables
│   └── campus_leaves/    # Group directory with multiple files
│       ├── interfaces.yml
│       ├── dot1x.yml
│       └── leaf.yml
└── host_vars/             # Host-level variables (optional)
    ├── spine1.yml        # Individual host configuration
    └── leaf1.yml
```

---

## Inventory File Structure

The main `inventory.yml` file defines the hierarchy of devices and groups:

### Flat Connection Schema (deploy/info/validate)

In addition to the Ansible-style structure, `deploy eos`, `info`, and `validate`
also support a flat schema:

```yaml
---
globals:
  credentials:
    username: arista
    password: arista
  tls_verify: false

groups:
  leaf_eos:
    kind: arista_eos
    credentials:
      username: arista
      password: arista
  demo: {}

hosts:
  leaf1:
    address: 192.168.72.13   # alias accepted: ansible_host
    groups:
      - leaf_eos
      - demo
```

Resolution rules for flat schema:

1. `credentials` (field by field): host > groups (in host order, first group wins) > globals
2. `kind`: host > groups (first group wins) > globals
3. `tls_verify`: host > groups (first group wins) > globals

Validation rules:

- Referenced groups must exist
- `kind` must resolve for every host
- Credentials must resolve (`username` and `password`)
- `address` (or `ansible_host`) must be present

!!! warning "Do not mix schemas in one file"
    A single inventory file cannot mix flat keys (`globals/groups/hosts`) with Ansible top-level keys (`all`, custom root groups, etc.).

### EOS Design Workflow Example

```yaml
---
all:
  children:
    cv_servers:           # CloudVision servers (optional)
      hosts:
        cv_atd1:
          ansible_host: 192.168.0.5
          cv_collection: v3
    ATD_LAB:              # Main lab group
      children:
        ATD_FABRIC:       # Fabric group containing spines and leafs
          children:
            ATD_SPINES:   # Spine switches group
              vars:
                type: spine
              hosts:
                s1-spine1:
                  ansible_host: 192.168.0.10
                s1-spine2:
                  ansible_host: 192.168.0.11
            ATD_LEAFS:    # Leaf switches group
              vars:
                type: l3leaf
              children:
                pod1:     # Leaf sub-groups for MLAG pairs
                  hosts:
                    s1-leaf1:
                      ansible_host: 192.168.0.12
                    s1-leaf2:
                      ansible_host: 192.168.0.13
                pod2:
                  hosts:
                    s1-leaf3:
                      ansible_host: 192.168.0.14
                    s1-leaf4:
                      ansible_host: 192.168.0.15
        ATD_TENANTS_NETWORKS: # Tenant configuration group
          children:
            ATD_LEAFS:
        ATD_SERVERS:         # Server configuration group
          children:
            ATD_LEAFS:
  vars:
    # Global Ansible connection parameters
    ansible_user: arista
    ansible_password: arista123!
    ansible_network_os: arista.eos.eos
    ansible_connection: httpapi
    ansible_httpapi_use_ssl: true
    ansible_httpapi_validate_certs: false
    ansible_python_interpreter: $(which python3)
```

### CLI Config Gen Workflow Example

For configuration-only generation without topology design:

```yaml
---
all:
  hosts:
    spine1:
      ansible_host: 192.168.73.11
    spine2:
      ansible_host: 192.168.73.12
    leaf1:
      ansible_host: 192.168.73.13
    leaf2:
      ansible_host: 192.168.73.14
  vars:
    ansible_user: admin
    ansible_connection: httpapi
    ansible_network_os: arista.eos.eos
    ansible_httpapi_use_ssl: true
    ansible_httpapi_validate_certs: false
```

---

## Variable Inheritance Hierarchy

Variables are inherited in this specific order (last wins):

1. **`group_vars/all.yml`** - Global defaults for all devices
2. **Parent group variables** - Higher-level groups (e.g., `ATD_LAB.yml`)
3. **Fabric group variables** - Fabric-specific settings (e.g., `ATD_FABRIC.yml`)
4. **Device type groups** - Role-specific variables (e.g., `ATD_SPINES.yml`, `ATD_LEAFS.yml`)
5. **Sub-group variables** - Pod or rack-specific settings (e.g., `pod1.yml`)
6. **Host-specific variables** - Individual device overrides from `host_vars/`

### Example Inheritance Flow

For device `s1-leaf1` in the hierarchy above:

```
all.yml → ATD_LAB.yml → ATD_FABRIC.yml → ATD_LEAFS.yml → pod1.yml → host_vars/s1-leaf1.yml
```

---

## Group Variable Organization

### Single File per Group

```
group_vars/
├── all.yml              # Global settings
├── ATD_FABRIC.yml       # Fabric topology and BGP settings
├── ATD_SPINES.yml       # Spine-specific configuration
└── ATD_LEAFS.yml        # Leaf-specific configuration
```

### Directory Structure per Group

```
group_vars/
├── all/
│   ├── common.yml       # Base settings
│   └── credentials.yml  # Authentication settings
├── campus_leaves/
│   ├── interfaces.yml   # Interface profiles and network ports
│   ├── dot1x.yml       # 802.1X authentication settings
│   └── leaf.yml        # Leaf-specific topology
└── campus_spines/
    └── spines.yml       # Spine configuration
```

---

## Jinja2 Template Support

AVD CLI supports Jinja2 templating in all variable files, enabling dynamic configuration based on conditions and variables.

### Basic Jinja2 Examples

#### Conditional Values

```yaml
# Platform-dependent MTU settings
default_interface_mtu: "{% if lab_type == 'act' %}1500{% else %}{{poc_platform_mtu}}{% endif %}"
mlag_peer_link_mtu: "{% if lab_type == 'act' %}1500{% else %}9214{% endif %}"

# Environment-based VRFs
mgmt_interface_vrf: "{{default_poc_management_vrf}}"
default_poc_syslog_vrf: "{{ default_poc_management_vrf }}"
```

#### Variable References

```yaml
# Reference other variables
default_poc_management_vrf: MGMT
default_poc_syslog_server: "192.168.0.201"
default_poc_sflow_vrf: "{{ default_poc_management_vrf }}"
default_poc_radius_vrf: "{{ default_poc_management_vrf }}"
```

#### Complex Logic

```yaml
# Feature flags with conditions
lab_type: "act"
has_poe: False
has_storm_control: False

# Dynamic platform settings
poc_platform_mtu: 1500
platform_settings:
  mtu: "{% if lab_type == 'act' %}1500{% else %}{{poc_platform_mtu}}{% endif %}"
  features:
    poe: "{{ has_poe }}"
    storm_control: "{{ has_storm_control }}"
```

### Advanced Jinja2 Usage

#### Switch-Specific Configuration

```yaml
network_ports:
  - switches:
      - "leaf-1a"
      - "leaf-1b"
      - "leaf-2a"
    switch_ports:
      - Ethernet10-15
    description: 802.1x Standard Port - EAPoL with Multi Host
    profile: PP-DOT1X
    native_vlan: 666
    structured_config:
      switchport:
        phone:
          trunk: untagged
          vlan: 667

  - platforms:           # Platform-based selection
      - '720XP'
    switch_ports:
      - Ethernet1-10
    description: 802.1x Standard Port - EAPoL with Multi Host
    profile: PP-DOT1X
    native_vlan: 666
```

#### Custom Structured Configuration

```yaml
# Prefix for custom configuration sections
custom_structured_configuration_prefix:
  - "custom_inband_"
  - "custom_structured_"

# Dynamic fabric tags
default_cv_tags_campus: CAMPUS_AVD
cv_tags:
  - "{{ default_cv_tags_campus }}"
  - "FABRIC_{{ fabric_name | upper }}"
```

---

## Best Practices

### 1. Group Organization

- Use hierarchical groups that reflect your network topology
- Separate fabric configuration from tenant/service configuration
- Group devices by role (spine, leaf, border-leaf, etc.)

### 2. Variable Structure

- Keep global settings in `group_vars/all.yml`
- Use fabric-specific files for topology and underlay settings
- Separate tenant/service configuration into dedicated groups

### 3. Jinja2 Usage

- Use Jinja2 for environment-specific values (lab vs production)
- Reference variables to avoid duplication
- Keep complex logic in dedicated variable files

### 4. File Organization

- Use single files for simple groups
- Use directories for complex groups with multiple configuration aspects
- Name files descriptively (e.g., `interfaces.yml`, `routing.yml`)

### 5. Host Variables

- Use `host_vars/` sparingly for device-specific overrides
- Prefer group variables for consistent configuration
- Document any host-specific exceptions

---

## Validation

AVD CLI automatically validates your inventory structure:

```bash
# Validate inventory structure
avd-cli info --inventory ./inventory

# Check variable inheritance
avd-cli info --inventory ./inventory --format yaml
```

See the complete [User Guide](commands/overview.md) for more commands and options.
