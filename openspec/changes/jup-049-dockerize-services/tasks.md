## 1. Reconcile inherited Docker coverage

- [x] 1.1 JUP-049 inventory every application and infrastructure service
- [x] 1.2 JUP-049 reproduce the clean frontend image build failure
- [x] 1.3 JUP-049 refine Trello scope, dependencies and rotating roles

## 2. Complete the container baseline

- [x] 2.1 JUP-049 pin application and infrastructure image inputs by digest
- [x] 2.2 JUP-049 build the frontend with pnpm 9 and the frozen workspace lockfile
- [x] 2.3 JUP-049 run application images as non-root with healthchecks
- [x] 2.4 JUP-049 add read-only filesystems, init and no-new-privileges in Compose
- [x] 2.5 JUP-049 add automated topology validation to the existing CI context

## 3. Validate and publish

- [x] 3.1 JUP-049 run repository and strict OpenSpec validation
- [ ] 3.2 JUP-049 build all images and pass an isolated health smoke on dockerserver
- [ ] 3.3 JUP-049 publish a pull request toward develop and pass remote CI
- [ ] 3.4 JUP-049 obtain pairing, review and functional validation evidence
