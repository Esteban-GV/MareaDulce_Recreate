import React from 'react';
import { BrowserRouter, Routes, Route, Outlet, Link } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import { SystemProvider } from './context/SystemContext';

import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { MaintenanceBanner } from './components/layout/MaintenanceBanner';
import { CartDrawer } from './components/cart/CartDrawer';
import { AdminLayout } from './components/layout/AdminLayout';

import { HomeView } from './views/HomeView';
import { CatalogView } from './views/CatalogView';
import { ProductDetailView } from './views/ProductDetailView';
import { CustomCakeView } from './views/CustomCakeView';
import { CheckoutView } from './views/CheckoutView';
import { OrderConfirmationView } from './views/OrderConfirmationView';
import { OrderTrackerView } from './views/OrderTrackerView';
import { LoginView } from './views/LoginView';

import { AdminDashboardView } from './views/admin/AdminDashboardView';
import { AdminOrdersView } from './views/admin/AdminOrdersView';
import { AdminProductsView } from './views/admin/AdminProductsView';
import { AdminInventoryView } from './views/admin/AdminInventoryView';

const StorefrontLayout: React.FC = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <MaintenanceBanner />
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <CartDrawer />
    </div>
  );
};

const NotFoundView: React.FC = () => {
  return (
    <div className="max-w-md mx-auto py-20 px-4 text-center space-y-4">
      <div className="w-16 h-16 rounded-full bg-menta-100 flex items-center justify-center mx-auto text-2xl font-serif font-bold text-petroleo-500">
        404
      </div>
      <h2 className="font-serif text-2xl font-semibold text-carbon-500">Receta no encontrada</h2>
      <p className="text-sm text-gris-700">La página que buscas no existe o fue movida a otra bandeja del horno.</p>
      <Link
        to="/"
        className="inline-block px-6 py-2.5 bg-aguamarina-500 text-carbon-500 font-bold rounded-md text-xs hover:bg-aguamarina-600 transition-colors"
      >
        Regresar al Inicio
      </Link>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <SystemProvider>
        <CartProvider>
          <BrowserRouter>
            <Routes>
              {/* Tienda Pública */}
              <Route path="/" element={<StorefrontLayout />}>
                <Route index element={<HomeView />} />
                <Route path="catalogo" element={<CatalogView />} />
                <Route path="producto/:slug" element={<ProductDetailView />} />
                <Route path="personalizados" element={<CustomCakeView />} />
                <Route path="checkout" element={<CheckoutView />} />
                <Route path="confirmacion/:orderNumber" element={<OrderConfirmationView />} />
                <Route path="seguimiento" element={<OrderTrackerView />} />
                <Route path="login" element={<LoginView />} />
                <Route path="*" element={<NotFoundView />} />
              </Route>

              {/* Panel Administrativo */}
              <Route path="/admin" element={<AdminLayout />}>
                <Route index element={<AdminDashboardView />} />
                <Route path="pedidos" element={<AdminOrdersView />} />
                <Route path="productos" element={<AdminProductsView />} />
                <Route path="inventario" element={<AdminInventoryView />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </CartProvider>
      </SystemProvider>
    </AuthProvider>
  );
};

export default App;
