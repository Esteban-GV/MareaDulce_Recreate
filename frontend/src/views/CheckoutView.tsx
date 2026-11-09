import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { useSystem } from '../context/SystemContext';
import { createOrder, generateIdempotencyKey } from '../services/api';
import { DeliveryType } from '../types';
import { Check, ArrowRight, ArrowLeft, ShieldCheck, AlertCircle, RefreshCw, ShoppingBag } from 'lucide-react';

export const CheckoutView: React.FC = () => {
  const { items, totalPriceCop, clearCart } = useCart();
  const { user } = useAuth();
  const { isOnline, checkHealth } = useSystem();
  const navigate = useNavigate();

  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form State
  const [customerName, setCustomerName] = useState(user?.full_name || '');
  const [customerEmail, setCustomerEmail] = useState(user?.email || '');
  const [customerPhone, setCustomerPhone] = useState(user?.phone || '');
  const [deliveryType, setDeliveryType] = useState<DeliveryType>('domicilio');
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [deliveryDate, setDeliveryDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  });
  const [deliverySlot, setDeliverySlot] = useState('Tarde (14:00 - 18:00)');
  const [orderNotes, setOrderNotes] = useState('');

  // Clave de Idempotencia única persistida durante el intento de checkout
  const [idempotencyKey] = useState<string>(() => generateIdempotencyKey());

  if (items.length === 0) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-16 h-16 rounded-full bg-menta-100 flex items-center justify-center mx-auto">
          <ShoppingBag className="w-8 h-8 text-petroleo-500" />
        </div>
        <h2 className="font-serif text-2xl font-semibold text-carbon-500">Tu canasta está vacía</h2>
        <p className="text-sm text-gris-700">Agrega productos a tu canasta antes de iniciar el proceso de compra.</p>
        <button
          onClick={() => navigate('/catalogo')}
          className="px-6 py-3 bg-aguamarina-500 text-carbon-500 font-bold rounded-md hover:bg-aguamarina-600 transition-colors"
        >
          Ir al Catálogo
        </button>
      </div>
    );
  }

  const handleNextStep = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    if (step === 1) {
      if (!customerName.trim() || !customerEmail.trim() || !customerPhone.trim()) {
        setErrorMsg('Por favor completa todos tus datos personales.');
        return;
      }
      setStep(2);
    } else if (step === 2) {
      if (deliveryType === 'domicilio' && !deliveryAddress.trim()) {
        setErrorMsg('Ingresa la dirección para el envío de tu pedido.');
        return;
      }
      setStep(3);
    }
  };

  const handleConfirmOrder = async () => {
    if (!isOnline) {
      setErrorMsg('Estamos actualizando la tienda. Tu pedido se enviará automáticamente en cuanto regrese la conexión.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    const payload = {
      customer_name: customerName,
      customer_email: customerEmail,
      customer_phone: customerPhone,
      delivery_type: deliveryType,
      delivery_address: deliveryType === 'domicilio' ? deliveryAddress : undefined,
      delivery_date: deliveryDate,
      delivery_slot: deliverySlot,
      notes: orderNotes,
      payment_method: 'simulado_demo',
      items: items.map((i) => ({
        product_id: i.product.id,
        quantity: i.quantity,
        customization: i.customization,
      })),
    };

    try {
      const order = await createOrder(payload, idempotencyKey);
      clearCart();
      navigate(`/confirmacion/${order.order_number}`, { state: { order } });
    } catch (err: any) {
      setErrorMsg(err.message || 'Ocurrió un error al confirmar tu pedido. Por favor intenta de nuevo.');
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      
      {/* Indicador de Pasos del Checkout */}
      <div className="max-w-3xl mx-auto mb-10">
        <div className="flex items-center justify-between relative">
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-0.5 bg-crema-200 -z-10" />

          {/* Paso 1 */}
          <div className="flex flex-col items-center gap-1.5 bg-crema-100 px-3">
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition-colors ${
                step >= 1 ? 'bg-aguamarina-500 text-carbon-500' : 'bg-crema-200 text-gris-700'
              }`}
            >
              {step > 1 ? <Check className="w-4 h-4" /> : '1'}
            </div>
            <span className="text-xs font-semibold text-carbon-500">1. Tus Datos</span>
          </div>

          {/* Paso 2 */}
          <div className="flex flex-col items-center gap-1.5 bg-crema-100 px-3">
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition-colors ${
                step >= 2 ? 'bg-aguamarina-500 text-carbon-500' : 'bg-crema-200 text-gris-700'
              }`}
            >
              {step > 2 ? <Check className="w-4 h-4" /> : '2'}
            </div>
            <span className="text-xs font-semibold text-carbon-500">2. Entrega</span>
          </div>

          {/* Paso 3 */}
          <div className="flex flex-col items-center gap-1.5 bg-crema-100 px-3">
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs transition-colors ${
                step === 3 ? 'bg-aguamarina-500 text-carbon-500' : 'bg-crema-200 text-gris-700'
              }`}
            >
              3
            </div>
            <span className="text-xs font-semibold text-carbon-500">3. Confirmación</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Formulario Principal de Pasos */}
        <div className="lg:col-span-7 bg-white p-6 sm:p-8 rounded-xl border border-crema-200 shadow-sm space-y-6">
          
          {errorMsg && (
            <div className="p-3.5 bg-feedback-error-bg border border-feedback-error/30 rounded-md text-xs text-feedback-error flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* PASO 1: DATOS DEL CLIENTE */}
          {step === 1 && (
            <form onSubmit={handleNextStep} className="space-y-4">
              <h2 className="font-serif text-xl font-semibold text-petroleo-500">Datos Personales</h2>
              <p className="text-xs text-gris-700">Para enviarte la confirmación del pedido y el código de seguimiento.</p>

              <div>
                <label className="block text-xs font-semibold text-carbon-500 mb-1">Nombre Completo *</label>
                <input
                  type="text"
                  required
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  placeholder="Ej: Laura Camila Díaz"
                  className="w-full px-3 py-2 bg-crema-100/40 border border-crema-300 rounded-md text-sm text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-carbon-500 mb-1">Correo Electrónico *</label>
                  <input
                    type="email"
                    required
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    placeholder="laura@ejemplo.com"
                    className="w-full px-3 py-2 bg-crema-100/40 border border-crema-300 rounded-md text-sm text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-carbon-500 mb-1">Teléfono Móvil *</label>
                  <input
                    type="tel"
                    required
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    placeholder="+57 312 345 6789"
                    className="w-full px-3 py-2 bg-crema-100/40 border border-crema-300 rounded-md text-sm text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-end">
                <button
                  type="submit"
                  className="px-6 py-3 bg-aguamarina-500 hover:bg-aguamarina-600 text-carbon-500 font-bold rounded-md flex items-center gap-2 shadow-sm transition-all min-h-[44px]"
                >
                  <span>Continuar a Entrega</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </form>
          )}

          {/* PASO 2: MODALIDAD DE ENTREGA */}
          {step === 2 && (
            <form onSubmit={handleNextStep} className="space-y-4">
              <h2 className="font-serif text-xl font-semibold text-petroleo-500">Método y Fecha de Entrega</h2>

              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setDeliveryType('domicilio')}
                  className={`p-4 rounded-lg border text-left transition-all ${
                    deliveryType === 'domicilio'
                      ? 'border-aguamarina-500 bg-menta-100/60 ring-2 ring-aguamarina-500/30'
                      : 'border-crema-200 bg-white hover:bg-crema-100'
                  }`}
                >
                  <p className="font-semibold text-sm text-carbon-500">Envío a Domicilio</p>
                  <p className="text-xs text-gris-700 mt-1">Directo a tu puerta en Bogotá</p>
                </button>

                <button
                  type="button"
                  onClick={() => setDeliveryType('recogida_tienda')}
                  className={`p-4 rounded-lg border text-left transition-all ${
                    deliveryType === 'recogida_tienda'
                      ? 'border-aguamarina-500 bg-menta-100/60 ring-2 ring-aguamarina-500/30'
                      : 'border-crema-200 bg-white hover:bg-crema-100'
                  }`}
                >
                  <p className="font-semibold text-sm text-carbon-500">Recogida en Tienda</p>
                  <p className="text-xs text-gris-700 mt-1">Cra 15 # 85-30, sin costo</p>
                </button>
              </div>

              {deliveryType === 'domicilio' && (
                <div>
                  <label className="block text-xs font-semibold text-carbon-500 mb-1">Dirección de Entrega *</label>
                  <input
                    type="text"
                    required
                    value={deliveryAddress}
                    onChange={(e) => setDeliveryAddress(e.target.value)}
                    placeholder="Ej: Carrera 15 # 85-30, Apto 501"
                    className="w-full px-3 py-2 bg-crema-100/40 border border-crema-300 rounded-md text-sm text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                  />
                </div>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-carbon-500 mb-1">Fecha de Entrega *</label>
                  <input
                    type="date"
                    required
                    value={deliveryDate}
                    onChange={(e) => setDeliveryDate(e.target.value)}
                    className="w-full px-3 py-2 bg-crema-100/40 border border-crema-300 rounded-md text-sm text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-carbon-500 mb-1">Franja Horaria *</label>
                  <select
                    value={deliverySlot}
                    onChange={(e) => setDeliverySlot(e.target.value)}
                    className="w-full px-3 py-2 bg-crema-100/40 border border-crema-300 rounded-md text-sm text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                  >
                    <option value="Mañana (09:00 - 13:00)">Mañana (09:00 – 13:00)</option>
                    <option value="Tarde (14:00 - 18:00)">Tarde (14:00 – 18:00)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-carbon-500 mb-1">Notas adicionales (Opcional)</label>
                <textarea
                  rows={2}
                  value={orderNotes}
                  onChange={(e) => setOrderNotes(e.target.value)}
                  placeholder="Ej: Dejar en portería con el celador..."
                  className="w-full px-3 py-2 bg-crema-100/40 border border-crema-300 rounded-md text-sm text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                />
              </div>

              <div className="pt-4 flex justify-between">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="px-4 py-2 text-sm text-gris-700 hover:text-carbon-500 flex items-center gap-1.5"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Atrás</span>
                </button>
                <button
                  type="submit"
                  className="px-6 py-3 bg-aguamarina-500 hover:bg-aguamarina-600 text-carbon-500 font-bold rounded-md flex items-center gap-2 shadow-sm transition-all min-h-[44px]"
                >
                  <span>Continuar a Confirmación</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </form>
          )}

          {/* PASO 3: PAGO SIMULADO Y CONFIRMACIÓN */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="font-serif text-xl font-semibold text-petroleo-500">Confirmación y Pago</h2>
                <p className="text-xs text-gris-700">Verifica los detalles antes de registrar tu pedido en la plataforma.</p>
              </div>

              {/* Selector de Pago Simulado Requerido por Sección 1.7 */}
              <div className="p-4 bg-menta-100 rounded-lg border border-aguamarina-500/40 space-y-2">
                <div className="flex items-center gap-2 text-petroleo-500 font-bold text-sm">
                  <ShieldCheck className="w-5 h-5 text-feedback-exito" />
                  <span>Pago Simulado (Modo Demostración)</span>
                </div>
                <p className="text-xs text-gris-700 leading-relaxed">
                  Esta plataforma opera como laboratorio de ingeniería sobre Kubernetes con estrategia <strong>Recreate</strong>. No se solicitan datos de tarjeta bancaria real. La transacción se aprobará de forma inmediata.
                </p>
              </div>

              {/* Resumen del Destinatario */}
              <div className="text-xs bg-crema-100 p-4 rounded-lg space-y-1 text-carbon-500 border border-crema-200">
                <p><strong>Destinatario:</strong> {customerName} ({customerPhone})</p>
                <p><strong>Correo:</strong> {customerEmail}</p>
                <p><strong>Entrega:</strong> {deliveryType === 'domicilio' ? `Domicilio: ${deliveryAddress}` : 'Recogida en tienda'}</p>
                <p><strong>Fecha programada:</strong> {deliveryDate} • {deliverySlot}</p>
              </div>

              {/* Botón de Confirmación con Resiliencia Recreate */}
              <div className="pt-2 flex flex-col gap-3">
                <button
                  onClick={handleConfirmOrder}
                  disabled={submitting || !isOnline}
                  className={`w-full py-4 px-6 rounded-md font-bold text-sm flex items-center justify-center gap-2 shadow-md transition-all min-h-[48px] ${
                    submitting
                      ? 'bg-aguamarina-300 text-carbon-500 cursor-wait'
                      : !isOnline
                      ? 'bg-crema-300 text-gris-700 cursor-not-allowed'
                      : 'bg-aguamarina-500 hover:bg-aguamarina-600 text-carbon-500'
                  }`}
                >
                  {submitting ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Enviando tu pedido. No cierres esta página...</span>
                    </>
                  ) : !isOnline ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Disponible en unos segundos — Actualizando tienda...</span>
                    </>
                  ) : (
                    <>
                      <Check className="w-5 h-5" />
                      <span>Confirmar Pedido • $ {totalPriceCop.toLocaleString('es-CO')} COP</span>
                    </>
                  )}
                </button>

                {!isOnline && (
                  <button
                    onClick={() => checkHealth()}
                    className="text-xs text-petroleo-500 hover:underline text-center py-1 font-semibold"
                  >
                    Reintentar conexión ahora
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => setStep(2)}
                  disabled={submitting}
                  className="text-xs text-gris-700 hover:text-carbon-500 text-center py-1"
                >
                  Modificar datos de entrega
                </button>
              </div>

            </div>
          )}

        </div>

        {/* Barra Lateral con Resumen de Compra Sticky */}
        <div className="lg:col-span-5 bg-white p-6 rounded-xl border border-crema-200 shadow-sm sticky top-28 space-y-4">
          <h3 className="font-serif text-base font-semibold text-petroleo-500 border-b border-crema-200 pb-3">
            Resumen de tu Pedido ({items.length} {items.length === 1 ? 'producto' : 'productos'})
          </h3>

          <div className="divide-y divide-crema-200 max-h-80 overflow-y-auto space-y-3">
            {items.map(({ product, quantity, customization }) => (
              <div key={product.id} className="pt-3 flex justify-between items-start text-xs">
                <div>
                  <p className="font-semibold text-carbon-500">{product.name} × {quantity}</p>
                  {customization?.custom_message && (
                    <p className="text-[11px] text-gris-700 italic">«{customization.custom_message}»</p>
                  )}
                </div>
                <span className="font-bold text-petroleo-500 tabular-nums">
                  $ {(product.price_cop * quantity).toLocaleString('es-CO')}
                </span>
              </div>
            ))}
          </div>

          <div className="border-t border-crema-200 pt-3 space-y-1.5 text-xs">
            <div className="flex justify-between text-gris-700">
              <span>Subtotal:</span>
              <span className="tabular-nums font-semibold">$ {totalPriceCop.toLocaleString('es-CO')}</span>
            </div>
            <div className="flex justify-between text-gris-700">
              <span>Envío / Entrega:</span>
              <span className="text-feedback-exito font-semibold">Gratis (Demo)</span>
            </div>
            <div className="flex justify-between text-sm font-bold text-petroleo-500 pt-2 border-t border-crema-200">
              <span>Total a pagar:</span>
              <span className="text-base tabular-nums">$ {totalPriceCop.toLocaleString('es-CO')} COP</span>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
};
