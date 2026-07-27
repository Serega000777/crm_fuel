import { useCallback, useEffect, useState } from "react";
import { ArrowDownToLine, ArrowUpFromLine, Fuel as FuelIcon, LoaderCircle, RefreshCw, WalletCards, X } from "lucide-react";
import { api, type Dashboard, type Fuel } from "./api";

const rub = (kopecks:number)=>new Intl.NumberFormat("ru-RU",{style:"currency",currency:"RUB",maximumFractionDigits:2}).format(kopecks/100);
type Mode = "purchase"|"sale"|"price";

function OperationSheet({mode,fuel,onClose,onDone}:{mode:Mode;fuel:Fuel;onClose:()=>void;onDone:()=>void}) {
  const [liters,setLiters]=useState(""); const [price,setPrice]=useState(mode==="price"?(fuel.sale_price_kopecks/100).toString():"");
  const [payment,setPayment]=useState("cash"); const [busy,setBusy]=useState(false); const [error,setError]=useState("");
  const title=mode==="purchase"?"Новая закупка":mode==="sale"?"Новая продажа":"Цена продажи";
  async function submit(e:React.FormEvent){e.preventDefault();setBusy(true);setError("");
    try {
      if(mode==="price") await api.price(fuel.id,Math.round(Number(price)*100));
      else if(mode==="purchase") await api.purchase({fuel_id:fuel.id,liters,unit_price_kopecks:Math.round(Number(price)*100),payment_method:payment});
      else await api.sale({fuel_id:fuel.id,liters,payment_method:payment});
      onDone(); onClose();
    } catch(e){setError(e instanceof Error?e.message:"Ошибка");} finally{setBusy(false)}
  }
  return <div className="overlay" onMouseDown={e=>e.target===e.currentTarget&&onClose()}><form className="sheet" onSubmit={submit}>
    <div className="sheetHead"><div><span className="eyebrow">{fuel.name}</span><h2>{title}</h2></div><button type="button" className="icon" onClick={onClose}><X/></button></div>
    {mode!=="price"&&<label>Количество, л<input inputMode="decimal" required min=".001" step=".001" value={liters} onChange={e=>setLiters(e.target.value.replace(",","."))} placeholder="0.000"/></label>}
    {mode!=="sale"&&<label>{mode==="purchase"?"Закупочная цена, ₽/л":"Цена продажи, ₽/л"}<input inputMode="decimal" required min=".01" step=".01" value={price} onChange={e=>setPrice(e.target.value.replace(",","."))} placeholder="0.00"/></label>}
    {mode!=="price"&&<label>Способ оплаты<select value={payment} onChange={e=>setPayment(e.target.value)}><option value="cash">Наличные</option><option value="card">Карта</option><option value="transfer">Перевод</option></select></label>}
    {mode==="sale"&&<div className="total">Итого <strong>{liters?rub(Number(liters)*fuel.sale_price_kopecks):"—"}</strong></div>}
    {error&&<div className="error">{error}</div>}<button className="primary" disabled={busy}>{busy?<LoaderCircle className="spin"/>:"Провести операцию"}</button>
  </form></div>
}

export default function App(){
  const [data,setData]=useState<Dashboard|null>(null),[error,setError]=useState(""),[active,setActive]=useState<{mode:Mode;fuel:Fuel}|null>(null);
  const load=useCallback(async()=>{try{setError("");setData(await api.dashboard())}catch(e){setError(e instanceof Error?e.message:"Ошибка загрузки")}},[]);
  useEffect(()=>{void load()},[load]);
  if(!data&&!error)return <main className="center"><LoaderCircle className="spin"/><p>Загружаем CRM Fuel…</p></main>;
  return <main><header><div><span className="brand"><FuelIcon/> CRM FUEL</span><h1>Добрый день</h1><p>Все показатели за всё время</p></div><button className="icon refresh" onClick={()=>void load()}><RefreshCw/></button></header>
    {error&&<div className="error banner">{error}<button onClick={()=>void load()}>Повторить</button></div>}
    {data&&<><section className="metrics"><article><WalletCards/><span>Выручка</span><strong>{rub(data.revenue_kopecks)}</strong></article><article><span>Валовая прибыль</span><strong className="profit">{rub(data.gross_profit_kopecks)}</strong></article><article><span>Остаток</span><strong>{Number(data.total_stock_liters).toLocaleString("ru-RU")} л</strong></article></section>
    <div className="sectionTitle"><h2>Топливо</h2><span>{data.fuels.length} позиции</span></div><section className="fuelGrid">{data.fuels.map(f=><article className="fuelCard" key={f.id} style={{"--accent":f.color} as React.CSSProperties}>
      <div className="fuelTop"><div className="fuelName"><i/ ><div><h3>{f.name}</h3><span>{rub(f.sale_price_kopecks)} / л</span></div></div><button className="priceBtn" onClick={()=>setActive({mode:"price",fuel:f})}>Цена</button></div>
      <div className="stock"><span>В резервуаре</span><strong>{Number(f.stock_liters).toLocaleString("ru-RU")} <small>л</small></strong></div>
      <div className="actions"><button onClick={()=>setActive({mode:"purchase",fuel:f})}><ArrowDownToLine/> Закупка</button><button className="sale" disabled={!f.sale_price_kopecks||Number(f.stock_liters)<=0} onClick={()=>setActive({mode:"sale",fuel:f})}><ArrowUpFromLine/> Продажа</button></div>
    </article>)}</section>
    <nav><button className="selected"><FuelIcon/>Главная</button><button onClick={()=>alert("История операций появится на следующем этапе")}><RefreshCw/>Операции</button><button onClick={()=>alert("Отчёты появятся на следующем этапе")}><WalletCards/>Отчёты</button></nav></>}
    {active&&<OperationSheet {...active} onClose={()=>setActive(null)} onDone={()=>void load()}/>}
  </main>
}

