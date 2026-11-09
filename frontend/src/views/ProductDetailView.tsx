import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Product } from '../types';
import { fetchProductDetail } from '../services/api';
import { useCart } from '../context/CartContext';
import { ArrowLeft, Clock, Users, ShieldAlert, Plus, Minus, ShoppingBag, Check } from 'lucide-react';

export const ProductDetailView: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const { addItem } = useCart();
  
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [customMessage, setCustomMessage] = useState('');
  const [addedAnimation, setAddedAnimation] = useState(false);

  useEffect(() => {
    if (slug) {
      setLoading(true);
      fetchProductDetail(slug)
        .then((p) => {
          setProduct(p);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [slug]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center text-gris-700">
        <p className="animate-pulse">Cargando delicia artesanal...</p>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center space-y-4">
        <h2 className="font-serif text-2xl font-semibold text-carbon-500">Producto no encontrado</h2>
        <p className="text-sm text-gris-700">El producto solicitado no está disponible en este momento.</p>
        <Link to="/catalogo" className="inline-flex items-center gap-2 text-sm font-semibold text-petroleo-500 hover:underline">
          <ArrowLeft className="w-4 h-4" />
          <span>Volver al catálogo</span>
        </Link>
      </div>
    );
  }

  const isOutOfStock = product.stock <= 0;
  const maxChars = 40;

  const handleAddToCart = () => {
    addItem(product, quantity, {
      custom_message: customMessage.trim() || undefined,
    });
    setAddedAnimation(true);
    setTimeout(() => setAddedAnimation(false), 2000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Migas de Pan (Breadcrumbs) */}
      <nav className="flex items-center gap-2 text-xs text-gris-700">
        <Link to="/" className="hover:text-petroleo-500 transition-colors">Inicio</Link>
        <span>/</span>
        <Link to="/catalogo" className="hover:text-petroleo-500 transition-colors">Catálogo</Link>
        <span>/</span>
        <span className="font-medium text-carbon-500">{product.name}</span>
      </nav>

      {/* Grid de Detalle */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
        
        {/* Imagen Principal */}
        <div className="lg:col-span-6 bg-white rounded-2xl border border-crema-200 overflow-hidden shadow-sm aspect-square relative">
          <img
            src={product.image_url || '/assets/isotipo.svg'}
            alt={product.name}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '/assets/isotipo.svg';
            }}
          />
          {product.badge && (
            <span className="absolute top-4 left-4 bg-aguamarina-500 text-carbon-500 text-xs font-bold px-3 py-1 rounded-pill uppercase tracking-wider shadow-sm">
              {product.badge}
            </span>
          )}
        </div>

        {/* Información y Opciones de Compra */}
        <div className="lg:col-span-6 space-y-6">
          
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-aguamarina-700">
              {product.category_name || 'Pastelería Artesanal'}
            </span>
            <h1 className="font-serif text-3xl sm:text-4xl font-semibold text-carbon-500 mt-1">
              {product.name}
            </h1>
            <p className="font-bold text-3xl text-petroleo-500 tabular-nums mt-3">
              $ {product.price_cop.toLocaleString('es-CO')}{' '}
              <span className="text-sm font-normal text-gris-700">COP</span>
            </p>
          </div>

          <p className="text-sm sm:text-base text-gris-700 leading-relaxed">
            {product.description}
          </p>

          {/* Atributos Clave */}
          <div className="grid grid-cols-2 gap-4 py-4 border-y border-crema-200 text-xs">
            <div className="flex items-center gap-2 text-carbon-500 font-medium">
              <Users className="w-4 h-4 text-petroleo-500" />
              <span>Rendimiento: {product.servings}</span>
            </div>
            <div className="flex items-center gap-2 text-carbon-500 font-medium">
              <Clock className="w-4 h-4 text-petroleo-500" />
              <span>Tiempo de horneado: {product.prep_time_hours}h</span>
            </div>
          </div>

          {/* Alérgenos Declarados */}
          {product.allergens && product.allergens.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-carbon-500">
                <ShieldAlert className="w-4 h-4 text-coral-500" />
                <span>Alérgenos presentes:</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {product.allergens.map((allergen, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 bg-crema-200 text-carbon-500 rounded text-[11px] font-medium capitalize"
                  >
                    {allergen}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Campo de Dedicatoria Personalizada (Máximo 40 caracteres) */}
          <div className="space-y-1.5 bg-crema-100/60 p-4 rounded-lg border border-crema-200">
            <div className="flex justify-between items-center text-xs font-semibold text-carbon-500">
              <label htmlFor="customMessage">Dedicatoria en chocolate (Opcional):</label>
              <span className={`text-[11px] ${customMessage.length >= maxChars ? 'text-feedback-error' : 'text-gris-700'}`}>
                {customMessage.length}/{maxChars}
              </span>
            </div>
            <input
              id="customMessage"
              type="text"
              maxLength={maxChars}
              value={customMessage}
              onChange={(e) => setCustomMessage(e.target.value)}
              placeholder="Ej: ¡Feliz Cumpleaños Mamá!"
              className="w-full px-3 py-2 bg-white border border-crema-300 rounded-md text-sm text-carbon-500 placeholder-gris-700 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
            />
            <p className="text-[11px] text-gris-700">
              Se escribe a mano alzada en placa de chocolate blanco artesanal.
            </p>
          </div>

          {/* Selector de Cantidad y Botón de Compra */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-2">
            
            {/* Control Cantidad */}
            <div className="flex items-center border border-crema-300 rounded-md bg-white justify-between px-2 py-1 min-w-[120px]">
              <button
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                className="p-2 hover:bg-crema-200 text-gris-700 rounded min-w-[36px] min-h-[36px] flex items-center justify-center"
                aria-label="Restar una unidad"
              >
                <Minus className="w-4 h-4" />
              </button>
              <span className="font-bold text-sm text-carbon-500 tabular-nums">{quantity}</span>
              <button
                onClick={() => setQuantity((q) => Math.min(product.stock, q + 1))}
                disabled={quantity >= product.stock}
                className="p-2 hover:bg-crema-200 text-gris-700 disabled:opacity-40 rounded min-w-[36px] min-h-[36px] flex items-center justify-center"
                aria-label="Sumar una unidad"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            {/* Botón Agregar al Carrito */}
            <button
              onClick={handleAddToCart}
              disabled={isOutOfStock}
              className={`flex-1 py-3.5 px-6 rounded-md font-bold text-sm flex items-center justify-center gap-2 shadow-sm transition-all min-h-[44px] focus:outline-none focus:ring-2 focus:ring-petroleo-500 ${
                isOutOfStock
                  ? 'bg-crema-200 text-gris-700 cursor-not-allowed'
                  : addedAnimation
                  ? 'bg-menta-500 text-petroleo-500'
                  : 'bg-aguamarina-500 hover:bg-aguamarina-600 text-carbon-500'
              }`}
            >
              {isOutOfStock ? (
                <span>Agotado temporalmente</span>
              ) : addedAnimation ? (
                <>
                  <Check className="w-4 h-4" />
                  <span>¡Agregado a tu Canasta!</span>
                </>
              ) : (
                <>
                  <ShoppingBag className="w-4 h-4" />
                  <span>Agregar {quantity > 1 ? `(${quantity})` : ''} • $ {(product.price_cop * quantity).toLocaleString('es-CO')}</span>
                </>
              )}
            </button>
          </div>

          {/* Ingredientes y Conservación */}
          <div className="border-t border-crema-200 pt-4 space-y-2 text-xs text-gris-700">
            <p><strong>Ingredientes:</strong> {product.ingredients}</p>
            <p><strong>Conservación:</strong> Mantener refrigerado entre 4°C y 8°C. Consumir dentro de las 72 horas posteriores a la entrega.</p>
          </div>

        </div>

      </div>

    </div>
  );
};
