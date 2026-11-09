import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../../context/CartContext';
import { X, Trash2, Plus, Minus, ArrowRight, ShoppingBag } from 'lucide-react';

export const CartDrawer: React.FC = () => {
  const { items, isDrawerOpen, closeDrawer, removeItem, updateQuantity, totalPriceCop } = useCart();
  const navigate = useNavigate();

  if (!isDrawerOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden" role="dialog" aria-modal="true">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-carbon-500/40 backdrop-blur-sm transition-opacity"
        onClick={closeDrawer}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white shadow-2xl flex flex-col border-l border-crema-200">
          
          {/* Header del Cajón */}
          <div className="p-5 border-b border-crema-200 flex items-center justify-between bg-crema-100">
            <div className="flex items-center gap-2">
              <ShoppingBag className="w-5 h-5 text-petroleo-500" />
              <h2 className="font-serif text-lg font-semibold text-petroleo-500">Tu Canasta Dulce</h2>
            </div>
            <button
              onClick={closeDrawer}
              className="p-2 rounded-full hover:bg-crema-200 text-gris-700 min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label="Cerrar canasta"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Lista de Ítems */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {items.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-gris-700">
                <div className="w-16 h-16 rounded-full bg-menta-100 flex items-center justify-center mb-4">
                  <ShoppingBag className="w-8 h-8 text-aguamarina-700" />
                </div>
                <h3 className="font-serif text-lg font-semibold text-petroleo-500 mb-1">Tu canasta está vacía</h3>
                <p className="text-sm max-w-xs mb-6 text-gris-700">
                  Explora nuestras tortas y postres artesanales para endulzar tu día.
                </p>
                <button
                  onClick={() => {
                    closeDrawer();
                    navigate('/catalogo');
                  }}
                  className="px-5 py-2.5 bg-aguamarina-500 hover:bg-aguamarina-600 text-carbon-500 font-semibold rounded-md text-sm transition-colors"
                >
                  Ver el Catálogo
                </button>
              </div>
            ) : (
              items.map(({ product, quantity, customization }) => (
                <div
                  key={product.id}
                  className="p-3 bg-crema-100/60 rounded-lg border border-crema-200 flex gap-3 relative group"
                >
                  <img
                    src={product.image_url || '/assets/isotipo.svg'}
                    alt={product.name}
                    className="w-20 h-20 rounded-md object-cover bg-menta-100 flex-shrink-0"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '/assets/isotipo.svg';
                    }}
                  />
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm text-carbon-500 truncate" title={product.name}>
                      {product.name}
                    </h4>
                    <p className="font-bold text-sm text-petroleo-500 tabular-nums mt-0.5">
                      $ {product.price_cop.toLocaleString('es-CO')}
                    </p>

                    {/* Personalización si aplica */}
                    {customization?.custom_message && (
                      <p className="text-[11px] text-gris-700 bg-white/80 px-2 py-0.5 rounded border border-crema-300 mt-1 truncate">
                        «{customization.custom_message}»
                      </p>
                    )}

                    {/* Controles de Cantidad */}
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex items-center border border-crema-300 rounded bg-white">
                        <button
                          onClick={() => updateQuantity(product.id, quantity - 1)}
                          className="p-1 hover:bg-crema-200 text-gris-700 min-w-[28px] min-h-[28px] flex items-center justify-center"
                          aria-label="Disminuir cantidad"
                        >
                          <Minus className="w-3.5 h-3.5" />
                        </button>
                        <span className="px-2 text-xs font-semibold tabular-nums text-carbon-500">
                          {quantity}
                        </span>
                        <button
                          onClick={() => updateQuantity(product.id, quantity + 1)}
                          disabled={product.stock > 0 && quantity >= product.stock}
                          className="p-1 hover:bg-crema-200 text-gris-700 disabled:opacity-40 min-w-[28px] min-h-[28px] flex items-center justify-center"
                          aria-label="Aumentar cantidad"
                        >
                          <Plus className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <button
                        onClick={() => removeItem(product.id)}
                        className="text-feedback-error/80 hover:text-feedback-error p-1 transition-colors ml-auto min-w-[32px] min-h-[32px] flex items-center justify-center"
                        title="Eliminar de la canasta"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer del Cajón con Subtotal y Checkout */}
          {items.length > 0 && (
            <div className="p-5 border-t border-crema-200 bg-crema-100">
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm text-gris-700">Subtotal de productos:</span>
                <span className="font-bold text-lg text-petroleo-500 tabular-nums">
                  $ {totalPriceCop.toLocaleString('es-CO')} COP
                </span>
              </div>
              <p className="text-[11px] text-gris-700 mb-4">
                El costo de envío o recogida se calcula en el siguiente paso.
              </p>
              <button
                onClick={() => {
                  closeDrawer();
                  navigate('/checkout');
                }}
                className="w-full py-3 px-4 bg-aguamarina-500 hover:bg-aguamarina-600 text-carbon-500 font-bold rounded-md flex items-center justify-center gap-2 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-petroleo-500 min-h-[44px]"
              >
                <span>Proceder al Pago</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
