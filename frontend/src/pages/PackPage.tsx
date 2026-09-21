import { useEffect, useState } from "react";
import { api } from "../api/client";
import { CATEGORY_LABEL, Category, categoryClass } from "../categories";
type R = { id: number; name: string };
type Item = { stop_name: string; category: Category };
type Bag = { id: number; bag_index: number; weight_kg: number; volume_l: number; items: Item[] };
type Rj = { id: number; stop_name: string; reason: string };
export default function PackPage() {
  const [routes, setRoutes] = useState<R[]>([]);
  const [rid, setRid] = useState<number | "">("");
  const [bags, setBags] = useState<Bag[]>([]);
  const [rejects, setRejects] = useState<Rj[]>([]);
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  useEffect(() => { api<R[]>("/routes").then(r => { setRoutes(r); if (r[0]) setRid(r[0].id); }); }, []);
  async function run() {
    setMsg(""); setErr("");
    try {
      const out = await api<Bag[]>("/pack", { method: "POST", body: JSON.stringify({ route_id: rid }) });
      setBags(out);
      const rj = await api<Rj[]>(`/rejects?route_id=${rid}`);
      setRejects(rj);
      setMsg(`完成装袋：${out.length} 袋${rj.length ? `，拒收 ${rj.length} 单（与拒收页一致）` : "，无拒收"}`);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>装袋</h2>
    <div className="toolbar">
      <select value={rid} onChange={e => setRid(Number(e.target.value))}>{routes.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
      <button onClick={run}>按路线顺序双约束装袋</button>
    </div>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    {bags.map(b => (
      <div key={b.id}>
        <div className="mono">袋 {b.bag_index} · {b.weight_kg}kg / {b.volume_l}L</div>
        <div className="bag-row">{b.items.map((it, i) => (
          <div className={`bag-block bag-block--${it.category}`} key={i}>
            <span className={categoryClass(it.category)}>{CATEGORY_LABEL[it.category]}</span>
            {it.stop_name}
          </div>
        ))}</div>
      </div>
    ))}
    {rejects.length > 0 && (
      <>
        <h3>本路线拒收（与拒收页一致）</h3>
        <table className="table"><thead><tr><th>订户</th><th>原因</th></tr></thead>
          <tbody>{rejects.map(r => <tr key={r.id}><td>{r.stop_name}</td><td className="err">{r.reason}</td></tr>)}</tbody>
        </table>
      </>
    )}
  </>);
}
