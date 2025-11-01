async function fetchWallets() {
  const res = await fetch("http://localhost:8000/v1/wallets", { cache: "no-store" });
  if (!res.ok) throw new Error("API error");
  return res.json();
}

export default async function Home() {
  const wallets = await fetchWallets();
  return (
    <main style={{padding:24, fontFamily:"ui-sans-serif"}}>
      <h1 style={{fontSize:28, marginBottom:12}}>Oculus — Copy Wallets</h1>
      <table style={{borderCollapse:"collapse", width:"100%"}}>
        <thead>
          <tr>
            <th style={{textAlign:"left", borderBottom:"1px solid #ddd", padding:"8px"}}>Label</th>
            <th style={{textAlign:"left", borderBottom:"1px solid #ddd", padding:"8px"}}>Status</th>
          </tr>
        </thead>
        <tbody>
          {wallets.map((w:any)=>(
            <tr key={w.id}>
              <td style={{padding:"8px", borderBottom:"1px solid #f0f0f0"}}>{w.label}</td>
              <td style={{padding:"8px", borderBottom:"1px solid #f0f0f0"}}>{w.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
