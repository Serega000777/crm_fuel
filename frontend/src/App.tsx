import { useCallback, useEffect, useState } from "react";
import {
  ArrowDownToLine,
  ArrowUpFromLine,
  Banknote,
  Fuel as FuelIcon,
  History,
  LoaderCircle,
  ReceiptText,
  RefreshCw,
  RotateCcw,
  WalletCards,
  X,
} from "lucide-react";
import { api, parseKopecks, type Dashboard, type Fuel, type Operation } from "./api";

const rub = (value: number) =>
  new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB" }).format(value / 100);
type FuelMode = "purchase" | "sale" | "price";
type CashMode = "expense" | "collection";

function FuelSheet({
  mode,
  fuel,
  onClose,
  onDone,
}: {
  mode: FuelMode;
  fuel: Fuel;
  onClose: () => void;
  onDone: () => void;
}) {
  const [liters, setLiters] = useState(""),
    [price, setPrice] = useState(
      mode === "price" ? (fuel.sale_price_kopecks / 100).toString() : "",
    ),
    [payment, setPayment] = useState("cash"),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const title =
    mode === "purchase" ? "Новая закупка" : mode === "sale" ? "Новая продажа" : "Цена продажи";
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "price") await api.price(fuel.id, parseKopecks(price));
      else if (mode === "purchase")
        await api.purchase({
          fuel_id: fuel.id,
          liters,
          unit_price_kopecks: parseKopecks(price),
          payment_method: payment,
        });
      else await api.sale({ fuel_id: fuel.id, liters, payment_method: payment });
      onDone();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="overlay">
      <form className="sheet" onSubmit={submit}>
        <div className="sheetHead">
          <div>
            <span className="eyebrow">{fuel.name}</span>
            <h2>{title}</h2>
          </div>
          <button type="button" className="icon" onClick={onClose}>
            <X />
          </button>
        </div>
        {mode !== "price" && (
          <label>
            Количество, л
            <input
              inputMode="decimal"
              required
              min=".001"
              step=".001"
              value={liters}
              onChange={(e) => setLiters(e.target.value.replace(",", "."))}
            />
          </label>
        )}
        {mode !== "sale" && (
          <label>
            {mode === "purchase" ? "Закупочная цена, ₽/л" : "Цена продажи, ₽/л"}
            <input
              inputMode="decimal"
              required
              min=".01"
              step=".01"
              value={price}
              onChange={(e) => setPrice(e.target.value.replace(",", "."))}
            />
          </label>
        )}
        {mode !== "price" && (
          <label>
            Способ оплаты
            <select value={payment} onChange={(e) => setPayment(e.target.value)}>
              <option value="cash">Наличные</option>
              <option value="card">Карта</option>
              <option value="transfer">Перевод</option>
            </select>
          </label>
        )}
        {mode === "sale" && (
          <div className="total">
            Итого <strong>{liters ? rub(Number(liters) * fuel.sale_price_kopecks) : "—"}</strong>
          </div>
        )}
        {error && <div className="error">{error}</div>}
        <button className="primary" disabled={busy}>
          {busy ? <LoaderCircle className="spin" /> : "Провести операцию"}
        </button>
      </form>
    </div>
  );
}

