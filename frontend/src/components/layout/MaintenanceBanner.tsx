import React, { useState, useEffect } from 'react';
import { useSystem } from '../../context/SystemContext';
import { RefreshCw, CheckCircle, Info } from 'lucide-react';

export const MaintenanceBanner: React.FC = () => {
  const { isOnline, justRestored, isReconnecting, checkHealth } = useSystem();
  const [countdown, setCountdown] = useState<number>(5);

  useEffect(() => {
    if (isOnline) {
      setCountdown(5);
      return;
    }
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          checkHealth();
          return 5;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [isOnline, checkHealth]);

  if (justRestored) {
    return (
      <div className="bg-menta-500 border-b border-aguamarina-500 px-4 py-2.5 text-center text-sm font-medium text-petroleo-500 flex items-center justify-center gap-2 transition-all">
        <CheckCircle className="w-4 h-4 text-feedback-exito" />
        <span>¡Listo, ya estamos de vuelta! Puedes continuar con tu compra normalmente.</span>
      </div>
    );
  }

  if (isOnline) {
    return null;
  }

  return (
    <div className="bg-vainilla-500 border-b border-[#E0C680] px-4 py-2.5 text-center text-sm text-carbon-500 flex flex-wrap items-center justify-center gap-3 shadow-sm transition-all">
      <div className="flex items-center gap-2 font-medium">
        <Info className="w-4 h-4 text-feedback-advertencia" />
        <span>Estamos actualizando la tienda. Tu carrito está guardado en tu dispositivo.</span>
      </div>
      <div className="flex items-center gap-2 text-xs">
        <span className="text-gris-700">Reintentando en {countdown}s</span>
        <button
          onClick={() => checkHealth()}
          disabled={isReconnecting}
          className="inline-flex items-center gap-1 px-2.5 py-1 bg-crema-100 hover:bg-white text-carbon-500 font-semibold rounded-md border border-crema-300 transition-colors"
        >
          <RefreshCw className={`w-3 h-3 ${isReconnecting ? 'animate-spin' : ''}`} />
          {isReconnecting ? 'Conectando...' : 'Reintentar ahora'}
        </button>
      </div>
    </div>
  );
};
