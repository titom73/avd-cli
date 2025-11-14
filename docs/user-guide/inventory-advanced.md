# Inventory Advanced Features

This page details the features that make an AVD inventory more than a static list of hosts. The loader processes the inventory with a Jinja2 rendering engine, understands Ansible-style `host_vars` and `group_vars`, and applies group inheritance so you can define defaults once and specialize only where needed.

---

## Jinja2 Rendering inside inventory files

Every inventory file that AVD CLI loads is rendered with Jinja2 before validation. That includes `inventory.yml`, any `group_vars/*.yml`, the files under `group_vars/<group>/`, and the `host_vars` files. The rendering context exposes:

- **Inventory data**: devices, groups, fabrics, tags, and any fields defined in `inventory.yml` are available through the usual dot notation.
- **Variables**: any value defined earlier in the hierarchy (global defaults, parent group variables) can be referenced with `{{ variable_name }}`.
- **Environment helpers**: standard Jinja filters (`default`, `upper`, `join`, etc.) behave exactly as in Ansible, and custom filters added by AVD CLI appear automatically.

### Common patterns with Jinja2

```yaml
# group_vars/ATD_LAB.yml
lab_type: act
poc_platform_mtu: 9214
default_interface_mtu: "{% if lab_type == 'act' %}1500{% else %}{{ poc_platform_mtu }}{% endif %}"
management_vrf: "{{ 'MGMT' if lab_type == 'act' else 'DEFAULT' }}"
```

The values above render to concrete integers and strings before the loader validates the inventory. Use this technique for environment-aware defaults, feature flags, or to compose longer strings from shorter pieces of data.

### Using loops and filters

For cases where you need to normalize lists or build maps within templates, loops and filters run without restrictions:

```yaml
# host_vars/s1-leaf1.yml
interfaces:
  - name: Ethernet1
    description: "Uplink to {{ uplink_peer }}"
    mtu: {{ default_interface_mtu }}
  {% for extra in extra_interfaces %}
  - name: {{ extra.name }}
    description: {{ extra.description }}
    mtu: {{ extra.mtu | default(default_interface_mtu) }}
  {% endfor %}
```

The `extra_interfaces` list can come from the host file itself or from shared data defined higher in the hierarchy, so you can extend a subset of devices without duplicating every field.

### Injecting computed values

Sometimes you want a value to depend on other fields. Use Jinja expressions to refer to other variables defined in the same file or inherited ones:

```yaml
# group_vars/ATD_SPINES.yml
uplink_vlan: 4093
mlag_peer_vlan: 4094
peer_link_tag: "{{ uplink_vlan }}-{{ mlag_peer_vlan }}"
```

The loader evaluates `peer_link_tag` after the other two variables resolve, so you get `4093-4094` in downstream templates.

---

## Host-level variables (`host_vars`)

In addition to group variables, you can add a `host_vars/` directory next to `inventory.yml`. Each file is rendered, validated, and merged with the themed defaults.

### Structure

```
inventory/
├── host_vars/
│   ├── s1-signleaf.yml
│   └── s1-spine1.yml
```

### Host overrides

Use host variables for values that differ per device. They are applied after group-level data, so they can override anything except inline values in the inventory file.

```yaml
# host_vars/s1-spine1.yml
hostname: s1-spine1
ansible_host: 192.168.0.10
mgmt_gateway: 192.168.0.1
mlag_peer: s1-spine2
```

If the same value also appears in `group_vars/ATD_SPINES.yml`, the `host_vars` file wins.

### Referencing group data

Host variable files can depend on the group defaults too:

```yaml
# host_vars/s1-leaf1.yml
uplink_peer: "{{ groups.ATD_SPINES | first }}"
leaf_role: leaf
```

Here the `groups` object is part of the Jinja context and contains the inventory groups defined in `inventory.yml`. Use it when you need to look at siblings or parent groups from a host-level template.

---

## Group inheritance and variable precedence

AVD CLI follows the same precedence order as Ansible. If the same variable exists in multiple places, the value defined lower in the list overrides the previous ones.

