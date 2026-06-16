# AGENTS.md

This workspace is for the SURF posture detection project only.

## Collaboration Rules

1. Confirm technical details with the user before implementation when the choice affects scope, architecture, evaluation, or deliverables.
2. For any code change, identify and run the full available test and validation flow before closing the task.
3. For docs-only or structure-only changes, perform integrity checks instead of code tests. At minimum, verify file existence, content completeness, and expected directory layout.
4. Keep all solutions compatible with the China mainland environment and avoid VPN-dependent requirements.
5. Preserve the original provided materials in the parent workspace. Do not destructively reorganize or overwrite them.
6. The current project scope is standing posture detection with side-view priority. Do not expand to sitting posture unless the user explicitly changes the scope.
7. Prefer full-body images and keypoint-based posture logic centered on ear, shoulder, torso, hip, knee, and related alignment checks.
8. Keep project notes in `docs/`, copied source materials in `references/`, experiment records in `experiments/`, and presentation assets in `deliverables/`.
9. If no automated test suite exists for a future code task, run the fullest available manual or scripted validation flow and clearly report the gap.
10. Do not move or duplicate the large raw dataset unless the user explicitly asks for it.

## Current Bootstrap Contents

- `docs/meeting-01-requirements.md`: Chinese summary of the first project meeting.
- `references/`: copied lightweight reference materials and figures from the provided assets.
- `experiments/`: reserved for training logs, trial notes, and model comparisons.
- `deliverables/`: reserved for poster drafts, slides, and other final outputs.
