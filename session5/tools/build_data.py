"""
build_data.py — session5/harness/data 3종 생성 (강사용, 재현 가능)

입력 (레포 밖, 미리 클론):
  SHIU  = philshiu/Drosophila_brain_model  → Connectivity_783.parquet, Completeness_783.csv
  ANNOT = flyconnectome/flywire_annotations → supplemental_files/Supplemental_file1_neuron_annotations.tsv
출력:
  OUT/connections.parquet  (pre, post, syn, sign)  시냅스 >= 5
  OUT/neurons.csv.gz       (index, root_id, 주석 컬럼)
  OUT/groups.json          (그룹 이름 -> index 목록)
  OUT/BUILD_REPORT.md      (실측값 — DATA.md 에 옮겨 적는다)

사용: python build_data.py <SHIU_DIR> <ANNOT_DIR> <OUT_DIR>
"""
import json, os, sys, time
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

MIN_SYN = 5
W_UNIT_MV = 0.275

def main(shiu, annot, out):
    t0 = time.time()
    os.makedirs(out, exist_ok=True)
    rep = []

    # ---------- 1) 뉴런 목록(인덱스 순서) ----------
    comp = pd.read_csv(os.path.join(shiu, "Completeness_783.csv"))
    comp.columns = ["root_id", "completed"]
    root_ids = comp["root_id"].to_numpy(dtype=np.int64)
    N = len(root_ids)
    assert len(np.unique(root_ids)) == N, "root_id 중복"
    rep.append(f"- 뉴런 수 N = {N:,} (Completeness_783.csv 행 수)")

    # ---------- 2) 연결 원본 ----------
    cols = ["Presynaptic_ID", "Postsynaptic_ID", "Presynaptic_Index", "Postsynaptic_Index", "Connectivity", "Excitatory"]
    raw = pq.read_table(os.path.join(shiu, "Connectivity_783.parquet"), columns=cols).to_pandas()
    rep.append(f"- 원본 연결 행 수 = {len(raw):,}, 총 시냅스 = {int(raw.Connectivity.sum()):,}")

    # 인덱스 ↔ root_id 매핑이 Completeness 순서와 같은지 검증
    pre_map = raw.drop_duplicates("Presynaptic_Index")[["Presynaptic_Index", "Presynaptic_ID"]].to_numpy()
    post_map = raw.drop_duplicates("Postsynaptic_Index")[["Postsynaptic_Index", "Postsynaptic_ID"]].to_numpy()
    ok_pre = bool(np.all(root_ids[pre_map[:, 0]] == pre_map[:, 1]))
    ok_post = bool(np.all(root_ids[post_map[:, 0]] == post_map[:, 1]))
    assert ok_pre and ok_post, "인덱스 순서가 Completeness 와 다름"
    assert raw.Presynaptic_Index.min() >= 0 and raw.Presynaptic_Index.max() < N
    assert raw.Postsynaptic_Index.min() >= 0 and raw.Postsynaptic_Index.max() < N
    rep.append("- 인덱스 ↔ root_id: Completeness_783.csv 행 순서 = 인덱스 (pre/post 모두 검증 통과)")
    assert set(raw.Excitatory.unique()) <= {1, -1}, "부호 값 이상"

    # ---------- 3) 슬림 연결 ----------
    sl = raw[raw.Connectivity >= MIN_SYN]
    conn = pd.DataFrame({
        "pre": sl.Presynaptic_Index.to_numpy(np.int32),
        "post": sl.Postsynaptic_Index.to_numpy(np.int32),
        "syn": sl.Connectivity.to_numpy(np.int16),
        "sign": sl.Excitatory.to_numpy(np.int8),
    }).sort_values(["post", "pre"], kind="stable").reset_index(drop=True)
    assert conn.syn.max() < 32767
    dup = conn.duplicated(["pre", "post"]).sum()
    assert dup == 0, f"(pre, post) 중복 {dup}"
    p = os.path.join(out, "connections.parquet")
    pq.write_table(pa.Table.from_pandas(conn, preserve_index=False), p, compression="zstd")
    n_pre, n_post = conn.pre.nunique(), conn.post.nunique()
    rep.append(f"- connections.parquet: {len(conn):,} 행 (시냅스 ≥ {MIN_SYN}), 크기 {os.path.getsize(p)/1e6:.1f} MB, (pre,post) 중복 0")
    rep.append(f"  · 부호: +1 {int((conn.sign==1).sum()):,} 행 / −1 {int((conn.sign==-1).sum()):,} 행; syn 최대 {int(conn.syn.max())}; 총 시냅스 {int(conn.syn.sum()):,}")
    rep.append(f"  · 프리시냅스 뉴런 {n_pre:,}개, 포스트시냅스 뉴런 {n_post:,}개")

    # ---------- 4) 주석 결합 ----------
    a = pd.read_csv(os.path.join(annot, "supplemental_files", "Supplemental_file1_neuron_annotations.tsv"), sep="\t", low_memory=False)
    keep = ["root_id", "super_class", "cell_class", "cell_sub_class", "cell_type", "hemibrain_type", "side", "top_nt"]
    a = a[keep].drop_duplicates("root_id")
    idx_of = pd.Series(np.arange(N), index=root_ids)
    a = a[a.root_id.isin(idx_of.index)].copy()
    a["index"] = idx_of.loc[a.root_id].to_numpy()
    neurons = pd.DataFrame({"index": np.arange(N), "root_id": root_ids})
    neurons = neurons.merge(a.drop(columns=["root_id"]), on="index", how="left")
    neurons = neurons[["index", "root_id"] + keep[1:]]
    p2 = os.path.join(out, "neurons.csv.gz")
    neurons.to_csv(p2, index=False, compression="gzip")
    n_annot = int(neurons.cell_type.notna().sum())
    rep.append(f"- neurons.csv.gz: {N:,} 행, 주석 매칭 {len(a):,}개(annotations 139,248 중), cell_type 있는 뉴런 {n_annot:,}개, 크기 {os.path.getsize(p2)/1e6:.1f} MB")

    # ---------- 5) 그룹 ----------
    def by_type(ct, side):
        m = (neurons.cell_type == ct) & (neurons.side == side)
        return sorted(int(i) for i in neurons.loc[m, "index"])
    def by_subclass(sc):
        m = neurons.cell_sub_class == sc
        return sorted(int(i) for i in neurons.loc[m, "index"])
    groups = {
        "LPLC2_L": by_type("LPLC2", "left"), "LPLC2_R": by_type("LPLC2", "right"),
        "LC4_L": by_type("LC4", "left"), "LC4_R": by_type("LC4", "right"),
        "GF_L": by_type("DNp01", "left"), "GF_R": by_type("DNp01", "right"),
        "sugar_GRN": by_subclass("sugar/water"), "bitter_GRN": by_subclass("bitter"),
        "ingestion_MN": by_subclass("ingestion_motor_neuron"),
    }
    for k, v in groups.items():
        assert len(v) > 0, f"그룹 비어 있음: {k}"
    with open(os.path.join(out, "groups.json"), "w", encoding="utf-8") as f:
        json.dump(groups, f, indent=1)
    rep.append("- groups.json 그룹별 개수: " + ", ".join(f"{k} {len(v)}" for k, v in groups.items()))
    # GF 로 들어오는 LPLC2/LC4 입력 시냅스 합 (도망 회로 배선 확인용)
    W = conn.set_index(["pre", "post"])["syn"]
    for g in ["GF_L", "GF_R"]:
        gi = groups[g][0]
        sub = conn[conn.post == gi]
        tot = int(sub.syn.sum()); n_in = len(sub)
        def insum(src): return int(sub[sub.pre.isin(groups[src])].syn.sum())
        rep.append(f"  · {g}(index {gi}): 입력 연결 {n_in}개, 입력 시냅스 합 {tot:,}; LPLC2_L {insum('LPLC2_L')}, LPLC2_R {insum('LPLC2_R')}, LC4_L {insum('LC4_L')}, LC4_R {insum('LC4_R')}")
    # MN9 후보 세부
    mn = neurons[neurons.cell_sub_class == "ingestion_motor_neuron"]
    rep.append("  · ingestion_motor_neuron 의 cell_type 분포: " + str(mn.cell_type.value_counts(dropna=False).to_dict()))

    total_mb = sum(os.path.getsize(os.path.join(out, f)) for f in ["connections.parquet", "neurons.csv.gz", "groups.json"]) / 1e6
    rep.append(f"- data/ 합계 {total_mb:.1f} MB; 생성 소요 {time.time()-t0:.0f} s")
    with open(os.path.join(out, "BUILD_REPORT.md"), "w", encoding="utf-8") as f:
        f.write("# BUILD_REPORT — session5/harness/data 실측\n\n" + "\n".join(rep) + "\n")
    print("\n".join(rep))

if __name__ == "__main__":
    main(*sys.argv[1:4])
