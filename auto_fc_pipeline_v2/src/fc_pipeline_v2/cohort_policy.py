"""Study-qualified documented inclusion decisions, separate from numerical QC."""
from pathlib import Path
import json

DEFAULT_POLICY = Path(__file__).resolve().parents[2] / 'extra_data_pipeline/participant_policy.json'


def participant_decision(participant, policy_path=DEFAULT_POLICY):
    policy = json.loads(Path(policy_path).read_text(encoding='utf-8'))
    return policy['participants'].get(participant, {'action': 'retain', 'basis': 'No explicit exclusion in this PCD-only policy'})


def is_excluded(participant, policy_path=DEFAULT_POLICY):
    return participant_decision(participant, policy_path)['action'] == 'exclude'
