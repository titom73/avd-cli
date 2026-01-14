# Technical Debt Reduction - AVD CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Réduire la dette technique du repository AVD CLI en extrayant le code dupliqué, réorganisant la structure CLI, et ajoutant les abstractions manquantes.

**Architecture:** Refactoring progressif en 4 phases : (1) extraction des utilitaires partagés, (2) réorganisation CLI, (3) création d'abstractions, (4) amélioration des tests. Chaque phase est indépendante et peut être mergée séparément.

**Tech Stack:** Python 3.10+, Click, Rich, pytest, dataclasses → Pydantic v2

---

## Phase 1: Extraction du Code Dupliqué

### Task 1.1: Créer le module utilitaire `deep_merge`

**Files:**
- Create: `avd_cli/utils/merge.py`
- Modify: `avd_cli/logics/loader.py:735-770`
- Modify: `avd_cli/logics/generator.py:598-621`
- Test: `tests/unit/utils/test_merge.py`

**Step 1: Write the failing test**

```python
# tests/unit/utils/test_merge.py
"""Unit tests for deep_merge utility."""
import pytest
from avd_cli.utils.merge import deep_merge


class TestDeepMerge:
    """Test cases for deep_merge function."""

    def test_deep_merge_flat_dicts(self) -> None:
        """Test merging flat dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested_dicts(self) -> None:
        """Test merging nested dictionaries."""
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"d": 4, "e": 5}, "f": 6}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}

    def test_deep_merge_list_replacement(self) -> None:
        """Test that lists are replaced, not merged."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result = deep_merge(base, override)
        assert result == {"items": [4, 5]}

    def test_deep_merge_does_not_mutate_inputs(self) -> None:
        """Test that original dicts are not modified."""
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        deep_merge(base, override)
        assert base == {"a": {"b": 1}}
        assert override == {"a": {"c": 2}}

    def test_deep_merge_empty_base(self) -> None:
        """Test merging into empty base."""
        result = deep_merge({}, {"a": 1})
        assert result == {"a": 1}

    def test_deep_merge_empty_override(self) -> None:
        """Test merging empty override."""
        result = deep_merge({"a": 1}, {})
        assert result == {"a": 1}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/utils/test_merge.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'avd_cli.utils.merge'"

**Step 3: Write minimal implementation**

```python
# avd_cli/utils/merge.py
"""Deep merge utility for dictionary operations."""
from copy import deepcopy
from typing import Any, Dict


