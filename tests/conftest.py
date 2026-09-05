from __future__ import annotations

import sys

import pytest


@pytest.fixture(autouse=True)
def forget_registered_workspaces():
    """
    Drop kash's workspace registry between tests, so one test cannot read another's items.

    kash registers a workspace under its directory *name* and, on the next request for
    that name, hands back the base directory registered first, ignoring the path it was
    given. Every real run puts its workspace at `<--workspace>/workspace`, so two tests
    that each drive a real run through `main()` both ask for the name "workspace" and the
    second silently gets the first one's files. That is dt-565k, and it is invisible: the
    symptom is a test that passes against a broken change because the item it expected to
    be absent was sitting in the other test's workspace.

    Clearing the name map is enough. The `FileStore` behind each directory stays cached,
    so re-registering the same path costs nothing.
    """
    yield
    module = sys.modules.get("kash.workspaces.workspace_registry")
    if module is None:
        # The test never touched kash, so there is nothing registered and importing it
        # here would only slow every test in the suite down.
        return
    module.get_ws_registry()._workspaces.clear()  # pyright: ignore[reportPrivateUsage]
