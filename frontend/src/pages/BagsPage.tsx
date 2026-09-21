import { useEffect, useState } from "react";
import { api } from "../api/client";
import { CATEGORY_LABEL, Category, categoryClass } from "../categories";
type Item = { stop_name: string; weight_kg: number; volume_l: number; category: Category };
type Bag = { id: number; route_id: number; bag_index: number; weight_kg: number; volume_l: number; items: Item[] };
function bagCategories(items: Item[]): Category[] {
  const present = new Set(items.map(i => i.category));
  return (["printed", "liquid", "normal"] as Category[]).filter(c => present.has(c));
}
export default function BagsPage() {
  const [rows, setRows] = useState<Bag[]>([]);
  useEffect(() => { api<Bag[]>("/bags").then(setRows); }, []);
  return (<>
    <h2>袋明细</h2>
    <table className="table"><thead><tr><th>路线</th><th>袋号</th><th>袋内品类</th><th>重量</th><th>体积</th><th>订户</th></tr></thead>
    <tbody>{rows.map(b => <tr key={b.id}><td>{b.route_id}</td><td>{b.bag_index}</td>
      <td>{bagCategories(b.items).map(c => <span key={c} className={categoryClass(c)}>{CATEGORY_LABEL[c]}</span>)}</td>
      <td className="mono">{b.weight_kg}</td><td className="mono">{b.volume_l}</td>
      <td>{b.items.map((i, k) => (
        <span className="bag-item-cat" key={k}>
          <span className={categoryClass(i.category)}>{CATEGORY_LABEL[i.category]}</span>{i.stop_name}{k < b.items.length - 1 ? " → " : ""}
        </span>
      ))}</td></tr>)}
      {!rows.length && <tr><td colSpan={6}>尚无装袋结果，请先执行装袋</td></tr>}
    </tbody></table>
  </>);
}