function CashSheet({
  mode,
  cash,
  onClose,
  onDone,
}: {
  mode: CashMode;
  cash: number;
  onClose: () => void;
  onDone: () => void;
}) {
  const [amount, setAmount] = useState(mode === "collection" ? (cash / 100).toFixed(2) : ""),
    [description, setDescription] = useState(mode === "collection" ? "Инкассация" : ""),
    [payment, setPayment] = useState("cash"),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const amount_kopecks = parseKopecks(amount);
      if (mode === "expense")
        await api.expense({ amount_kopecks, description, payment_method: payment });
      else await api.collect({ amount_kopecks, description });
      onDone();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="overlay">
      <form className="sheet" onSubmit={submit}>
        <div className="sheetHead">
          <div>
            <span className="eyebrow">КАССА {rub(cash)}</span>
            <h2>{mode === "expense" ? "Новый расход" : "Инкассация"}</h2>
          </div>
          <button type="button" className="icon" onClick={onClose}>
            <X />
          </button>
        </div>
        <label>
          Сумма, ₽
          <input
            inputMode="decimal"
            required
            min=".01"
            step=".01"
            value={amount}
            onChange={(e) => setAmount(e.target.value.replace(",", "."))}
          />
        </label>
        <label>
          Описание
          <input
            required
            minLength={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        {mode === "expense" && (
          <label>
            Способ оплаты
            <select value={payment} onChange={(e) => setPayment(e.target.value)}>
              <option value="cash">Наличные</option>
              <option value="card">Карта</option>
              <option value="transfer">Перевод</option>
            </select>
          </label>
        )}
        {error && <div className="error">{error}</div>}
        <button className="primary" disabled={busy}>
          {busy ? (
            <LoaderCircle className="spin" />
          ) : mode === "expense" ? (
            "Добавить расход"
          ) : (
            "Провести инкассацию"
          )}
        </button>
      </form>
    </div>
  );
}

const labels: Record<string, string> = {
  purchase: "Закупка",
  sale: "Продажа",
  expense: "Расход",
  collection: "Инкассация",
  reversal: "Отмена",
};
function HistoryView({
  items,
  onReverse,
}: {
  items: Operation[];
  onReverse: (item: Operation) => void;
}) {
  if (!items.length)
    return (
      <div className="empty">
        <History />
        <h3>Операций пока нет</h3>
        <p>Закупки, продажи и движения кассы появятся здесь.</p>
      </div>
    );
  const reversed = new Set(items.filter((i) => i.reversal_of_id).map((i) => i.reversal_of_id));
  return (
    <section className="history">
      {items.map((item) => (
        <article key={item.id}>
          <div className={`opIcon ${item.type}`}>
            <History />
          </div>
          <div className="opBody">
            <strong>{labels[item.type] || item.type}</strong>
            <span>{item.description || new Date(item.created_at).toLocaleString("ru-RU")}</span>
          </div>
          <div className="opAmount">
            <strong>{rub(item.total_kopecks)}</strong>
            {item.type !== "reversal" && !reversed.has(item.id) && (
              <button title="Отменить" onClick={() => onReverse(item)}>
                <RotateCcw />
              </button>
            )}
          </div>
        </article>
      ))}
    </section>
  );
}

