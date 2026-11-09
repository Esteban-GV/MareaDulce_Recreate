import React, { useEffect, useState } from 'react';
import { fetchAdminInventory, updateProductStock } from '../../services/api';
import { Check, Save, RefreshCw } from 'lucide-react';

export const AdminInventoryView: React.FC = () => {
  const [inventory, setInventory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [stockInputs, setStockInputs] = useState<Record<number, number>>({});
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadData = () => {
    setLoading(true);
    fetchAdminInventory()
      .then((data) => {
        setInventory(data);
        const map: Record<number, number> = {};
        data.forEach((item: any) => {
          map[item.id] = item.stock;
        });
        setStockInputs(map);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveStock = async (productId: number) => {
    const newStock = stockInputs[productId];
    if (newStock === undefined || newStock < 0) return;
    setSavingId(productId);
    try {
      await updateProductStock(productId, newStock);
      setFeedback('Existencias actualizadas correctamente.');
      setTimeout(() => setFeedback(null), 3000);
      loadData();
    } catch (err: any) {
      setFeedback(err.message || 'Error al actualizar inventario');
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-petroleo-500">Control Rápido de Inventario</h1>
          <p className="text-xs text-gris-700">Ajuste de existencias para prevención de sobreventas en SQLite</p>
        </div>
        <button
          onClick={loadData}
          className="p-2 bg-white border border-crema-300 rounded-md hover:bg-crema-100 text-gris-700 flex items-center gap-1.5 text-xs font-semibold"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Actualizar</span>
        </button>
      </div>

      {feedback && (
        <div className="p-3 bg-menta-100 border border-menta-500/50 rounded-md text-xs text-petroleo-500 flex items-center gap-2">
          <Check className="w-4 h-4" />
          <span>{feedback}</span>
        </div>
      )}

      <div className="bg-white rounded-xl border border-crema-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#FAF8F4] text-gris-700 border-b border-crema-200 uppercase font-semibold">
              <tr>
                <th className="py-3 px-4">ID</th>
                <th className="py-3 px-4">Producto</th>
                <th className="py-3 px-4">Categoría</th>
                <th className="py-3 px-4">Precio COP</th>
                <th className="py-3 px-4">Estado Stock</th>
                <th className="py-3 px-4">Existencias</th>
                <th className="py-3 px-4 text-right">Guardar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-crema-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gris-700 animate-pulse">
                    Cargando inventario...
                  </td>
                </tr>
              ) : (
                inventory.map((item) => (
                  <tr key={item.id} className="hover:bg-crema-100/50 transition-colors">
                    <td className="py-3 px-4 font-mono text-gris-700">#{item.id}</td>
                    <td className="py-3 px-4 font-semibold text-carbon-500">{item.name}</td>
                    <td className="py-3 px-4 text-gris-700">{item.category}</td>
                    <td className="py-3 px-4 font-bold tabular-nums">$ {item.price_cop.toLocaleString('es-CO')}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-pill text-[10px] font-bold uppercase tracking-wider ${
                        item.stock_status === 'DISPONIBLE'
                          ? 'bg-menta-500 text-petroleo-500'
                          : item.stock_status === 'BAJO_STOCK'
                          ? 'bg-vainilla-500 text-carbon-500'
                          : 'bg-feedback-error-bg text-feedback-error'
                      }`}>
                        {item.stock_status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <input
                        type="number"
                        min={0}
                        value={stockInputs[item.id] ?? item.stock}
                        onChange={(e) =>
                          setStockInputs({ ...stockInputs, [item.id]: Math.max(0, parseInt(e.target.value) || 0) })
                        }
                        className="w-20 px-2 py-1 bg-crema-100/50 border border-crema-300 rounded font-semibold tabular-nums text-center focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                      />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleSaveStock(item.id)}
                        disabled={savingId === item.id}
                        className="px-3 py-1 bg-aguamarina-500 hover:bg-aguamarina-600 text-carbon-500 font-bold rounded text-xs flex items-center gap-1 ml-auto shadow-xs"
                      >
                        <Save className="w-3.5 h-3.5" />
                        <span>{savingId === item.id ? '...' : 'Fijar'}</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
