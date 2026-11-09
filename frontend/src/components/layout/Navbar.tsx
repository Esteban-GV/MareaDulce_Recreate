import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../../context/CartContext';
import { useAuth } from '../../context/AuthContext';
import { useSystem } from '../../context/SystemContext';
import { ShoppingBag, User, Menu, X, Shield, LogOut } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { totalItems, openDrawer } = useCart();
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const { version } = useSystem();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-40 bg-crema-100/95 backdrop-blur-md border-b border-crema-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          
          {/* Logotipo Oficial con Badge de Versión */}
          <Link to="/" className="flex items-center gap-3 group focus:outline-none focus:ring-2 focus:ring-petroleo-500 rounded-lg p-1">
            <img
              src="/assets/isotipo.svg"
              alt="Isotipo Marea Dulce"
              className="w-10 h-10 object-contain transition-transform group-hover:scale-105"
            />
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-serif text-2xl font-semibold text-petroleo-500 tracking-tight leading-none">
                  Marea Dulce
                </span>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold tracking-wide border shadow-sm ${
                    version.startsWith('2')
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-400'
                      : 'bg-aguamarina-500/20 text-petroleo-500 border-aguamarina-500/40'
                  }`}
                  title={`Versión activa en Kubernetes: v${version}`}
                >
                  v{version}
                </span>
              </div>
              <span className="font-sans text-[10px] font-medium text-gris-700 tracking-wider uppercase mt-1">
                Pastelería Artesanal · K8s Recreate
              </span>
            </div>
          </Link>

          {/* Navegación Escritorio */}
          <nav className="hidden md:flex items-center gap-8 font-medium text-sm text-petroleo-500">
            <Link to="/" className="hover:text-aguamarina-700 transition-colors py-2">
              Inicio
            </Link>
            <Link to="/catalogo" className="hover:text-aguamarina-700 transition-colors py-2">
              Catálogo
            </Link>
            <Link to="/personalizados" className="hover:text-aguamarina-700 transition-colors py-2">
              Tortas Personalizadas
            </Link>
            <Link to="/seguimiento" className="hover:text-aguamarina-700 transition-colors py-2">
              Seguir Pedido
            </Link>
            {isAdmin && (
              <Link
                to="/admin"
                className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 bg-menta-500 text-petroleo-500 rounded-pill border border-aguamarina-500/30 hover:bg-aguamarina-300 transition-colors"
              >
                <Shield className="w-3.5 h-3.5" />
                Panel Admin
              </Link>
            )}
          </nav>

          {/* Acciones del Usuario & Carrito */}
          <div className="flex items-center gap-3">
            {/* Botón Carrito */}
            <button
              onClick={openDrawer}
              className="relative p-2.5 rounded-full hover:bg-crema-200 text-petroleo-500 transition-colors focus:outline-none focus:ring-2 focus:ring-petroleo-500 min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label="Abrir carrito de compras"
            >
              <ShoppingBag className="w-6 h-6" />
              {totalItems > 0 && (
                <span className="absolute top-1 right-1 bg-aguamarina-500 text-carbon-500 font-bold text-xs w-5 h-5 rounded-full flex items-center justify-center border-2 border-crema-100 shadow-sm">
                  {totalItems}
                </span>
              )}
            </button>

            {/* Usuario / Login */}
            {isAuthenticated ? (
              <div className="relative group">
                <button
                  className="flex items-center gap-2 p-2 rounded-full hover:bg-crema-200 text-petroleo-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500 min-w-[44px] min-h-[44px]"
                  title={`Conectado como ${user?.full_name}`}
                >
                  <div className="w-8 h-8 rounded-full bg-aguamarina-500 text-carbon-500 flex items-center justify-center font-bold text-xs uppercase">
                    {user?.full_name.charAt(0)}
                  </div>
                </button>
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-crema-200 py-1 hidden group-hover:block z-50">
                  <div className="px-4 py-2 border-b border-crema-200">
                    <p className="text-xs font-medium text-gris-700">Hola,</p>
                    <p className="text-sm font-semibold text-carbon-500 truncate">{user?.full_name}</p>
                  </div>
                  {isAdmin && (
                    <Link
                      to="/admin"
                      className="block px-4 py-2 text-sm text-petroleo-500 hover:bg-menta-100 transition-colors"
                    >
                      Panel Administrativo
                    </Link>
                  )}
                  <button
                    onClick={() => {
                      logout();
                      navigate('/');
                    }}
                    className="w-full text-left px-4 py-2 text-sm text-feedback-error hover:bg-feedback-error-bg flex items-center gap-2"
                  >
                    <LogOut className="w-4 h-4" />
                    Cerrar Sesión
                  </button>
                </div>
              </div>
            ) : (
              <Link
                to="/login"
                className="hidden sm:inline-flex items-center gap-2 px-4 py-2 rounded-md font-medium text-sm text-carbon-500 bg-aguamarina-500 hover:bg-aguamarina-600 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-petroleo-500 min-h-[44px]"
              >
                <User className="w-4 h-4" />
                Ingresar
              </Link>
            )}

            {/* Menú Móvil Hamburguesa */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-petroleo-500 hover:bg-crema-200 min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label="Abrir menú de navegación"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Menú Móvil Desplegable */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-crema-200 flex flex-col gap-3 font-medium text-petroleo-500">
            <Link
              to="/"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-md hover:bg-crema-200"
            >
              Inicio
            </Link>
            <Link
              to="/catalogo"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-md hover:bg-crema-200"
            >
              Catálogo Completo
            </Link>
            <Link
              to="/personalizados"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-md hover:bg-crema-200"
            >
              Tortas Personalizadas
            </Link>
            <Link
              to="/seguimiento"
              onClick={() => setMobileMenuOpen(false)}
              className="px-3 py-2 rounded-md hover:bg-crema-200"
            >
              Seguimiento de Pedidos
            </Link>
            {isAdmin && (
              <Link
                to="/admin"
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2 rounded-md bg-menta-500 text-petroleo-500 font-semibold"
              >
                Panel de Administración
              </Link>
            )}
            {!isAuthenticated && (
              <Link
                to="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2.5 rounded-md bg-aguamarina-500 text-carbon-500 text-center font-semibold mt-2"
              >
                Iniciar Sesión
              </Link>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
