import React, { useEffect, useState } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { Order } from '../types';
import { fetchOrderTracking } from '../services/api';
import { CheckCircle, Package, ArrowRight, Home } from 'lucide-react';

export const OrderConfirmationView: React.FC = () => {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const location = useLocation();
  const [order, setOrder] = useState<Order | null>((location.state as any)?.order || null);
  const [loading, setLoading] = useState(!order);

  useEffect(() => {
    if (!order && orderNumber) {
      fetchOrderTracking(orderNumber)
        .then((o) => {
          setOrder(o);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [order, orderNumber]);

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center text-gris-700 animate-pulse">
        Cargando confirmación de pedido...
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-8">
      
      {/* Tarjeta de Éxito */}
      <div className="bg-white rounded-2xl border border-crema-200 p-8 text-center shadow-sm space-y-4">
        <div className="w-16 h-16 rounded-full bg-menta-100 flex items-center justify-center mx-auto">
          <CheckCircle className="w-10 h-10 text-feedback-exito" />
        </div>

        <span className="text-xs font-bold uppercase tracking-wider text-aguamarina-700">
          ¡Pedido Confirmado con Éxito!
        </span>

        <h1 className="font-serif text-3xl font-semibold text-carbon-500">
          Gracias por tu compra, {order?.customer_name || 'Estimado cliente'}
        </h1>

        <p className="text-sm text-gris-700 max-w-lg mx-auto">
          Hemos recibido tu solicitud y nuestros maestros pasteleros ya están preparando los mejores ingredientes frescos.
        </p>

        {/* Código de Pedido MD-AAAA-NNNNNN */}
        <div className="bg-crema-100/70 p-4 rounded-xl border border-crema-300 inline-block my-2">
          <p className="text-xs text-gris-700 uppercase font-semibold tracking-wider">Código de Pedido:</p>
          <p className="font-mono text-2xl font-bold text-petroleo-500 tracking-wider mt-0.5">
            {order?.order_number || orderNumber}
          </p>
        </div>

        <p className="text-xs text-gris-700">
          Enviamos el comprobante y los detalles de entrega a <strong>{order?.customer_email}</strong>.
        </p>
      </div>

      {/* Resumen del Pedido */}
      {order && (
        <div className="bg-white rounded-xl border border-crema-200 p-6 shadow-sm space-y-4">
          <h2 className="font-serif text-lg font-semibold text-petroleo-500 border-b border-crema-200 pb-2">
            Detalles del Pedido
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-carbon-500">
            <div>
              <p className="text-gris-700">Modalidad de entrega:</p>
              <p className="font-semibold capitalize">{order.delivery_type.replace('_', ' ')}</p>
              {order.delivery_address && <p className="text-gris-700 mt-1">{order.delivery_address}</p>}
            </div>
            <div>
              <p className="text-gris-700">Fecha y franja horaria:</p>
              <p className="font-semibold">{order.delivery_date} • {order.delivery_slot || 'Por coordinar'}</p>
            </div>
          </div>

          <div className="divide-y divide-crema-200 pt-2">
            {order.items.map((item) => (
              <div key={item.id} className="py-2.5 flex justify-between items-center text-xs">
                <div>
                  <span className="font-semibold text-carbon-500">{item.product_name}</span>
                  <span className="text-gris-700"> × {item.quantity}</span>
                  {item.custom_message && (
                    <p className="text-[11px] text-gris-700 italic">«{item.custom_message}»</p>
                  )}
                </div>
                <span className="font-bold text-petroleo-500 tabular-nums">
                  $ {item.subtotal_cop.toLocaleString('es-CO')}
                </span>
              </div>
            ))}
          </div>

          <div className="border-t border-crema-200 pt-3 flex justify-between items-center text-sm font-bold text-petroleo-500">
            <span>Total Pagado (Simulado):</span>
            <span className="text-base tabular-nums">$ {order.total_cop.toLocaleString('es-CO')} COP</span>
          </div>
        </div>
      )}

      {/* Acciones */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <Link
          to={`/seguimiento?code=${order?.order_number || orderNumber}`}
          className="w-full sm:w-auto px-6 py-3 bg-aguamarina-500 hover:bg-aguamarina-600 text-carbon-500 font-bold rounded-md flex items-center justify-center gap-2 shadow-sm transition-all"
        >
          <Package className="w-4 h-4" />
          <span>Seguir Estado en Vivo</span>
          <ArrowRight className="w-4 h-4" />
        </Link>

        <Link
          to="/"
          className="w-full sm:w-auto px-6 py-3 bg-white hover:bg-crema-200 text-petroleo-500 font-semibold rounded-md border border-crema-300 flex items-center justify-center gap-2 transition-all"
        >
          <Home className="w-4 h-4" />
          <span>Volver al Inicio</span>
        </Link>
      </div>

    </div>
  );
};