def deep_merge(
    base: Dict[str, Any],
    override: Dict[str, Any],
    *,
    copy: bool = True
) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Recursively merges nested dictionaries. Override values take precedence.
    Lists are replaced, not merged.

    Parameters
    ----------
    base : Dict[str, Any]
        Base dictionary
    override : Dict[str, Any]
        Dictionary to merge into base (takes precedence)
    copy : bool, optional
        If True, creates deep copies to avoid mutation, by default True

    Returns
    -------
    Dict[str, Any]
        Merged dictionary

    Examples
    --------
    >>> base = {"a": 1, "b": {"c": 2, "d": 3}}
    >>> override = {"b": {"d": 4, "e": 5}, "f": 6}
    >>> deep_merge(base, override)
    {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "f": 6}
    """
    result = deepcopy(base) if copy else base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value, copy=copy)
        else:
            result[key] = deepcopy(value) if copy else value

    return result
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/utils/test_merge.py -v`
Expected: PASS

**Step 5: Update loader.py to use shared utility**

Replace lines 735-770 in `avd_cli/logics/loader.py`:
```python
# Add import at top of file
from avd_cli.utils.merge import deep_merge

# Remove the _deep_merge method and replace usages:
# Change: merged_data = self._deep_merge(merged_data, file_data)
# To: merged_data = deep_merge(merged_data, file_data, copy=False)
```

**Step 6: Update generator.py to use shared utility**

Replace lines 598-621 in `avd_cli/logics/generator.py`:
```python
# Add import at top of file
from avd_cli.utils.merge import deep_merge

# Remove the _deep_merge method and replace usages
```

**Step 7: Run all tests**

Run: `uv run pytest tests/ -v --tb=short`
Expected: All tests PASS

**Step 8: Commit**

```bash
git add avd_cli/utils/merge.py tests/unit/utils/test_merge.py avd_cli/logics/loader.py avd_cli/logics/generator.py
git commit -m "refactor(utils): extract deep_merge to shared utility

- Create avd_cli/utils/merge.py with deep_merge function
- Remove duplicate implementations from loader.py and generator.py
- Add comprehensive unit tests for merge utility
- Fixes DRY violation across logics layer"
```

---

### Task 1.2: Extraire la logique de filtrage des devices

**Files:**
- Modify: `avd_cli/utils/device_filter.py`
- Modify: `avd_cli/logics/generator.py:74-122`
- Modify: `avd_cli/logics/topology.py:71-82`
- Test: `tests/unit/utils/test_device_filter.py`

**Step 1: Write the failing test**

```python
# Add to tests/unit/utils/test_device_filter.py
def test_filter_devices_from_inventory(self) -> None:
    """Test filtering devices from InventoryData."""
    from avd_cli.utils.device_filter import filter_devices
    # ... test implementation
```

**Step 2-8:** Similar TDD pattern - extract `filter_devices(inventory, device_filter)` function to device_filter.py

**Commit message:**
```
refactor(utils): consolidate device filtering logic

- Add filter_devices() function to device_filter.py
- Remove duplicate _filter_devices() from generator.py and topology.py
- Standardize filtering interface across all modules
```

---

## Phase 2: Réorganisation de la Structure CLI

### Task 2.1: Extraire la commande deploy vers son propre module

**Files:**
- Create: `avd_cli/cli/commands/deploy.py`
- Modify: `avd_cli/cli/main.py:1169-1395`
- Test: `tests/unit/cli/test_commands_deploy.py`

**Step 1: Write the failing test**

```python
# tests/unit/cli/test_commands_deploy.py
"""Unit tests for deploy command."""
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

from avd_cli.cli.commands.deploy import deploy_eos


class TestDeployCommand:
    """Test cases for deploy command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        return CliRunner()

    @patch("avd_cli.cli.commands.deploy.EosDeployer")
    @patch("avd_cli.cli.commands.deploy.InventoryLoader")
    def test_deploy_eos_dry_run(
        self,
        mock_loader: MagicMock,
        mock_deployer: MagicMock,
        runner: CliRunner,
        tmp_path,
    ) -> None:
        """Test deploy eos command with dry-run."""
        # Setup mocks
        mock_inventory = MagicMock()
        mock_loader.return_value.load.return_value = mock_inventory

        inventory_path = tmp_path / "inventory"
        inventory_path.mkdir()

        result = runner.invoke(
            deploy_eos,
            ["--inventory-path", str(inventory_path), "--dry-run"],
        )
        assert result.exit_code == 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/cli/test_commands_deploy.py -v`
Expected: FAIL

**Step 3: Create deploy command module**

```python
# avd_cli/cli/commands/deploy.py
"""Deploy command for AVD CLI."""
import asyncio
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from avd_cli.cli.shared import common_inventory_options

console = Console()


@click.group(name="deploy")
def deploy() -> None:
    """Deploy configurations to network devices."""
    pass


@deploy.command(name="eos")
@common_inventory_options
@click.option("--dry-run", is_flag=True, help="Simulate deployment without changes")
@click.option("--diff", is_flag=True, help="Show configuration diff")
@click.option("--max-concurrent", default=10, help="Max concurrent deployments")
@click.option("--timeout", default=30, help="Timeout per device in seconds")
@click.pass_context
def deploy_eos(
    ctx: click.Context,
    inventory_path: Path,
    output_path: Optional[Path],
    devices: tuple[str, ...],
    dry_run: bool,
    diff: bool,
    max_concurrent: int,
    timeout: int,
) -> None:
    """Deploy configurations to EOS devices via eAPI."""
    # Import lazily to avoid startup overhead
    from avd_cli.logics.deployer import EosDeployer
    from avd_cli.logics.loader import InventoryLoader
    from avd_cli.utils.device_filter import DeviceFilter

    # ... implementation extracted from main.py
