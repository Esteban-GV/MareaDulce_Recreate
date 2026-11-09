import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Order, OrderStatus } from '../types';
import { fetchOrderTracking } from '../services/api';
import { Search, CheckCircle2, Clock, XCircle, AlertCircle } from 'lucide-react';

const STEPS: { status: OrderStatus; label: string; desc: string }[] = [
  { status: 'PENDIENTE', label: 'Recibido', desc: 'Pedido registrado en plataforma' },
  { status: 'CONFIRMADO', label: 'Confirmado', desc: 'Orden validada por cocina' },
  { status: 'EN_PREPARACION', label: 'En Preparación', desc: 'Horneando y decorando' },
  { status: 'LISTO', label: 'Listo', desc: 'Empacado y listo para despacho' },
  { status: 'ENTREGADO', label: 'Entregado', desc: 'Entregado al destinatario' },
];

export const OrderTrackerView: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialCode = searchParams.get('code') || '';
  
  const [orderCode, setOrderCode] = useState(initialCode);
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const searchOrder = (code: string) => {
    if (!code.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    fetchOrderTracking(code.trim())
      .then((data) => {
        setOrder(data);
        setLoading(false);
      })
      .catch((err) => {
        setOrder(null);
        setErrorMsg(err.message || 'No se encontró ningún pedido con ese código.');
        setLoading(false);
      });
  };

  useEffect(() => {
    if (initialCode) {
      searchOrder(initialCode);
    }
  }, [initialCode]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchParams({ code: orderCode });
    searchOrder(orderCode);
  };

  const getStepIndex = (currentStatus: OrderStatus) => {
    if (currentStatus === 'CANCELADO') return -1;
    return STEPS.findIndex((s) => s.status === currentStatus);
  };

  const currentStepIdx = order ? getStepIndex(order.status) : -1;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      
      {/* Encabezado */}
      <div className="text-center max-w-xl mx-auto space-y-2">
        <h1 className="font-serif text-3xl font-semibold text-petroleo-500">
          Seguimiento de Pedido en Vivo
        </h1>
        <p className="text-sm text-gris-700">
          Ingresa el código alfanumérico que recibiste al momento de tu compra (ej: MD-2026-000001).
        </p>
      </div>

      {/* Buscador */}
      <form onSubmit={handleSearch} className="max-w-lg mx-auto flex gap-2">
        <div className="relative flex-1">
          <Search className="w-5 h-5 text-gris-700 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            required
            value={orderCode}
            onChange={(e) => setOrderCode(e.target.value.toUpperCase())}
            placeholder="MD-2026-XXXXXX"
            className="w-full pl-10 pr-4 py-3 bg-white border border-crema-300 rounded-md font-mono text-base font-semibold text-carbon-500 uppercase focus:outline-none focus:ring-2 focus:ring-petroleo-500 shadow-sm"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 bg-aguamarina-500 hover:bg-aguamarina-600 text-carbon-500 font-bold rounded-md shadow-sm transition-all flex items-center gap-2 min-h-[44px]"
        >
          {loading ? 'Buscando...' : 'Consultar'}
        </button>
      </form>

      {errorMsg && (
        <div className="max-w-md mx-auto p-4 bg-feedback-error-bg border border-feedback-error/30 rounded-lg text-xs text-feedback-error flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Resultado y Línea de Tiempo */}
      {order && (
        <div className="bg-white rounded-2xl border border-crema-200 p-6 sm:p-8 shadow-sm space-y-8">
          
          {/* Header de la Orden */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-crema-200 pb-4">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-gris-700">Código Oficial</span>
              <p className="font-mono text-2xl font-bold text-petroleo-500">{order.order_number}</p>
              <p className="text-xs text-gris-700 mt-0.5">Destinatario: {order.customer_name}</p>
            </div>

            <div className="text-right">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-pill text-xs font-bold uppercase tracking-wider ${
                order.status === 'CANCELADO'
                  ? 'bg-feedback-error-bg text-feedback-error'
                  : 'bg-menta-500 text-petroleo-500'
              }`}>
                {order.status === 'CANCELADO' ? <XCircle className="w-3.5 h-3.5" /> : <Clock className="w-3.5 h-3.5" />}
                <span>Estado: {order.status}</span>
              </span>
              <p className="text-xs text-gris-700 mt-1">Fecha programada: {order.delivery_date}</p>
            </div>
          </div>

          {/* Línea de Tiempo de Estados */}
          {order.status === 'CANCELADO' ? (
            <div className="p-6 bg-feedback-error-bg rounded-xl border border-feedback-error/30 text-center space-y-2">
              <XCircle className="w-8 h-8 text-feedback-error mx-auto" />
              <h3 className="font-serif text-lg font-semibold text-feedback-error">Pedido Cancelado</h3>
              <p className="text-xs text-gris-700 max-w-sm mx-auto">
                Este pedido ha sido cancelado y las unidades fueron reincorporadas al inventario disponible.
              </p>
            </div>
          ) : (
            <div className="py-4">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 relative">
                {STEPS.map((step, idx) => {
                  const isCompleted = currentStepIdx >= idx;
                  const isCurrent = currentStepIdx === idx;
                  return (
                    <div
                      key={step.status}
                      className={`flex md:flex-col items-center gap-3 p-3 rounded-lg border text-center transition-all ${
                        isCurrent
                          ? 'border-aguamarina-500 bg-menta-100 ring-2 ring-aguamarina-500/30'
                          : isCompleted
                          ? 'border-crema-200 bg-crema-100/50'
                          : 'border-crema-200 bg-white opacity-40'
                      }`}
                    >
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0 ${
                          isCompleted
                            ? 'bg-aguamarina-500 text-carbon-500'
                            : 'bg-crema-200 text-gris-700'
                        }`}
                      >
                        {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                      </div>

                      <div className="text-left md:text-center">
                        <p className="font-semibold text-xs text-carbon-500">{step.label}</p>
                        <p className="text-[10px] text-gris-700">{step.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Lista de Productos en la Orden */}
          <div className="border-t border-crema-200 pt-4 space-y-3">
            <h3 className="font-serif text-sm font-semibold text-petroleo-500">Productos del Pedido</h3>
            <div className="divide-y divide-crema-200 text-xs text-carbon-500">
              {order.items.map((i) => (
                <div key={i.id} className="py-2 flex justify-between items-center">
                  <div>
                    <span className="font-medium">{i.product_name}</span>
                    <span className="text-gris-700"> × {i.quantity}</span>
                    {i.custom_message && (
                      <p className="text-[11px] text-gris-700 italic">«{i.custom_message}»</p>
                    )}
                  </div>
                  <span className="font-bold text-petroleo-500 tabular-nums">
                    $ {i.subtotal_cop.toLocaleString('es-CO')}
                  </span>
                </div>
              ))}
            </div>

            <div className="flex justify-between items-center pt-2 text-sm font-bold text-petroleo-500">
              <span>Total:</span>
              <span className="tabular-nums">$ {order.total_cop.toLocaleString('es-CO')} COP</span>
            </div>
          </div>

        </div>
      )}

    </div>
  );
};
