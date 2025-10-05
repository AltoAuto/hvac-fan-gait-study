import os, datetime, json

def _fmt(x, d=1):
    try: return f"{x:.{d}f}"
    except: return str(x)

def _pct(x, d=0):
    try: return f"{x:.{d}f}%"
    except: return str(x)

def _savings_vs_fixed(m, wh_fixed):
    return 100.0 * (wh_fixed - m["Wh"]) / max(wh_fixed, 1e-9)

def console_summary(metrics, title="=== SUMMARY — 1 HOUR SIMULATION ===", extras=None):
    """Pretty print to terminal."""
    whf = metrics["fixed"]["Wh"]
    lines = [title]
    lines.append(f"Fixed : {metrics['fixed']['Wh']:.1f} Wh | SFP={metrics['fixed']['SFP']:.3f} | "
                 f"Comp={metrics['fixed']['compliance_pct']:.0f}%")
    s_m = _savings_vs_fixed(metrics["modes"], whf)
    lines.append(f"Modes : {metrics['modes']['Wh']:.1f} Wh | SFP={metrics['modes']['SFP']:.3f} | "
                 f"Comp={metrics['modes']['compliance_pct']:.0f}% | "
                 f"Savings vs fixed={s_m:.0f}%")
    s_v = _savings_vs_fixed(metrics["var"], whf)
    lines.append(f"Var   : {metrics['var']['Wh']:.1f} Wh | SFP={metrics['var']['SFP']:.3f} | "
                 f"Comp={metrics['var']['compliance_pct']:.0f}% | "
                 f"Savings vs fixed={s_v:.0f}%")
    if extras:
        lines.append(extras)
    print("\n".join(lines))

def _table_rows(metrics):
    order  = ["fixed", "modes", "var"]
    labels = {"fixed":"Fixed","modes":"Mode-switch","var":"Variable"}
    whf = metrics["fixed"]["Wh"]
    rows = []
    for k in order:
        m = metrics[k]
        rows.append({
            "Strategy": labels[k],
            "Energy (Wh)": _fmt(m["Wh"],1),
            "SFP (W/CFM)": _fmt(m["SFP"],3),
            "Compliance":  _pct(m["compliance_pct"],0),
            "Delivered (CFM·h)": _fmt(m["cfmh_delivered"],1),
            "Shortfall (CFM·h)": _fmt(m["cfmh_shortfall"],1),
            "Oversupply (CFM·h)": _fmt(m["cfmh_oversupply"],1),
            "Savings vs Fixed": _fmt(_savings_vs_fixed(m, whf),0) + "%"
        })
    return rows

def build_summary_sheet(outdir, metrics, fan_spec=None, system_spec=None, sim_spec=None,
                        figs=None, fname_md="result_sheet.md", fname_html="result_sheet.html"):
    """
    Portfolio-ready one-pager: key numbers + 2–3 plots.
    figs (optional): dict keys like {"g1","g5E","g5S","g6"} mapped to image paths.
    """
    os.makedirs(outdir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = _table_rows(metrics)

    # ===== Markdown =====
    md = []
    md.append(f"# Fan Gait Switching — Result Sheet")
    md.append(f"_Generated: {ts}_\n")
    md.append("## Summary")
    whf = metrics["fixed"]["Wh"]; whm = metrics["modes"]["Wh"]; whv = metrics["var"]["Wh"]
    sav_m = _savings_vs_fixed(metrics["modes"], whf)
    sav_v = _savings_vs_fixed(metrics["var"],  whf)
    md.append(f"- Mode-switch reduces energy by **{sav_m:.0f}%** vs fixed (this run).")
    md.append(f"- Variable reduces energy by **{sav_v:.0f}%** vs fixed and achieves "
              f"**{_pct(metrics['var']['compliance_pct'])}** compliance.\n")

    md.append("## Key Results (1 hour)")
    headers = list(rows[0].keys())
    md.append("| " + " | ".join(headers) + " |")
    md.append("| " + " | ".join(["---"]*len(headers)) + " |")
    for r in rows:
        md.append("| " + " | ".join(str(r[h]) for h in headers) + " |")
    md.append("")

    if fan_spec or system_spec or sim_spec:
        md.append("## Parameters")
        params = {
            "fan": vars(fan_spec) if fan_spec else {},
            "system": vars(system_spec) if system_spec else {},
            "sim": {k:getattr(sim_spec,k) for k in dir(sim_spec) if not k.startswith('_')} if sim_spec else {}
        }
        md += ["```json", json.dumps(params, indent=2, default=str), "```", ""]

    def _img_md(title, key):
        if not figs: return
        p = figs.get(key);
        if p and os.path.exists(p):
            md.append(f"## {title}")
            md.append(f"![{title}]({os.path.relpath(p, outdir).replace(os.sep,'/')})\n")

    # include the two most impactful visuals by default
    _img_md("Energy vs Strategy (Wh, compliance)", "g5E")
    _img_md("Shortfall & Oversupply (CFM·h)", "g5S")

    md_path = os.path.join(outdir, fname_md)
    with open(md_path, "w", encoding="utf-8") as f: f.write("\n".join(md))

    # ===== HTML =====
    html = []
    html += ["<!doctype html><html><head><meta charset='utf-8'>",
             "<title>Fan Gait Switching — Result Sheet</title>",
             "<style>body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:900px;margin:32px auto;line-height:1.45}",
             "h1,h2{margin-top:1.1em} table{border-collapse:collapse} th,td{border:1px solid #ddd;padding:6px 8px}",
             "img{max-width:100%;height:auto;border:1px solid #eee;padding:4px;border-radius:6px}",
             "code,pre{background:#f6f8fa;border:1px solid #e1e4e8;padding:8px;border-radius:6px}</style></head><body>"]
    html += [f"<h1>Fan Gait Switching — Result Sheet</h1><p><em>Generated: {ts}</em></p>"]
    html += [f"<h2>Executive Summary</h2>",
             f"<ul><li>Mode-switch reduces energy by <b>{sav_m:.0f}%</b> vs fixed.</li>",
             f"<li>Variable reduces energy by <b>{sav_v:.0f}%</b> vs fixed and achieves "
             f"<b>{metrics['var']['compliance_pct']:.0f}%</b> compliance.</li></ul>"]
    # table
    html += ["<h2>Key Results (1 hour)</h2><table><thead><tr>"]
    for h in headers: html.append(f"<th>{h}</th>")
    html += ["</tr></thead><tbody>"]
    for r in rows:
        html.append("<tr>" + "".join(f"<td>{r[h]}</td>" for h in headers) + "</tr>")
    html += ["</tbody></table>"]
    # params
    if fan_spec or system_spec or sim_spec:
        html += ["<h2>Parameters</h2><pre><code>",
                 json.dumps(params, indent=2, default=str),
                 "</code></pre>"]
    # images
    def _img_html(title, key):
        if not figs: return
        p = figs.get(key);
        if p and os.path.exists(p):
            rel = os.path.relpath(p, outdir).replace(os.sep,'/')
            html.append(f"<h2>{title}</h2><img src='{rel}' alt='{title}'>")
    _img_html("Energy vs Strategy (Wh, compliance)", "g5E")
    _img_html("Shortfall & Oversupply (CFM·h)", "g5S")

    html += ["</body></html>"]
    html_path = os.path.join(outdir, fname_html)
    with open(html_path, "w", encoding="utf-8") as f: f.write("\n".join(html))
    return md_path, html_path

