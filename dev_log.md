# Dev Log

## [2025-10-07] Deprecated scanning colorimeter script

**Context**: Reviewing the code base, we see old scripts that use deprecated approaches
**Issue**: `scanning_colorimeter.py` creates its own postman, which was acceptable prior to creation of the DeviceManager
**Action**: Rewrite this script as a demonstration with current infrastructure
**Next Steps**
- [ ] Update `host.md` in the documention upon completion of this task

## [2025-10-07] Host testing with fake device

**Context**: Development when I don't have access to the devices
**Issue**: I'd like to try out some AI orchestration without needing access to the actual devices
**Action**: Create a fakelab - Use our understanding of the code to access commands and generate fake data
**Next Steps**
- [ ] step 1
- [ ] step 2

---

## [2025-10-07] Homing should use sequencer

**Context**: Homing state of sidekick has not bee updated since introduction of sequencing
**Issue**: Results in non-standard code
**Action**: Refactoring
**Next Steps**
- [ ] step 1
- [ ] step 2

---

