import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { checkBackendHealth } from '../services/api';

interface SystemContextType {
  isOnline: boolean;
  isReconnecting: boolean;
  justRestored: boolean;
  checkHealth: () => Promise<boolean>;
}

const SystemContext = createContext<SystemContextType | undefined>(undefined);

export const SystemProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [isReconnecting, setIsReconnecting] = useState<boolean>(false);
  const [justRestored, setJustRestored] = useState<boolean>(false);

  const checkHealth = useCallback(async (): Promise<boolean> => {
    setIsReconnecting(true);
    const healthy = await checkBackendHealth();
    setIsReconnecting(false);

    if (!healthy && isOnline) {
      setIsOnline(false);
      setJustRestored(false);
    } else if (healthy && !isOnline) {
      setIsOnline(true);
      setJustRestored(true);
      setTimeout(() => setJustRestored(false), 6000);
    }
    return healthy;
  }, [isOnline]);

  useEffect(() => {
    // Verificación inicial y sondeo periódico cada 4 segundos
    checkHealth();
    const interval = setInterval(() => {
      checkHealth();
    }, 4000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return (
    <SystemContext.Provider value={{ isOnline, isReconnecting, justRestored, checkHealth }}>
      {children}
    </SystemContext.Provider>
  );
};

export const useSystem = () => {
  const context = useContext(SystemContext);
  if (!context) throw new Error('useSystem debe ser usado dentro de un SystemProvider');
  return context;
};
