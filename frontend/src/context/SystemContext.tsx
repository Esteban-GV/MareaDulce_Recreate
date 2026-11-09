import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { checkBackendHealth } from '../services/api';

interface SystemContextType {
  isOnline: boolean;
  isReconnecting: boolean;
  justRestored: boolean;
  version: string;
  checkHealth: () => Promise<boolean>;
}

const SystemContext = createContext<SystemContextType | undefined>(undefined);

export const SystemProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [isReconnecting, setIsReconnecting] = useState<boolean>(false);
  const [justRestored, setJustRestored] = useState<boolean>(false);
  const [version, setVersion] = useState<string>('1.0.0');

  const fetchVersion = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/version', { signal: AbortSignal.timeout(2000) });
      if (res.ok) {
        const data = await res.json();
        if (data.version) {
          setVersion(data.version);
        }
      }
    } catch {
      // Ignorar fallos transitorios durante recreate
    }
  }, []);

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
      fetchVersion();
      setTimeout(() => setJustRestored(false), 6000);
    } else if (healthy) {
      fetchVersion();
    }
    return healthy;
  }, [isOnline, fetchVersion]);

  useEffect(() => {
    // Verificación inicial y sondeo periódico cada 4 segundos
    checkHealth();
    const interval = setInterval(() => {
      checkHealth();
    }, 4000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return (
    <SystemContext.Provider value={{ isOnline, isReconnecting, justRestored, version, checkHealth }}>
      {children}
    </SystemContext.Provider>
  );
};

export const useSystem = () => {
  const context = useContext(SystemContext);
  if (!context) throw new Error('useSystem debe ser usado dentro de un SystemProvider');
  return context;
};