```

**Step 4-6:** Continue TDD pattern

**Step 7: Update main.py imports**

```python
# In avd_cli/cli/main.py
from avd_cli.cli.commands.deploy import deploy

# Register command group
cli.add_command(deploy)
```

**Step 8: Commit**

```bash
git add avd_cli/cli/commands/deploy.py tests/unit/cli/test_commands_deploy.py avd_cli/cli/main.py
git commit -m "refactor(cli): extract deploy command to separate module

- Create avd_cli/cli/commands/deploy.py
- Remove deploy logic from main.py (226 lines reduced)
- Add unit tests for deploy command
- Follows existing commands/ module pattern"
```

---

### Task 2.2: Consolider les commandes generate (éliminer duplication)

**Files:**
- Modify: `avd_cli/cli/main.py:255-712`
- Modify: `avd_cli/cli/commands/generate.py`
- Test: existing tests

**Objectif:** Supprimer le code dupliqué entre main.py et commands/generate.py. Garder une seule source de vérité dans commands/generate.py.

---

## Phase 3: Création d'Abstractions

### Task 3.1: Créer BaseGenerator pour les générateurs

**Files:**
- Create: `avd_cli/logics/base_generator.py`
- Modify: `avd_cli/logics/generator.py`
- Test: `tests/unit/logics/test_base_generator.py`

**Step 1: Write the failing test**

```python
# tests/unit/logics/test_base_generator.py
"""Unit tests for BaseGenerator."""
import pytest
from abc import ABC
from avd_cli.logics.base_generator import BaseGenerator


class TestBaseGenerator:
    """Test cases for BaseGenerator abstract class."""

    def test_base_generator_is_abstract(self) -> None:
        """Test that BaseGenerator cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseGenerator()

    def test_base_generator_requires_generate_method(self) -> None:
        """Test that subclasses must implement generate()."""
        class IncompleteGenerator(BaseGenerator):
            pass

        with pytest.raises(TypeError):
            IncompleteGenerator()
```

**Step 3: Write implementation**

```python
# avd_cli/logics/base_generator.py
"""Base generator abstract class."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from avd_cli.models.inventory import DeviceDefinition, InventoryData
    from avd_cli.utils.device_filter import DeviceFilter


class BaseGenerator(ABC):
    """Abstract base class for all AVD generators.

    Provides common functionality for configuration, documentation,
    and test generators.
    """

    @abstractmethod
    def generate(
        self,
        inventory: "InventoryData",
        output_path: Path,
        device_filter: Optional["DeviceFilter"] = None,
    ) -> List[Path]:
        """Generate output files from inventory.

        Parameters
        ----------
        inventory : InventoryData
            Loaded inventory data
        output_path : Path
            Directory for generated files
        device_filter : Optional[DeviceFilter], optional
            Filter to limit devices, by default None

        Returns
        -------
        List[Path]
            List of generated file paths
        """
        pass

    def _get_filtered_devices(
        self,
        inventory: "InventoryData",
        device_filter: Optional["DeviceFilter"] = None,
    ) -> List["DeviceDefinition"]:
        """Get devices from inventory, optionally filtered.

        Parameters
        ----------
        inventory : InventoryData
            Loaded inventory data
        device_filter : Optional[DeviceFilter], optional
            Filter to apply, by default None

        Returns
        -------
        List[DeviceDefinition]
            Filtered list of devices
        """
        from avd_cli.utils.device_filter import filter_devices
        return filter_devices(inventory, device_filter)
