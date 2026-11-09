import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Product, Category } from '../types';
import { fetchProducts, fetchCategories } from '../services/api';
import { ProductCard } from '../components/catalog/ProductCard';
import { Search, Filter, AlertCircle, CheckCircle } from 'lucide-react';

export const CatalogView: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedCategory = searchParams.get('category') || '';
  
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [onlyInStock, setOnlyInStock] = useState(false);
  const [sortBy, setSortBy] = useState<'featured' | 'price_asc' | 'price_desc'>('featured');
  const [loading, setLoading] = useState(true);
  const [isCached, setIsCached] = useState(false);

  useEffect(() => {
    fetchCategories().then((res) => setCategories(res.data));
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchProducts({
      category: selectedCategory || undefined,
      search: searchTerm || undefined,
      only_in_stock: onlyInStock,
    }).then((res) => {
      setProducts(res.data);
      setIsCached(res.isCached);
      setLoading(false);
    });
  }, [selectedCategory, searchTerm, onlyInStock]);

  const handleCategoryChange = (slug: string) => {
    if (slug) {
      setSearchParams({ category: slug });
    } else {
      setSearchParams({});
    }
  };

  const sortedProducts = [...products].sort((a, b) => {
    if (sortBy === 'price_asc') return a.price_cop - b.price_cop;
    if (sortBy === 'price_desc') return b.price_cop - a.price_cop;
    return (b.is_featured ? 1 : 0) - (a.is_featured ? 1 : 0);
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      
      {/* Encabezado del Catálogo */}
      <div className="text-center max-w-2xl mx-auto space-y-2">
        <h1 className="font-serif text-3xl sm:text-4xl font-semibold text-petroleo-500">
          Catálogo de Repostería Artesanal
        </h1>
        <p className="text-sm text-gris-700">
          Selecciona tus postres y tortas favoritas. Horneamos cada mañana bajo pedido.
        </p>

        {isCached && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-menta-100 border border-menta-500/50 rounded-pill text-xs text-petroleo-500 font-medium mt-2">
            <CheckCircle className="w-3.5 h-3.5 text-aguamarina-700" />
            <span>Mostrando catálogo guardado en tu dispositivo.</span>
          </div>
        )}
      </div>

      {/* Barra de Filtros y Búsqueda */}
      <div className="bg-white p-4 rounded-lg border border-crema-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Buscador */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-gris-700 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por sabor, nombre..."
            className="w-full pl-9 pr-4 py-2 bg-crema-100/60 border border-crema-300 rounded-md text-sm text-carbon-500 placeholder-gris-700 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
          />
        </div>

        {/* Opciones de Filtro y Orden */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto justify-between md:justify-end">
          <label className="flex items-center gap-2 text-xs font-medium text-carbon-500 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={onlyInStock}
              onChange={(e) => setOnlyInStock(e.target.checked)}
              className="rounded border-crema-300 text-petroleo-500 focus:ring-petroleo-500 w-4 h-4"
            />
            <span>Solo disponibles</span>
          </label>

          <div className="flex items-center gap-2 text-xs text-gris-700">
            <Filter className="w-3.5 h-3.5" />
            <span>Ordenar:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-crema-100/60 border border-crema-300 rounded-md py-1.5 px-2.5 text-xs text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500 font-medium"
            >
              <option value="featured">Destacados</option>
              <option value="price_asc">Precio: menor a mayor</option>
              <option value="price_desc">Precio: mayor a menor</option>
            </select>
          </div>
        </div>

      </div>

      {/* Píldoras de Categorías */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        <button
          onClick={() => handleCategoryChange('')}
          className={`px-4 py-2 rounded-pill text-xs font-semibold whitespace-nowrap transition-all ${
            !selectedCategory
              ? 'bg-petroleo-500 text-crema-100 shadow-sm'
              : 'bg-white text-carbon-500 border border-crema-200 hover:bg-crema-200'
          }`}
        >
          Todos los Productos ({products.length})
        </button>

        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => handleCategoryChange(cat.slug)}
            className={`px-4 py-2 rounded-pill text-xs font-semibold whitespace-nowrap transition-all ${
              selectedCategory === cat.slug
                ? 'bg-petroleo-500 text-crema-100 shadow-sm'
                : 'bg-white text-carbon-500 border border-crema-200 hover:bg-crema-200'
            }`}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {/* Grilla de Productos */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
            <div key={n} className="bg-white rounded-lg border border-crema-200 p-4 space-y-3 animate-pulse">
              <div className="aspect-[4/5] bg-crema-200 rounded-md" />
              <div className="h-4 bg-crema-200 rounded w-3/4" />
              <div className="h-3 bg-crema-200 rounded w-1/2" />
              <div className="h-8 bg-crema-200 rounded mt-4" />
            </div>
          ))}
        </div>
      ) : sortedProducts.length === 0 ? (
        <div className="bg-white rounded-xl border border-crema-200 p-12 text-center max-w-md mx-auto space-y-3">
          <AlertCircle className="w-10 h-10 text-gris-700 mx-auto" />
          <h3 className="font-serif text-lg font-semibold text-carbon-500">No encontramos resultados</h3>
          <p className="text-xs text-gris-700">
            Intenta buscando con otra palabra o limpiando los filtros seleccionados.
          </p>
          <button
            onClick={() => {
              setSearchTerm('');
              handleCategoryChange('');
              setOnlyInStock(false);
            }}
            className="px-4 py-2 bg-aguamarina-500 text-carbon-500 font-semibold text-xs rounded-md hover:bg-aguamarina-600 transition-colors"
          >
            Limpiar Filtros
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {sortedProducts.map((prod) => (
            <ProductCard key={prod.id} product={prod} />
          ))}
        </div>
      )}

    </div>
  );
};