1. `inventory.yml` `vars` block (highest priority for the file itself)
2. `group_vars/all.yml`
3. `group_vars/<parent group>.yml` or directory files (inheritance follows the group hierarchy defined under `all.children`)
4. `group_vars/<leaf group>.yml`
5. Sub-group directories (e.g., `group_vars/campus_leaves/`) and their files
6. `host_vars/<hostname>.yml`
7. Inline host definitions within `inventory.yml` (lowest priority for duplicates)

### Example inheritance flow

Given this section of `inventory.yml`:

```yaml
all:
  vars:
    ansible_user: arista
  children:
    ATD_LAB:
      vars:
        design: l3ls-evpn
      children:
        ATD_FABRIC:
          vars:
            fabric: atd_fabric
          children:
            ATD_SPINES:
              vars:
                type: spine
            ATD_LEAFS:
              vars:
                type: l3leaf
                default_routing: ospf
```

The device `s1-leaf1` receives values in the following order:

```
1. `group_vars/all.yml`
2. `group_vars/ATD_LAB.yml`
3. `group_vars/ATD_FABRIC.yml`
4. `group_vars/ATD_LEAFS.yml`
5. Any files under `group_vars/pod1/` if the host belongs to `pod1`
6. `host_vars/s1-leaf1.yml`
7. `inventory.yml` host definition
```

The final value for `default_routing` is the one from `ATD_LEAFS`, unless `host_vars/s1-leaf1.yml` sets a different value.

### Merging dictionaries and lists

When you include dictionaries in multiple layers, the loader merges them. For example, if `group_vars/all.yml` defines an `ntp_servers` list and `group_vars/pod1.yml` defines additional entries, the two lists are concatenated, avoiding duplication.

---

## Scenario walkthroughs

### Scenario 1: Feature gate per environment

Use a `lab_type` variable in `group_vars/all.yml` and conditionally enable a service in host or group files:

```yaml
group_vars/all.yml
lab_type: poc
feature_flags:
  enable_advanced_mlag: false
```

```yaml
group_vars/ATD_LAB.yml
lab_type: act
feature_flags:
  enable_advanced_mlag: true
```

```yaml
host_vars/s1-leaf1.yml
mlag_peer_link_mtu: "{% if feature_flags.enable_advanced_mlag %}9214{% else %}1500{% endif %}"
```

This expression evaluates to `9214` for ATD_LAB but still allows labs that do not opt in to stay on the 1500 MTU profile.

### Scenario 2: Host-specific service credentials

Define credentials once under `group_vars` and override them for a single host when necessary:

```yaml
# group_vars/all.yml
service_account:
  username: ansible
  password: supersecure
```

```yaml
# host_vars/s1-spine1.yml
service_account:
  username: spine-admin
  password: evenmoresecure
```

When templates reference `service_account.username`, the spine-specific file is used, keeping credentials separate where required.

### Scenario 3: Mixed group hierarchy

If you have `group_vars/ATD_LEAFS.yml` and a directory `group_vars/ATD_LEAFS/` with multiple files, variables merge:

```yaml
# group_vars/ATD_LEAFS.yml
default_routing: ospf

# group_vars/ATD_LEAFS/interfaces.yml
leaf_interfaces:
  - name: Ethernet1
    description: Uplink
```

The loader treats values from both files as if they were declared together, so you can split large variable sets without losing inheritance.

---

## Tips for managing advanced inventory features

- Keep `group_vars/all.yml` limited to defaults and credential placeholders; override only the values you must change for each environment.
- Use descriptive group names to control inheritance. The loader honors the `children` tree that you express under `all.children`.
- Document any assumptions (for example, `lab_type`) in `group_vars/all.yml` so that templated values remain readable.
- Reserve `host_vars/<hostname>.yml` for truly unique devices such as controllers or leafs with custom uplinks.

For more examples, see the `examples/` directory in the repository, which illustrates real `group_vars`, `host_vars`, and advanced templating use cases.