```

**Commit:**
```bash
git commit -m "refactor(logics): add BaseGenerator abstract class

- Create avd_cli/logics/base_generator.py
- Define common interface for all generators
- Extract shared _get_filtered_devices() method
- Prepares for generator inheritance refactoring"
```

---

### Task 3.2: Migrer DeviceDefinition vers Pydantic v2

**Files:**
- Modify: `avd_cli/models/inventory.py:24-172`
- Test: `tests/unit/models/test_inventory.py`

**Note:** Cette tâche est optionnelle car Pydantic est déjà une dépendance mais pas utilisé. La migration apporterait:
- Validation automatique des types
- Messages d'erreur plus clairs
- Sérialisation JSON native
- Support des schémas OpenAPI

---

## Phase 4: Amélioration des Tests

### Task 4.1: Ajouter tests pour constants.py

**Files:**
- Create: `tests/unit/test_constants.py`

```python
# tests/unit/test_constants.py
"""Unit tests for constants module."""
import pytest
from avd_cli.constants import normalize_workflow, ExitCode, DEFAULT_OUTPUT_DIR


class TestNormalizeWorkflow:
    """Test cases for workflow normalization."""

    @pytest.mark.parametrize("input_workflow,expected", [
        ("eos_design", "eos_designs"),
        ("eos-design", "eos_designs"),
        ("eos_designs", "eos_designs"),
        ("cli_config", "eos_cli_config_gen"),
        ("eos_cli_config_gen", "eos_cli_config_gen"),
    ])
    def test_normalize_known_workflows(self, input_workflow: str, expected: str) -> None:
        """Test normalization of known workflow values."""
        assert normalize_workflow(input_workflow) == expected

    def test_normalize_unknown_workflow_returns_input(self) -> None:
        """Test that unknown workflows are returned unchanged."""
        assert normalize_workflow("custom_workflow") == "custom_workflow"


class TestExitCodes:
    """Test cases for exit code constants."""

    def test_success_is_zero(self) -> None:
        """Test SUCCESS exit code is 0."""
        assert ExitCode.SUCCESS == 0

    def test_error_is_nonzero(self) -> None:
        """Test ERROR exit code is non-zero."""
        assert ExitCode.ERROR != 0
```

---

### Task 4.2: Ajouter tests pour topology.py

**Files:**
- Create: `tests/unit/logics/test_topology.py`

Focus sur les méthodes privées critiques:
- `_compute_mgmt_subnet()`
- `_build_nodes()`
- `_build_links()`
- `_normalize_startup_dir()`

---

## Vérification

**Pour chaque phase, exécuter:**

```bash
# 1. Formatage
make format

# 2. Linting
make lint

# 3. Type checking
make type

# 4. Tests avec couverture
make ci-test

# 5. Vérification complète
make ci
```

**Critères de succès:**
- Tous les tests passent (>80% couverture)
- Pylint score ≥9.0
- MyPy strict sans erreurs
- Pas de régression fonctionnelle

---

## Résumé des fichiers modifiés

| Phase | Fichiers créés | Fichiers modifiés |
|-------|---------------|-------------------|
| 1.1 | `utils/merge.py`, `tests/unit/utils/test_merge.py` | `logics/loader.py`, `logics/generator.py` |
| 1.2 | - | `utils/device_filter.py`, `logics/generator.py`, `logics/topology.py` |
| 2.1 | `cli/commands/deploy.py`, `tests/unit/cli/test_commands_deploy.py` | `cli/main.py` |
| 2.2 | - | `cli/main.py`, `cli/commands/generate.py` |
| 3.1 | `logics/base_generator.py`, `tests/unit/logics/test_base_generator.py` | `logics/generator.py` |
| 3.2 | - | `models/inventory.py` (optionnel) |
| 4.1 | `tests/unit/test_constants.py` | - |
| 4.2 | `tests/unit/logics/test_topology.py` | - |