export default function App() {
  const [data, setData] = useState<Dashboard | null>(null),
    [operations, setOperations] = useState<Operation[]>([]),
    [error, setError] = useState(""),
    [active, setActive] = useState<{ mode: FuelMode; fuel: Fuel } | null>(null),
    [cashMode, setCashMode] = useState<CashMode | null>(null),
    [tab, setTab] = useState<"home" | "operations">("home");
  const load = useCallback(async () => {
    try {
      const [dashboard, history] = await Promise.all([api.dashboard(), api.operations()]);
      setError("");
      setData(dashboard);
      setOperations(history);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    }
  }, []);
  // Initial data loading synchronizes the component with the remote API.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);
  if (!data && !error)
    return (
      <main className="center">
        <LoaderCircle className="spin" />
        <p>Загружаем CRM Fuel…</p>
      </main>
    );
  return (
    <main>
      <header>
        <div>
          <span className="brand">
            <FuelIcon /> CRM FUEL
          </span>
          <h1>{tab === "home" ? "Добрый день" : "Операции"}</h1>
          <p>{tab === "home" ? "Финансы и остатки" : "Полная финансовая история"}</p>
        </div>
        <button className="icon" onClick={() => void load()}>
          <RefreshCw />
        </button>
      </header>
      {error && (
        <div className="error banner">
          {error}
          <button onClick={() => void load()}>Повторить</button>
        </div>
      )}
      {data && (
        <>
          {tab === "home" ? (
            <>
              <section className="metrics">
                <article>
                  <WalletCards />
                  <span>Чистая прибыль</span>
                  <strong>{rub(data.net_profit_kopecks)}</strong>
                </article>
                <article>
                  <span>Выручка</span>
                  <strong>{rub(data.revenue_kopecks)}</strong>
                </article>
                <article>
                  <span>Остаток</span>
                  <strong>{Number(data.total_stock_liters).toLocaleString("ru-RU")} л</strong>
                </article>
              </section>
              <section className="cashCard">
                <div>
                  <span>Наличные в кассе</span>
                  <strong>{rub(data.cash_balance_kopecks)}</strong>
                  <small>Расходы: {rub(data.expenses_kopecks)}</small>
                </div>
                <div>
                  <button onClick={() => setCashMode("expense")}>
                    <ReceiptText />
                    Расход
                  </button>
                  <button
                    onClick={() => setCashMode("collection")}
                    disabled={data.cash_balance_kopecks <= 0}
                  >
                    <Banknote />
                    Инкассация
                  </button>
                </div>
              </section>
              <div className="sectionTitle">
                <h2>Топливо</h2>
                <span>{data.fuels.length} позиции</span>
              </div>
              <section className="fuelGrid">
                {data.fuels.map((f) => (
                  <article
                    className="fuelCard"
                    key={f.id}
                    style={{ "--accent": f.color } as React.CSSProperties}
                  >
                    <div className="fuelTop">
                      <div className="fuelName">
                        <i />
                        <div>
                          <h3>{f.name}</h3>
                          <span>{rub(f.sale_price_kopecks)} / л</span>
                        </div>
                      </div>
                      <button
                        className="priceBtn"
                        onClick={() => setActive({ mode: "price", fuel: f })}
                      >
                        Цена
                      </button>
                    </div>
                    <div className="stock">
                      <span>В резервуаре</span>
                      <strong>
                        {Number(f.stock_liters).toLocaleString("ru-RU")} <small>л</small>
                      </strong>
                    </div>
                    <div className="actions">
                      <button onClick={() => setActive({ mode: "purchase", fuel: f })}>
                        <ArrowDownToLine /> Закупка
                      </button>
                      <button
                        className="sale"
                        disabled={!f.sale_price_kopecks || Number(f.stock_liters) <= 0}
                        onClick={() => setActive({ mode: "sale", fuel: f })}
                      >
                        <ArrowUpFromLine /> Продажа
                      </button>
                    </div>
                  </article>
                ))}
              </section>
            </>
          ) : (
            <>
              <div className="sectionTitle">
                <h2>История</h2>
                <span>{operations.length}</span>
              </div>
              <HistoryView
                items={operations}
                onReverse={async (item) => {
                  const reason = window.prompt("Причина отмены операции");
                  if (!reason) return;
                  try {
                    await api.reverse(item.id, reason);
                    void load();
                  } catch (e) {
                    setError(e instanceof Error ? e.message : "Ошибка");
                  }
                }}
              />
            </>
          )}
          <nav>
            <button className={tab === "home" ? "selected" : ""} onClick={() => setTab("home")}>
              <FuelIcon />
              Главная
            </button>
            <button
              className={tab === "operations" ? "selected" : ""}
              onClick={() => setTab("operations")}
            >
              <RefreshCw />
              Операции
            </button>
            <button onClick={() => alert("Отчёты — следующий этап")}>
              <WalletCards />
              Отчёты
            </button>
          </nav>
        </>
      )}
      {active && (
        <FuelSheet {...active} onClose={() => setActive(null)} onDone={() => void load()} />
      )}{" "}
      {cashMode && data && (
        <CashSheet
          mode={cashMode}
          cash={data.cash_balance_kopecks}
          onClose={() => setCashMode(null)}
          onDone={() => void load()}
        />
      )}
    </main>
  );
}
