import React, { useEffect, useState } from 'react';
import { KpiSummary, Order } from '../../types';
import { fetchAdminKpis, fetchOrders } from '../../services/api';
import { DollarSign, Clock, Calendar, AlertTriangle, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const AdminDashboardView: React.FC = () => {
  const [kpis, setKpis] = useState<KpiSummary | null>(null);
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchAdminKpis().catch(() => null),
      fetchOrders().catch(() => []),
    ]).then(([kpiData, ordersData]) => {
      if (kpiData) setKpis(kpiData);
      setRecentOrders(ordersData.slice(0, 5));
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-xs text-gris-700 animate-pulse">Cargando métricas de operación...</div>;
  }

  return (
    <div className="space-y-8">
      
      {/* Tarjetas de Indicadores KPI */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        
        {/* KPI 1: Ventas del Día */}
        <div className="bg-white p-5 rounded-xl border border-crema-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gris-700">Ventas del Día (COP)</p>
            <p className="font-bold text-2xl text-petroleo-500 tabular-nums mt-1">
              $ {(kpis?.today_sales_cop || 0).toLocaleString('es-CO')}
            </p>
            <span className="text-[11px] text-feedback-exito font-medium">Operación normal</span>
          </div>
          <div className="w-12 h-12 rounded-full bg-menta-100 flex items-center justify-center text-petroleo-500">
            <DollarSign className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 2: Pedidos Pendientes */}
        <div className="bg-white p-5 rounded-xl border border-crema-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gris-700">Pedidos Pendientes</p>
            <p className="font-bold text-2xl text-carbon-500 tabular-nums mt-1">
              {kpis?.pending_orders_count || 0}
            </p>
            <span className="text-[11px] text-coral-500 font-medium">Por confirmar</span>
          </div>
          <div className="w-12 h-12 rounded-full bg-coral-500/20 flex items-center justify-center text-coral-500">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 3: Pedidos del Mes */}
        <div className="bg-white p-5 rounded-xl border border-crema-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gris-700">Pedidos del Mes</p>
            <p className="font-bold text-2xl text-carbon-500 tabular-nums mt-1">
              {kpis?.month_orders_count || 0}
            </p>
            <span className="text-[11px] text-gris-700 font-medium">Acumulado mensual</span>
          </div>
          <div className="w-12 h-12 rounded-full bg-aguamarina-300/40 flex items-center justify-center text-petroleo-500">
            <Calendar className="w-6 h-6" />
          </div>
        </div>

        {/* KPI 4: Bajo Stock */}
        <div className="bg-white p-5 rounded-xl border border-crema-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gris-700">Alertas de Bajo Stock</p>
            <p className="font-bold text-2xl text-feedback-error tabular-nums mt-1">
              {kpis?.low_stock_products_count || 0}
            </p>
            <span className="text-[11px] text-feedback-advertencia font-medium">&le; 5 unidades</span>
          </div>
          <div className="w-12 h-12 rounded-full bg-vainilla-500/30 flex items-center justify-center text-feedback-advertencia">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

      </div>

      {/* Tabla de Pedidos Recientes */}
      <div className="bg-white rounded-xl border border-crema-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-crema-200 flex items-center justify-between">
          <div>
            <h2 className="font-serif text-base font-semibold text-petroleo-500">Últimos Pedidos Registrados</h2>
            <p className="text-xs text-gris-700">Monitoreo transaccional de órdenes recibidas</p>
          </div>
          <Link
            to="/admin/pedidos"
            className="text-xs font-semibold text-petroleo-500 hover:text-aguamarina-700 flex items-center gap-1"
          >
            <span>Ver todos los pedidos</span>
            <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#FAF8F4] text-gris-700 border-b border-crema-200 uppercase font-semibold">
              <tr>
                <th className="py-3 px-4">Código</th>
                <th className="py-3 px-4">Cliente</th>
                <th className="py-3 px-4">Entrega</th>
                <th className="py-3 px-4">Total COP</th>
                <th className="py-3 px-4">Estado</th>
                <th className="py-3 px-4 text-right">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-crema-200">
              {recentOrders.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gris-700">
                    No hay pedidos registrados en este momento.
                  </td>
                </tr>
              ) : (
                recentOrders.map((ord) => (
                  <tr key={ord.id} className="hover:bg-crema-100/50 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-petroleo-500">{ord.order_number}</td>
                    <td className="py-3 px-4">
                      <p className="font-semibold text-carbon-500">{ord.customer_name}</p>
                      <p className="text-[11px] text-gris-700">{ord.customer_email}</p>
                    </td>
                    <td className="py-3 px-4">
                      <span className="capitalize">{ord.delivery_type.replace('_', ' ')}</span>
                      <p className="text-[10px] text-gris-700">{ord.delivery_date}</p>
                    </td>
                    <td className="py-3 px-4 font-bold tabular-nums">
                      $ {ord.total_cop.toLocaleString('es-CO')}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2.5 py-0.5 rounded-pill text-[10px] font-bold uppercase tracking-wider ${
                        ord.status === 'CONFIRMADO' || ord.status === 'ENTREGADO'
                          ? 'bg-menta-500 text-petroleo-500'
                          : ord.status === 'CANCELADO'
                          ? 'bg-feedback-error-bg text-feedback-error'
                          : 'bg-vainilla-500 text-carbon-500'
                      }`}>
                        {ord.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Link
                        to="/admin/pedidos"
                        className="text-petroleo-500 hover:underline font-semibold"
                      >
                        Gestionar
                      </Link>
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
