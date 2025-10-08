# Dev Log

## [2025-10-08] Rename and organize host_app

**Context**: The three main structures of the program are messaging (communicate), devices (firmware) and the host (host_app).
**Issue**: Renaming host_app to host and reorganizing to have utilities, gui, core, etc may be helpful for future proofing
**Action**: move host_utilities in here, check that all dependencies are updated
- [X] Rename host_app to host
- [X] Deal with all the crap that appears because of ^^^
- [X] test updates

---

## [2025-10-08] Assumptions should be included in documentation

**Context**: Hardware/software design assumptions need to be clear for new developers
**Issue**: Is it obvious that microcontrollers must use CP at this point?
**Action**: Include in documentation some clear assumptions
**Next Steps**:
- [ ] Write an executive summary for the design protocols with asusumptions
- [ ] Identify what belongs in a _Getting Started_ section.

---

## [2025-10-07] Deprecated scanning colorimeter script

**Context**: Reviewing the code base, we see old scripts that use deprecated approaches
**Issue**: `scanning_colorimeter.py` creates its own postman, which was acceptable prior to creation of the DeviceManager
**Action**: Rewrite this script as a demonstration with current infrastructure
**Next Steps**
- [ ] Update `host.md` in the documention upon completion of this task

---

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

