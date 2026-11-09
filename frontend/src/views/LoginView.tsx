import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock, Mail, User, Phone, AlertCircle, ArrowRight } from 'lucide-react';

export const LoginView: React.FC = () => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setLoading(true);

    const endpoint = isRegister ? '/api/v1/auth/register' : '/api/v1/auth/login';
    const payload = isRegister
      ? { email, password, full_name: fullName, phone }
      : { email, password };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Error en autenticación');
      }

      login(data.access_token, data.user);
      if (data.user.role === 'administrador') {
        navigate('/admin');
      } else {
        navigate('/');
      }
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-12">
      <div className="bg-white rounded-2xl border border-crema-200 overflow-hidden shadow-sm grid grid-cols-1 md:grid-cols-12 min-h-[520px]">
        
        {/* Columna Izquierda: Ilustración de Marca con Ondas */}
        <div className="hidden md:flex md:col-span-5 bg-gradient-to-br from-menta-500 via-aguamarina-300 to-menta-100 p-8 flex-col justify-between text-carbon-500 relative overflow-hidden">
          <div className="z-10 space-y-2">
            <div className="flex items-center gap-2">
              <img src="/assets/isotipo.svg" alt="Marea Dulce" className="w-8 h-8" />
              <span className="font-serif text-2xl font-bold text-petroleo-500">Marea Dulce</span>
            </div>
            <p className="text-xs text-gris-700 italic">Pequeños antojos, grandes momentos.</p>
          </div>

          <div className="z-10 space-y-3">
            <h3 className="font-serif text-2xl font-semibold text-petroleo-500 leading-tight">
              Bienvenido a nuestra pastelería artesanal
            </h3>
            <p className="text-xs text-gris-700 leading-relaxed">
              Inicia sesión para consultar tus pedidos, gestionar direcciones frecuentes y vivir una experiencia dulce y personalizada.
            </p>
          </div>

          {/* Patrón de Ondas en el fondo */}
          <div className="absolute inset-0 opacity-20 pointer-events-none">
            <img src="/assets/wave-pattern.svg" alt="Ondas" className="w-full h-full object-cover" />
          </div>
        </div>

        {/* Columna Derecha: Formulario */}
        <div className="md:col-span-7 p-6 sm:p-10 flex flex-col justify-center">
          
          {/* Pestañas Login / Registro */}
          <div className="flex border-b border-crema-200 mb-6">
            <button
              onClick={() => {
                setIsRegister(false);
                setErrorMsg(null);
              }}
              className={`pb-3 font-semibold text-sm transition-all px-4 ${
                !isRegister
                  ? 'border-b-2 border-petroleo-500 text-petroleo-500'
                  : 'text-gris-700 hover:text-carbon-500'
              }`}
            >
              Iniciar Sesión
            </button>
            <button
              onClick={() => {
                setIsRegister(true);
                setErrorMsg(null);
              }}
              className={`pb-3 font-semibold text-sm transition-all px-4 ${
                isRegister
                  ? 'border-b-2 border-petroleo-500 text-petroleo-500'
                  : 'text-gris-700 hover:text-carbon-500'
              }`}
            >
              Crear Cuenta
            </button>
          </div>

          {errorMsg && (
            <div className="mb-4 p-3 bg-feedback-error-bg border border-feedback-error/30 rounded-md text-xs text-feedback-error flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            
            {isRegister && (
              <>
                <div>
                  <label className="block text-xs font-semibold text-carbon-500 mb-1">Nombre Completo *</label>
                  <div className="relative">
                    <User className="w-4 h-4 text-gris-700 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Ej: Daniel Gómez"
                      className="w-full pl-9 pr-3 py-2 bg-crema-100/40 border border-crema-300 rounded-md text-sm text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-carbon-500 mb-1">Teléfono Móvil (Opcional)</label>
                  <div className="relative">
                    <Phone className="w-4 h-4 text-gris-700 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+57 310 000 0000"
                      className="w-full pl-9 pr-3 py-2 bg-crema-100/40 border border-crema-300 rounded-md text-sm text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <label className="block text-xs font-semibold text-carbon-500 mb-1">Correo Electrónico *</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-gris-700 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@mareadulce.com"
                  className="w-full pl-9 pr-3 py-2 bg-crema-100/40 border border-crema-300 rounded-md text-sm text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-carbon-500 mb-1">Contraseña *</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-gris-700 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-3 py-2 bg-crema-100/40 border border-crema-300 rounded-md text-sm text-carbon-500 focus:outline-none focus:ring-2 focus:ring-petroleo-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-aguamarina-500 hover:bg-aguamarina-600 text-carbon-500 font-bold rounded-md flex items-center justify-center gap-2 shadow-sm transition-all min-h-[44px]"
            >
              <span>{loading ? 'Procesando...' : isRegister ? 'Registrarme' : 'Entrar a mi Cuenta'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            {!isRegister && (
              <div className="text-center text-xs text-gris-700 pt-2">
                <span>¿Credenciales de demostración Admin?</span>{' '}
                <span className="font-mono text-petroleo-500 font-semibold">admin@mareadulce.com</span> /{' '}
                <span className="font-mono text-petroleo-500 font-semibold">AdminMarea2026!</span>
              </div>
            )}

          </form>
        </div>

      </div>
    </div>
  );
};
