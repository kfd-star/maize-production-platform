import sys
import json
import pathlib
import importlib.util
import os
import glob
import pandas as pd


def load_module_by_path(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    # argv: algo obs_path [params_json]
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "missing args"}), flush=True)
        return 2
    algo = sys.argv[1]
    obs_path = sys.argv[2]
    params_json = sys.argv[3] if len(sys.argv) > 3 else None
    try:
        # resolve project root (this file lives in app-py/)
        base_dir = pathlib.Path(__file__).resolve().parent
        utils_dir = base_dir / 'utils'
        
        # 解析参数
        params = {}
        if params_json:
            try:
                params = json.loads(params_json)
            except json.JSONDecodeError as e:
                print(json.dumps({"ok": False, "error": f"参数解析失败: {e}"}), flush=True)
                return 3
        
        # 将算法过程中的print输出重定向到stderr，保证stdout仅输出一条JSON
        old_stdout = sys.stdout
        try:
            sys.stdout = sys.stderr
            if algo == 'EnKF':
                mod = load_module_by_path('MaizeSM_EnKF_mod', str(utils_dir / 'MaizeSM_EnKF.py'))
                out_dir = mod.run_MaizeSM_EnKf(
                    obs_csv_path=obs_path,
                    en_num=params.get('en_num', 25),
                    err_lai_o_value=params.get('err_lai_o', 0.01),
                    err_lai_value=params.get('err_lai', 1.28)
                )
            elif algo == 'UKF':
                mod = load_module_by_path('MaizeSM_UKF_mod', str(utils_dir / 'MaizeSM_UKF.py'))
                out_dir = mod.run_MaizeSM_UKF(
                    obs_csv_path=obs_path,
                    en_num=params.get('en_num', 1),
                    alpha=params.get('alpha', 4.0),
                    beta=params.get('beta', 1.0),
                    kappa=params.get('kappa', 0.0),
                    err_lai_o_value=params.get('err_lai_o', 2.0),
                    err_lai_value=params.get('err_lai', 0.5)
                )
            elif algo == 'PF':
                mod = load_module_by_path('MaizeSM_PF_mod', str(utils_dir / 'MaizeSM_pf.py'))
                out_dir = mod.run_MaizeSM_PF(
                    obs_csv_path=obs_path,
                    en_num=params.get('en_num', 40),
                    resample_threshold=params.get('resample_threshold', 30),
                    noise_std=params.get('noise_std', 0.15)
                )
            elif algo == 'NLS4DVar':
                mod = load_module_by_path('MaizeSM_NLS4DVAR_mod', str(utils_dir / 'MaizeSM_NLS-4DVAR.py'))
                out_dir = mod.run_MaizeSM_NLS4DVar(
                    obs_csv_path=obs_path,
                    b_time_steps=params.get('b_time_steps', 35),
                    time_steps=params.get('time_steps', 90),
                    en_num=params.get('en_num', 25),
                    i_max=params.get('i_max', 13),
                    R_scalar=params.get('R_scalar', 0.01),
                    nass=params.get('nass', 1)
                )
            else:
                raise ValueError(f"unsupported algo: {algo}")
        finally:
            sys.stdout = old_stdout

        # 汇总输出目录下的所有 CSV 为 JSON
        result = {"_output_dir": out_dir}
        try:
            csv_files = glob.glob(os.path.join(out_dir, "*.csv"))
            def _rank(p):
                n = os.path.basename(p)
                if "主要输出结果汇总" in n:
                    return (0, n)
                if "详细输出结果" in n:
                    return (1, n)
                return (2, n)
            csv_files.sort(key=_rank)
            for csv_path in csv_files:
                name = os.path.basename(csv_path)
                try:
                    df = pd.read_csv(csv_path, dtype=object, keep_default_na=True)
                    result[name] = df.to_dict(orient="records")
                except Exception as e:
                    result[name] = {"error": str(e)}
        except Exception:
            pass

        print(json.dumps({"ok": True, "data": result}, ensure_ascii=False), flush=True)
        return 0
    except Exception as e:
        # 确保错误也仅通过stdout输出JSON（算法logs已在stderr）
        try:
            print(json.dumps({"ok": False, "error": str(e)}), flush=True)
        except Exception:
            # 兜底
            sys.__stdout__.write(json.dumps({"ok": False, "error": "unknown error"}) + "\n")
            sys.__stdout__.flush()
        return 1


if __name__ == '__main__':
    sys.exit(main())


