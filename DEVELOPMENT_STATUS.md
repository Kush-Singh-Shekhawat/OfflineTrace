# Development Status

**Current phase:** Repository scaffold / interface agreement.

## Status by area

| Area | Owner | Status | Next step |
|---|---|---|---|
| Cryptography and key management | Member A | Scaffold | Agree algorithms, threat model, interfaces |
| Recipient screen | Member A | Scaffold | Build recipient/key metadata UI |
| PDF watermarking | Member B | Scaffold | Select embedding/extraction approach and test PDFs |
| Investigation screen | Member B | Scaffold | Build upload and result UI |
| FastAPI and API contracts | Member C | Scaffold | Wire routes and schemas |
| Ledger | Member C | Scaffold | Define event schema and verification rules |
| Shared React integration | Member C | Scaffold | Integrate feature screens and navigation |
| Automated tests | All | Scaffold | Add unit/integration/security coverage |

## Integration checklist

- [ ] All members use the same repository and branch naming convention.
- [ ] API contracts are agreed before parallel implementation.
- [ ] Each member commits only their assigned files plus agreed shared changes.
- [ ] Feature branches are merged through pull requests.
- [ ] Backend imports and frontend build work from a clean checkout.
- [ ] Offline demo check passes.
- [ ] Test report and demo instructions are updated.

Update this file whenever ownership, status, blockers, or integration decisions change.
