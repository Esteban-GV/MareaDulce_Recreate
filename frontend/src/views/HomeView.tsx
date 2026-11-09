import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Product, Category } from '../types';
import { fetchProducts, fetchCategories } from '../services/api';
import { ProductCard } from '../components/catalog/ProductCard';
import { ArrowRight, Sparkles, Clock, Heart, Award, CheckCircle } from 'lucide-react';

export const HomeView: React.FC = () => {
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isCached, setIsCached] = useState(false);

  useEffect(() => {
    fetchProducts({ featured: true }).then((res) => {
      setFeaturedProducts(res.data.slice(0, 4));
      setIsCached(res.isCached);
    });
    fetchCategories().then((res) => {
      setCategories(res.data);
    });
  }, []);

  return (
    <div className="space-y-16">
      
      {/* Banner de Aviso si se muestra desde caché */}
      {isCached && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-menta-100 border border-menta-500/50 rounded-lg p-2.5 text-xs text-petroleo-500 flex items-center justify-center gap-2">
            <CheckCircle className="w-4 h-4 text-aguamarina-700" />
            <span>Mostrando catálogo guardado en tu navegador. La disponibilidad y precios se confirman al finalizar la compra.</span>
          </div>
        </div>
      )}

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-8 pb-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            
            <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-pill bg-menta-500/70 text-petroleo-500 text-xs font-semibold tracking-wide border border-aguamarina-500/30">
                <Sparkles className="w-3.5 h-3.5 text-coral-500" />
                <span>Repostería de Autor &amp; Hecha Cada Día</span>
              </div>

              <h1 className="font-serif text-4xl sm:text-5xl lg:text-6xl font-semibold text-carbon-500 tracking-tight leading-[1.15]">
                Pequeños antojos, <br />
                <span className="text-petroleo-500 italic">grandes momentos.</span>
              </h1>

              <p className="text-base sm:text-lg text-gris-700 max-w-xl mx-auto lg:mx-0 leading-relaxed">
                Pastelería artesanal hecha cada día con ingredientes frescos, recetas tradicionales y un toque de mar que transforma tus celebraciones en recuerdos inolvidables.
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 pt-2">
                <Link
                  to="/catalogo"
                  className="w-full sm:w-auto px-6 py-3.5 bg-aguamarina-500 hover:bg-aguamarina-600 text-carbon-500 font-bold rounded-md shadow-sm transition-all flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-petroleo-500 min-h-[44px]"
                >
                  <span>Ver el Catálogo</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>

                <Link
                  to="/personalizados"
                  className="w-full sm:w-auto px-6 py-3.5 bg-white hover:bg-crema-200 text-petroleo-500 font-semibold rounded-md border border-crema-300 transition-all flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-petroleo-500 min-h-[44px]"
                >
                  <span>Pedir una Torta Personalizada</span>
                </Link>
              </div>
            </div>

            {/* Imagen Principal Hero */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md lg:max-w-none rounded-2xl overflow-hidden shadow-xl border-4 border-white bg-menta-100 aspect-square">
                <img
                  src="/assets/products/torta-frutos-rojos.webp"
                  alt="Torta artesanal de frutos rojos Marea Dulce"
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = '/assets/isotipo.svg';
                  }}
                />
                <div className="absolute bottom-4 left-4 right-4 bg-white/90 backdrop-blur-md p-3 rounded-lg border border-crema-200 shadow-sm flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold text-carbon-500">Torta de Vainilla y Frutos Rojos</p>
                    <p className="text-[11px] text-gris-700">12 porciones • Nuestra especialidad</p>
                  </div>
                  <span className="font-bold text-petroleo-500 text-sm">$ 98.000</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* Categorías Principales */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <h2 className="font-serif text-2xl sm:text-3xl font-semibold text-petroleo-500">
            Nuestras Creaciones Artesanales
          </h2>
          <p className="text-sm text-gris-700 mt-2">
            Cada receta se hornea el mismo día con ingredientes de origen seleccionados.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {categories.map((cat) => (
            <Link
              key={cat.id}
              to={`/catalogo?category=${cat.slug}`}
              className="group p-4 bg-white rounded-lg border border-crema-200 hover:border-aguamarina-500 text-center flex flex-col items-center justify-center gap-2 shadow-sm hover:shadow transition-all"
            >
              <div className="w-12 h-12 rounded-full bg-menta-100 group-hover:bg-aguamarina-300 flex items-center justify-center transition-colors">
                <img src="/assets/isotipo.svg" alt={cat.name} className="w-6 h-6 object-contain" />
              </div>
              <span className="font-serif text-sm font-semibold text-carbon-500 group-hover:text-petroleo-500 transition-colors">
                {cat.name}
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* Productos Destacados */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-end justify-between mb-8">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-aguamarina-700">Selección de la Casa</span>
            <h2 className="font-serif text-2xl sm:text-3xl font-semibold text-petroleo-500 mt-1">
              Favoritos de la Temporada
            </h2>
          </div>
          <Link
            to="/catalogo"
            className="text-sm font-semibold text-petroleo-500 hover:text-aguamarina-700 flex items-center gap-1 transition-colors"
          >
            <span>Ver todo el catálogo</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {featuredProducts.map((prod) => (
            <ProductCard key={prod.id} product={prod} />
          ))}
        </div>
      </section>

      {/* Banda Promocional en Coral con Texto Carbón */}
      <section className="bg-coral-500 py-6 text-carbon-500 shadow-inner">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center flex flex-col sm:flex-row items-center justify-center gap-4 font-medium text-sm sm:text-base">
          <span className="bg-white/80 px-3 py-1 rounded-pill text-xs font-bold uppercase tracking-wider text-carbon-500">
            Aviso de Demostración
          </span>
          <p className="font-medium">
            Entregas programadas en Bogotá. Todos los pedidos y pagos se procesan en modo de prueba técnica.
          </p>
        </div>
      </section>

      {/* Nuestra Historia / Valores */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-2xl border border-crema-200 p-8 sm:p-12 shadow-sm grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          
          <div className="lg:col-span-6 space-y-4">
            <span className="text-xs font-bold uppercase tracking-wider text-aguamarina-700">Tradición y Esmero</span>
            <h2 className="font-serif text-3xl font-semibold text-petroleo-500 leading-tight">
              Horneamos con paciencia, creamos con dulzura
            </h2>
            <p className="text-sm text-gris-700 leading-relaxed">
              Marea Dulce nació como un homenaje a los momentos compartidos en familia alrededor de una mesa. Cada batido, cada relleno y cada detalle decorativo se realiza de forma manual en nuestro taller, sin premezclas industriales ni conservantes artificiales.
            </p>

            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-crema-200 text-center">
              <div className="space-y-1">
                <Heart className="w-5 h-5 text-coral-500 mx-auto" />
                <p className="font-serif text-sm font-semibold text-carbon-500">100% Artesanal</p>
                <p className="text-[11px] text-gris-700">Hecho a mano</p>
              </div>
              <div className="space-y-1">
                <Award className="w-5 h-5 text-aguamarina-700 mx-auto" />
                <p className="font-serif text-sm font-semibold text-carbon-500">Ingredientes Puros</p>
                <p className="text-[11px] text-gris-700">Mantequilla de campo</p>
              </div>
              <div className="space-y-1">
                <Clock className="w-5 h-5 text-petroleo-500 mx-auto" />
                <p className="font-serif text-sm font-semibold text-carbon-500">Frescura Diaria</p>
                <p className="text-[11px] text-gris-700">Horneado el mismo día</p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-6">
            <div className="rounded-xl overflow-hidden bg-menta-100 border border-crema-200 aspect-[16/10]">
              <img
                src="/assets/products/torta-chocolate.webp"
                alt="Elaboración de pasteles artesanales"
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/assets/isotipo.svg';
                }}
              />
            </div>
          </div>

        </div>
      </section>

      {/* Testimonios */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-xl mx-auto mb-8">
          <span className="text-xs font-bold uppercase tracking-wider text-aguamarina-700">Experiencias</span>
          <h2 className="font-serif text-2xl sm:text-3xl font-semibold text-petroleo-500 mt-1">
            Lo que dicen nuestros clientes
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 bg-white rounded-lg border border-crema-200 shadow-sm space-y-3">
            <p className="text-xs text-gris-700 italic">
              «La torta de frutos rojos fue la protagonista del cumpleaños de mi madre. La textura esponjosa y el balance de dulce son insuperables.»
            </p>
            <div className="pt-2 border-t border-crema-200">
              <p className="font-semibold text-xs text-carbon-500">Camila Restrepo</p>
              <p className="text-[10px] text-gris-700">Cliente verificada</p>
            </div>
          </div>

          <div className="p-6 bg-white rounded-lg border border-crema-200 shadow-sm space-y-3">
            <p className="text-xs text-gris-700 italic">
              «Los cupcakes de Red Velvet tienen el mejor frosting de queso crema que he probado en Bogotá. Todo llegó puntual y perfectamente empacado.»
            </p>
            <div className="pt-2 border-t border-crema-200">
              <p className="font-semibold text-xs text-carbon-500">Julián Peñaranda</p>
              <p className="text-[10px] text-gris-700">Cliente verificado</p>
            </div>
          </div>

          <div className="p-6 bg-white rounded-lg border border-crema-200 shadow-sm space-y-3">
            <p className="text-xs text-gris-700 italic">
              «Solicitamos una torta personalizada para nuestro aniversario y plasmaron exactamente la idea. Además, el sabor de tres leches es delicioso.»
            </p>
            <div className="pt-2 border-t border-crema-200">
              <p className="font-semibold text-xs text-carbon-500">Natalia &amp; Santiago</p>
              <p className="text-[10px] text-gris-700">Clientes verificados</p>
            </div>
          </div>
        </div>
      </section>

    </div>
  );
};
