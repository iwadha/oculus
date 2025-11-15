export const fmt = {
pct(n?: number | null, dp = 2) { return n == null ? "—" : `${n.toFixed(dp)}%`; },
num(n?: number | null, dp = 2) { return n == null ? "—" : n.toFixed(dp); },
int(n?: number | null) { return n == null ? "—" : new Intl.NumberFormat().format(Math.round(n)); },
time(s: string | number | Date) {
const d = new Date(s);
return d.toLocaleTimeString();
},
};