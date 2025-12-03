# Workflows

AVD CLI supports multiple workflows for different use cases.

---

## Production Workflows

### eos-design

Full AVD pipeline with topology design and validation for production deployments.

**Use when:**
- Deploying new network fabric
- Managing full leaf-spine architecture
- Need automatic BGP, EVPN, MLAG configuration

**Typical flow:**
```bash
# 1. Validate inventory
avd-cli validate -i ./inventory

# 2. Generate all artifacts
avd-cli generate all -i ./inventory -o ./output

# 3. Deploy (with dry-run first)
avd-cli deploy eos -i ./inventory --dry-run --diff
avd-cli deploy eos -i ./inventory
```

### cli-config

Direct configuration generation from existing structured configs without topology design.

**Use when:**
- Managing configurations outside AVD design patterns
- Converting existing configs to structured format
- Need direct control over configuration templates

---

## Testing & Simulation Workflows

### Containerlab Testing

Generate Containerlab topologies from AVD inventory for pre-deployment testing and CI/CD validation.

**Use when:**
- Testing configurations before production deployment
- Running automated CI/CD validation
- Developing and debugging network designs
- Training and demonstrations

**Typical flow:**
```bash
# 1. Generate configurations
avd-cli generate configs -i ./inventory -o ./output

# 2. Generate Containerlab topology
avd-cli generate topology containerlab \
  -i ./inventory \
  -o ./output

# 3. Deploy with Containerlab
cd ./output/containerlab
sudo containerlab deploy -t containerlab-topology.yml

# 4. Validate with ANTA
avd-cli generate tests -i ./inventory -o ./output
anta nrfu --catalog ./output/tests/spine1_tests.yaml

# 5. Cleanup
sudo containerlab destroy -t containerlab-topology.yml
```

**Benefits:**
- **Pre-deployment validation**: Test configurations before touching production
- **CI/CD integration**: Automated testing in pipelines
- **Safe experimentation**: Test changes without risk
- **Reproducible environments**: Consistent test topologies

See [generate topology containerlab](commands/generate.md#generate-topology-containerlab) for detailed options.

---

## Workflow Selection Guide

| Scenario | Recommended Workflow | Commands |
|----------|---------------------|----------|
| New fabric deployment | eos-design | `validate` → `generate all` → `deploy eos` |
| Configuration updates | eos-design | `generate configs` → `deploy eos --diff` |
| Pre-deployment testing | eos-design + Containerlab | `generate configs` → `generate topology containerlab` |
| CI/CD validation | eos-design + Containerlab | `validate` → `generate all` → `generate topology containerlab` |
| Custom configs | cli-config | `generate configs --workflow cli-config` |

---

## See Also

- [generate command](commands/generate.md) - Complete command reference
- [deploy command](commands/deploy.md) - Deployment options
- [validate command](commands/validate.md) - Validation details
