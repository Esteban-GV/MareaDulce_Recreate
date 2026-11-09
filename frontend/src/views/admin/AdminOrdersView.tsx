import React, { useEffect, useState } from 'react';
import { Order, OrderStatus } from '../../types';
import { fetchOrders, updateOrderStatus } from '../../services/api';
import { Check, AlertCircle, RefreshCw, Filter } from 'lucide-react';

const VALID_TRANSITIONS: Record<OrderStatus, OrderStatus[]> = {
  PENDIENTE: ['CONFIRMADO', 'CANCELADO'],
  CONFIRMADO: ['EN_PREPARACION', 'CANCELADO'],
  EN_PREPARACION: ['LISTO', 'CANCELADO'],
  LISTO: ['ENTREGADO'],
  ENTREGADO: [],
  CANCELADO: [],
};

export const AdminOrdersView: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<{ text: string; error?: boolean } | null>(null);

  const loadOrders = () => {
    setLoading(true);
    fetchOrders(filterStatus || undefined)
      .then((data) => {
        setOrders(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    loadOrders();
  }, [filterStatus]);

  const handleStatusChange = async (orderId: number, newStatus: string) => {
    setUpdatingId(orderId);
    setFeedbackMsg(null);
    try {
      const updated = await updateOrderStatus(orderId, newStatus);
      setOrders((prev) => prev.map((o) => (o.id === orderId ? updated : o)));
      setFeedbackMsg({ text: `Pedido ${updated.order_number} actualizado a ${newStatus}.` });
      setTimeout(() => setFeedbackMsg(null), 4000);
    } catch (err: any) {
      setFeedbackMsg({ text: err.message || 'Error al actualizar estado', error: true });
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <div className="space-y-6">
      
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-serif text-2xl font-semibold text-petroleo-500">Gestión de Pedidos</h1>
          <p className="text-xs text-gris-700">Control de flujo y estados transaccionales</p>
        </div>

        {/* Filtro por Estado */}
        <div className="flex items-center gap-2 text-xs">
          <Filter className="w-4 h-4 text-gris-700" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-white border border-crema-300 rounded-md py-1.5 px-3 text-xs text-carbon-500 font-semibold focus:outline-none focus:ring-2 focus:ring-petroleo-500 shadow-xs"
          >
            <option value="">Todos los Estados ({orders.length})</option>
            <option value="PENDIENTE">Pendientes</option>
            <option value="CONFIRMADO">Confirmados</option>
            <option value="EN_PREPARACION">En Preparación</option>
            <option value="LISTO">Listos para Entrega</option>
            <option value="ENTREGADO">Entregados</option>
            <option value="CANCELADO">Cancelados</option>
          </select>
          <button
            onClick={loadOrders}
            className="p-1.5 bg-white border border-crema-300 rounded-md hover:bg-crema-100 text-gris-700"
            title="Recargar pedidos"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {feedbackMsg && (
        <div
          className={`p-3 rounded-md text-xs flex items-center gap-2 ${
            feedbackMsg.error
              ? 'bg-feedback-error-bg text-feedback-error border border-feedback-error/30'
              : 'bg-menta-100 text-petroleo-500 border border-menta-500/50'
          }`}
        >
          {feedbackMsg.error ? <AlertCircle className="w-4 h-4" /> : <Check className="w-4 h-4" />}
          <span>{feedbackMsg.text}</span>
        </div>
      )}

      {/* Lista de Pedidos Expandida */}
      <div className="space-y-4">
        {loading ? (
          <div className="p-12 text-center text-xs text-gris-700 animate-pulse bg-white rounded-xl border border-crema-200">
            Cargando pedidos...
          </div>
        ) : orders.length === 0 ? (
          <div className="p-12 text-center text-xs text-gris-700 bg-white rounded-xl border border-crema-200">
            No se encontraron pedidos con el filtro actual.
          </div>
        ) : (
          orders.map((ord) => {
            const allowed = VALID_TRANSITIONS[ord.status] || [];
            return (
              <div
                key={ord.id}
                className="bg-white rounded-xl border border-crema-200 p-5 shadow-xs space-y-4 hover:border-aguamarina-500/50 transition-colors"
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-crema-200 pb-3">
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-base font-bold text-petroleo-500">{ord.order_number}</span>
                      <span className={`px-2.5 py-0.5 rounded-pill text-[10px] font-bold uppercase tracking-wider ${
                        ord.status === 'CONFIRMADO' || ord.status === 'ENTREGADO'
                          ? 'bg-menta-500 text-petroleo-500'
                          : ord.status === 'CANCELADO'
                          ? 'bg-feedback-error-bg text-feedback-error'
                          : 'bg-vainilla-500 text-carbon-500'
                      }`}>
                        {ord.status}
                      </span>
                    </div>
                    <p className="text-xs text-gris-700 mt-0.5">
                      Cliente: <strong>{ord.customer_name}</strong> • {ord.customer_phone} • {ord.customer_email}
                    </p>
                  </div>

                  {/* Selector de Transición de Estado */}
                  <div className="flex items-center gap-2">
                    {allowed.length > 0 ? (
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] text-gris-700">Cambiar a:</span>
                        <select
                          disabled={updatingId === ord.id}
                          onChange={(e) => handleStatusChange(ord.id, e.target.value)}
                          defaultValue=""
                          className="bg-crema-100 border border-crema-300 rounded px-2.5 py-1 text-xs text-carbon-500 font-semibold focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                        >
                          <option value="" disabled>Seleccionar...</option>
                          {allowed.map((s) => (
                            <option key={s} value={s}>{s}</option>
                          ))}
                        </select>
                      </div>
                    ) : (
                      <span className="text-[11px] text-gris-700 italic">Estado final</span>
                    )}
                  </div>
                </div>

                {/* Ítems y Personalizaciones */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-4 text-xs">
                  <div className="md:col-span-8 space-y-1.5">
                    <p className="font-semibold text-carbon-500">Productos:</p>
                    <ul className="space-y-1">
                      {ord.items.map((i) => (
                        <li key={i.id} className="flex items-center justify-between text-gris-700 bg-crema-100/40 p-1.5 rounded">
                          <div>
                            <span className="font-medium text-carbon-500">{i.product_name}</span> × {i.quantity}
                            {i.custom_message && (
                              <span className="text-[11px] text-petroleo-500 font-medium ml-2">
                                [Mensaje: «{i.custom_message}»]
                              </span>
                            )}
                          </div>
                          <span className="font-bold tabular-nums text-carbon-500">
                            $ {i.subtotal_cop.toLocaleString('es-CO')}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="md:col-span-4 bg-crema-100/60 p-3 rounded-lg border border-crema-200 text-carbon-500 space-y-1">
                    <p><strong>Modalidad:</strong> {ord.delivery_type === 'domicilio' ? 'Envío a Domicilio' : 'Recogida en tienda'}</p>
                    {ord.delivery_address && <p><strong>Dirección:</strong> {ord.delivery_address}</p>}
                    <p><strong>Fecha programada:</strong> {ord.delivery_date} ({ord.delivery_slot || 'Sin franja'})</p>
                    <div className="pt-2 border-t border-crema-300 flex justify-between font-bold text-petroleo-500">
                      <span>Total:</span>
                      <span className="tabular-nums">$ {ord.total_cop.toLocaleString('es-CO')} COP</span>
                    </div>
                  </div>
                </div>

              </div>
            );
          })
        )}
      </div>

    </div>
  );
};
