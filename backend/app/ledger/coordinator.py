"""Coordinates local ledger writes; persistence and concurrency are pending."""

class LedgerCoordinator:
    def append_event(self, event: dict):
        raise NotImplementedError("Member C: define append semantics and persistence.")
