import React, { useEffect, useState } from 'react';
import { Product } from '../../types';
import { fetchProducts } from '../../services/api';
import { RefreshCw } from 'lucide-react';

export const AdminProductsView: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    setLoading(true);
    fetchProducts({ all_status: true }).then((prodRes) => {
      setProducts(prodRes.data);
      setLoading(false);
    });
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-petroleo-500">Catálogo de Productos</h1>
          <p className="text-xs text-gris-700">Administración de recetas, precios en COP y alérgenos</p>
        </div>
        <button
          onClick={loadData}
          className="p-2 bg-white border border-crema-300 rounded-md hover:bg-crema-100 text-gris-700 flex items-center gap-1.5 text-xs font-semibold"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Actualizar</span>
        </button>
      </div>

      <div className="bg-white rounded-xl border border-crema-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#FAF8F4] text-gris-700 border-b border-crema-200 uppercase font-semibold">
              <tr>
                <th className="py-3 px-4">Producto</th>
                <th className="py-3 px-4">Categoría</th>
                <th className="py-3 px-4">Porciones</th>
                <th className="py-3 px-4">Precio COP</th>
                <th className="py-3 px-4">Stock</th>
                <th className="py-3 px-4">Insignia</th>
                <th className="py-3 px-4">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-crema-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gris-700 animate-pulse">
                    Cargando productos...
                  </td>
                </tr>
              ) : (
                products.map((prod) => (
                  <tr key={prod.id} className="hover:bg-crema-100/50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <img
                          src={prod.image_url || '/assets/isotipo.svg'}
                          alt={prod.name}
                          className="w-10 h-10 rounded object-cover bg-menta-100 flex-shrink-0"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = '/assets/isotipo.svg';
                          }}
                        />
                        <div>
                          <p className="font-semibold text-carbon-500">{prod.name}</p>
                          <p className="text-[10px] text-gris-700 font-mono">{prod.slug}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-gris-700">{prod.category_name}</td>
                    <td className="py-3 px-4 text-gris-700">{prod.servings}</td>
                    <td className="py-3 px-4 font-bold tabular-nums">$ {prod.price_cop.toLocaleString('es-CO')}</td>
                    <td className="py-3 px-4 font-semibold tabular-nums">{prod.stock} u.</td>
                    <td className="py-3 px-4">
                      {prod.badge ? (
                        <span className="px-2 py-0.5 rounded-pill bg-crema-200 text-carbon-500 text-[10px] font-bold">
                          {prod.badge}
                        </span>
                      ) : (
                        <span className="text-gris-700 text-[11px]">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-pill text-[10px] font-bold ${
                        prod.is_active ? 'bg-menta-500 text-petroleo-500' : 'bg-crema-300 text-gris-700'
                      }`}>
                        {prod.is_active ? 'Activo' : 'Inactivo'}
                      </span>
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
