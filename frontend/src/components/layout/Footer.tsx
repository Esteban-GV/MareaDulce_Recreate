import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, Sparkles, ShieldCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="relative bg-[#F9F3E9] text-carbon-500 border-t border-crema-200 mt-20">
      {/* Patrón de onda decorativa en la parte superior */}
      <div className="w-full h-8 overflow-hidden -mt-8 pointer-events-none">
        <svg viewBox="0 0 1440 48" fill="none" className="w-full h-full preserve-3d" preserveAspectRatio="none">
          <path d="M0,24 C360,48 720,0 1080,24 C1260,36 1380,12 1440,16 L1440,48 L0,48 Z" fill="#F9F3E9"/>
        </svg>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          
          {/* Columna 1: Marca y Propósito */}
          <div className="md:col-span-1 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <img src="/assets/isotipo.svg" alt="Marea Dulce" className="w-8 h-8" />
              <span className="font-serif text-2xl font-semibold text-petroleo-500">Marea Dulce</span>
            </div>
            <p className="text-sm text-gris-700 italic">
              «Pequeños antojos, grandes momentos.»
            </p>
            <p className="text-xs text-gris-700 mt-2 leading-relaxed">
              Pastelería artesanal hecha cada día con ingredientes frescos y dedicación.
            </p>
          </div>

          {/* Columna 2: Categorías Principales */}
          <div>
            <h3 className="font-serif text-base font-semibold text-petroleo-500 mb-3">Nuestra Repostería</h3>
            <ul className="space-y-2 text-sm text-gris-700">
              <li><Link to="/catalogo?category=tortas" className="hover:text-petroleo-500 transition-colors">Tortas y Pasteles</Link></li>
              <li><Link to="/catalogo?category=cupcakes" className="hover:text-petroleo-500 transition-colors">Cupcakes Gourmet</Link></li>
              <li><Link to="/catalogo?category=galletas" className="hover:text-petroleo-500 transition-colors">Galletas Artesanales</Link></li>
              <li><Link to="/catalogo?category=postres-individuales" className="hover:text-petroleo-500 transition-colors">Postres Individuales</Link></li>
              <li><Link to="/personalizados" className="hover:text-petroleo-500 transition-colors">Pedidos Personalizados</Link></li>
            </ul>
          </div>

          {/* Columna 3: Información y Horarios */}
          <div>
            <h3 className="font-serif text-base font-semibold text-petroleo-500 mb-3">Atención y Pedidos</h3>
            <div className="space-y-2 text-sm text-gris-700">
              <p>📍 Carrera 15 # 85-30, Bogotá (Demo)</p>
              <p>⏰ Martes a Domingo: 8:00 AM – 7:00 PM</p>
              <p>🚚 Envíos locales y recogida en tienda</p>
              <Link to="/seguimiento" className="inline-block text-petroleo-500 font-medium hover:underline mt-1">
                Consultar estado de pedido →
              </Link>
            </div>
          </div>

          {/* Columna 4: Transparencia Técnica Cloud-Native */}
          <div className="bg-menta-100 p-4 rounded-lg border border-menta-500/40">
            <div className="flex items-center gap-2 text-petroleo-500 font-semibold text-sm mb-2">
              <ShieldCheck className="w-4 h-4 text-aguamarina-700" />
              <span>Plataforma Cloud-Native</span>
            </div>
            <p className="text-xs text-gris-700 leading-relaxed mb-3">
              Desplegada en Kubernetes con estrategia <strong>Recreate</strong>, persistencia SQLite en PVC y alta disponibilidad de catálogo.
            </p>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-white text-[11px] font-medium text-petroleo-500 border border-crema-300">
              <Sparkles className="w-3 h-3 text-coral-500" />
              <span>Demostración Académica</span>
            </div>
          </div>
        </div>

        {/* Barra Inferior */}
        <div className="border-t border-crema-200 mt-10 pt-6 flex flex-col sm:flex-row items-center justify-between text-xs text-gris-700 gap-4">
          <p>© 2026 Marea Dulce. Todos los derechos reservados. Tienda de demostración. Los pagos son simulados.</p>
          <div className="flex items-center gap-1 text-gris-700">
            <span>Hecho con</span>
            <Heart className="w-3.5 h-3.5 text-coral-500 fill-coral-500" />
            <span>para Kubernetes Recreate Stack</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
