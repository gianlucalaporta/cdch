import pandas as pd
import numpy as np

def build_cdchi(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    ID_CITY, ID_STATE = 'PlaceName', 'StateAbbr'
    vars_pref = ['OBESITY_AdjPrev','DIABETES_AdjPrev','BPHIGH_AdjPrev','COPD_AdjPrev','PHLTH_AdjPrev','LPA_AdjPrev']
    def resolve_vars(df, names):
        out=[]
        for v in names:
            if v in df.columns:
                out.append(v)
            elif v.endswith('_AdjPrev') and v.replace('_AdjPrev','_CrudePrev') in df.columns:
                out.append(v.replace('_AdjPrev','_CrudePrev'))
        return out
    use_vars = resolve_vars(df, vars_pref)
    work = df[[ID_CITY, ID_STATE] + use_vars].copy()
    for c in use_vars:
        work[c] = pd.to_numeric(work[c], errors='coerce')
    Z = work[use_vars].apply(lambda s: (s - s.mean(skipna=True)) / s.std(ddof=0, skipna=True))
    for c in use_vars:
        work[f'Z_{c}'] = Z[c]
    CARDIO = [c for c in ['Z_OBESITY_AdjPrev','Z_DIABETES_AdjPrev','Z_BPHIGH_AdjPrev'] if c in work.columns]
    RESP   = [c for c in ['Z_COPD_AdjPrev','Z_SMOKING_AdjPrev'] if c in work.columns]
    BEHAV  = [c for c in ['Z_LPA_AdjPrev','Z_PHLTH_AdjPrev'] if c in work.columns]
    def mean_or_nan(df, cols):
        return df[cols].mean(axis=1) if cols else np.nan
    work['domain_cardio'] = mean_or_nan(work, CARDIO)
    work['domain_resp']   = mean_or_nan(work, RESP)
    work['domain_behav']  = mean_or_nan(work, BEHAV)
    work['score_raw'] = work[['domain_cardio','domain_resp','domain_behav']].mean(axis=1)
    v = work['score_raw'].values.astype(float)
    vmin, vmax = np.nanmin(v), np.nanmax(v)
    work['CDCHI'] = 100 * (v - vmin) / (vmax - vmin) if vmax>vmin else 50.0
    cols = ['PlaceName','StateAbbr','CDCHI','domain_cardio','domain_resp','domain_behav']
    return work[cols].sort_values('CDCHI', ascending=False)

if __name__ == '__main__':
    import argparse, pathlib
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True, help='path al CSV 500 Cities')
    ap.add_argument('--output', default='outputs/cdchi_final.csv', help='dove salvare l\'output')
    args = ap.parse_args()
    df_out = build_cdchi(args.input)
    pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(args.output, index=False)
    print('Salvato:', args.output)