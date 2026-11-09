import React from 'react';
import { Link } from 'react-router-dom';
import { Product } from '../../types';
import { useCart } from '../../context/CartContext';
import { Plus, AlertCircle } from 'lucide-react';

interface ProductCardProps {
  product: Product;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  const { addItem } = useCart();
  const isOutOfStock = product.stock <= 0;

  const getBadgeStyle = (badge?: string) => {
    switch (badge?.toLowerCase()) {
      case 'destacado':
        return 'bg-aguamarina-500 text-carbon-500 font-bold';
      case 'popular':
        return 'bg-coral-500 text-carbon-500 font-bold';
      case 'nuevo':
        return 'bg-menta-500 text-petroleo-500 font-bold';
      case 'bajo stock':
        return 'bg-vainilla-500 text-carbon-500 font-bold';
      case 'temporada':
        return 'bg-petroleo-500 text-crema-100 font-bold';
      default:
        return 'bg-crema-200 text-gris-700';
    }
  };

  return (
    <div className="group bg-white rounded-lg border border-crema-200 overflow-hidden shadow-sm hover:shadow-md transition-all duration-200 flex flex-col h-full">
      {/* Imagen con Aspect Ratio 4:5 y Badge */}
      <Link to={`/producto/${product.slug}`} className="relative block aspect-[4/5] bg-menta-100 overflow-hidden">
        <img
          src={product.image_url || '/assets/isotipo.svg'}
          alt={product.name}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          onError={(e) => {
            (e.target as HTMLImageElement).src = '/assets/isotipo.svg';
          }}
        />
        {/* Badge Superior */}
        {product.badge && (
          <div className="absolute top-3 left-3">
            <span className={`text-[11px] px-2.5 py-1 rounded-pill uppercase tracking-wider ${getBadgeStyle(product.badge)}`}>
              {product.badge}
            </span>
          </div>
        )}
        {/* Aviso Agotado */}
        {isOutOfStock && (
          <div className="absolute inset-0 bg-carbon-500/60 backdrop-blur-[2px] flex items-center justify-center p-4">
            <span className="px-3 py-1.5 bg-white text-carbon-500 text-xs font-bold rounded-pill uppercase tracking-wider flex items-center gap-1.5 shadow-md">
              <AlertCircle className="w-3.5 h-3.5 text-feedback-error" />
              Agotado
            </span>
          </div>
        )}
      </Link>

      {/* Contenido de la Tarjeta */}
      <div className="p-4 flex flex-col flex-1 justify-between gap-3">
        <div>
          <div className="flex items-center justify-between text-xs text-gris-700 mb-1">
            <span>{product.category_name || 'Pastelería'}</span>
            <span className="text-[11px] font-medium">{product.servings}</span>
          </div>

          <Link to={`/producto/${product.slug}`}>
            <h3 className="font-serif text-base font-semibold text-carbon-500 group-hover:text-petroleo-500 transition-colors line-clamp-1">
              {product.name}
            </h3>
          </Link>

          <p className="text-xs text-gris-700 mt-1 line-clamp-2 leading-relaxed">
            {product.description}
          </p>
        </div>

        {/* Precio y Botón Agregar */}
        <div className="pt-2 border-t border-crema-200 flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-[10px] uppercase text-gris-700 font-semibold tracking-wider">Precio</span>
            <span className="font-bold text-lg text-petroleo-500 tabular-nums">
              $ {product.price_cop.toLocaleString('es-CO')}
            </span>
          </div>

          <button
            onClick={() => addItem(product, 1)}
            disabled={isOutOfStock}
            className="inline-flex items-center justify-center gap-1.5 px-3 py-2 bg-aguamarina-500 hover:bg-aguamarina-600 disabled:bg-crema-200 disabled:text-gris-700 text-carbon-500 font-semibold text-xs rounded-md shadow-sm transition-all min-h-[40px] focus:outline-none focus:ring-2 focus:ring-petroleo-500"
            aria-label={`Agregar ${product.name} a la canasta`}
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{isOutOfStock ? 'Sin Stock' : 'Agregar'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
