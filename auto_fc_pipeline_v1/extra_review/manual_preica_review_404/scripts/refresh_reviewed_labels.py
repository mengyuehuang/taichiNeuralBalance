"""Classify the refitted model using only complete, retained two-second epochs."""
import os
os.environ['MNE_USE_NUMBA']='false'
os.environ['MPLBACKEND']='Agg'
from pathlib import Path
import importlib.util
import json
import sys
HERE=Path(__file__).resolve().parents[1]
ROOT=HERE.parents[1]
OUT=HERE/'outputs/Selected_158s'
os.environ['_MNE_FAKE_HOME_DIR']=str(ROOT.parent/'.mne_fake_home')
sys.path.insert(0,str(ROOT/'src'))
import mne
from mne_icalabel import label_components
spec=importlib.util.spec_from_file_location('ica_runner',ROOT/'scripts/04_run_ica.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
raw=mne.io.read_raw_fif(OUT/'PreICA/404_HC4_preica_raw.fif',preload=True)
raw.set_eeg_reference('average',projection=False)
ica=mne.preprocessing.read_ica(OUT/'ICA/404_HC4-ica.fif')
epochs=mne.make_fixed_length_epochs(raw,duration=2,preload=True,reject_by_annotation=True)
result=label_components(epochs,ica,method='iclabel')
config=json.loads((OUT/'config.json').read_text())
table=module.build_review_table(list(result['labels']),list(result['y_pred_proba']),config['ica'])
table['label_input']='Retained complete 2-second epochs only; 1-55 Hz input; automatic suggestions only'
path=OUT/'ICA_Review/404/404_HC4_ica_review.csv'
table.to_csv(path,index=False)
module.save_review_workbook(table,path,config['ica'])
status=json.loads((OUT/'run_status.json').read_text())
status.update(label_input_epochs=len(epochs),label_input_seconds=len(epochs)*2,label_input_policy='Complete retained 2-second epochs, no BAD samples or gap concatenation')
(OUT/'run_status.json').write_text(json.dumps(status,indent=2))
print(json.dumps(status,indent=2))
