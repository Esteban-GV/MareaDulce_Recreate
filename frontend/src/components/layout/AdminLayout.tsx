import React from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useSystem } from '../../context/SystemContext';
import { LayoutDashboard, ShoppingBag, Layers, Warehouse, Store, LogOut, Wifi, WifiOff } from 'lucide-react';

export const AdminLayout: React.FC = () => {
  const { user, isAdmin, logout } = useAuth();
  const { isOnline, isReconnecting } = useSystem();
  const location = useLocation();
  const navigate = useNavigate();

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-crema-100 flex items-center justify-center p-4">
        <div className="bg-white p-8 rounded-xl border border-crema-200 text-center space-y-4 max-w-md shadow-sm">
          <h2 className="font-serif text-2xl font-bold text-petroleo-500">Acceso Administrativo Requerido</h2>
          <p className="text-sm text-gris-700">Debes iniciar sesión con una cuenta con rol de Administrador para ver este panel.</p>
          <button
            onClick={() => navigate('/login')}
            className="px-6 py-2.5 bg-aguamarina-500 text-carbon-500 font-bold rounded-md text-xs hover:bg-aguamarina-600 transition-colors"
          >
            Ir a Inicio de Sesión
          </button>
        </div>
      </div>
    );
  }

  const navItems = [
    { path: '/admin', label: 'Resumen & KPIs', icon: LayoutDashboard },
    { path: '/admin/pedidos', label: 'Gestión de Pedidos', icon: ShoppingBag },
    { path: '/admin/productos', label: 'Catálogo de Productos', icon: Layers },
    { path: '/admin/inventario', label: 'Control de Inventario', icon: Warehouse },
  ];

  return (
    <div className="min-h-screen bg-[#F4F8F6] flex flex-col md:flex-row text-carbon-500">
      
      {/* Barra Lateral Petróleo */}
      <aside className="w-full md:w-64 bg-petroleo-500 text-crema-100 flex flex-col justify-between flex-shrink-0 shadow-lg">
        <div>
          {/* Logo Admin */}
          <div className="p-6 border-b border-petroleo-600 flex items-center gap-3">
            <img src="/assets/isotipo.svg" alt="Marea Dulce" className="w-8 h-8" />
            <div>
              <span className="font-serif text-xl font-bold tracking-tight text-white">Marea Dulce</span>
              <p className="text-[10px] text-aguamarina-300 font-medium uppercase tracking-wider">Panel Administrativo</p>
            </div>
          </div>

          {/* Menú de Navegación */}
          <nav className="p-4 space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-aguamarina-500/20 text-white border-l-4 border-aguamarina-500 font-semibold'
                      : 'text-crema-200 hover:bg-petroleo-600 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4 text-aguamarina-300" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Footer Barra Lateral */}
        <div className="p-4 border-t border-petroleo-600 space-y-3">
          <Link
            to="/"
            className="flex items-center gap-2 px-3 py-2 text-xs font-semibold text-crema-200 hover:text-white rounded-md hover:bg-petroleo-600 transition-colors"
          >
            <Store className="w-4 h-4 text-aguamarina-300" />
            <span>Volver a la Tienda</span>
          </Link>

          <button
            onClick={() => {
              logout();
              navigate('/');
            }}
            className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-coral-500 hover:bg-petroleo-600 rounded-md transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      {/* Contenido Principal */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* Barra Superior con Estado del Backend (Sección 1.8) */}
        <header className="h-16 bg-white border-b border-crema-200 px-6 flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-3">
            <h1 className="font-serif text-lg font-semibold text-petroleo-500">
              Operaciones y Control Transaccional
            </h1>
          </div>

          <div className="flex items-center gap-4">
            {/* Indicador de Estado del Backend en Vivo */}
            <div className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-pill border bg-crema-100">
              {isOnline ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-feedback-exito animate-pulse" />
                  <span className="text-petroleo-500 font-semibold">Backend Conectado</span>
                  <Wifi className="w-3.5 h-3.5 text-feedback-exito ml-1" />
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-feedback-advertencia animate-ping" />
                  <span className="text-feedback-advertencia font-bold">
                    {isReconnecting ? 'Reconectando...' : 'Recreate Rollout en Curso'}
                  </span>
                  <WifiOff className="w-3.5 h-3.5 text-feedback-advertencia ml-1" />
                </>
              )}
            </div>

            <div className="text-right text-xs">
              <span className="text-gris-700">Admin: </span>
              <span className="font-semibold text-carbon-500">{user?.full_name}</span>
            </div>
          </div>
        </header>

        {/* Vistas Anidadas */}
        <main className="flex-1 p-6 lg:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>

    </div>
  );
};
