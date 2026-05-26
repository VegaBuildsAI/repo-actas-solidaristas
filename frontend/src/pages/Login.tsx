import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [correo, setCorreo] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(correo, password);
      navigate("/");
    } catch {
      setError("Correo o contraseña incorrectos.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink">
      <div className="w-full max-w-sm rounded-xl bg-panel p-8 shadow-lg">
        <h1 className="mb-1 text-xl font-semibold text-ink">Actas Solidaristas</h1>
        <p className="mb-6 text-sm text-ink/50">Iniciá sesión para continuar</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-ink/70">Correo electrónico</label>
            <input
              type="email"
              value={correo}
              onChange={(e) => setCorreo(e.target.value)}
              required
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-ink placeholder-ink/30 focus:border-indigo focus:outline-none focus:ring-1 focus:ring-indigo"
              placeholder="nombre@asociacion.cr"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-ink/70">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-ink placeholder-ink/30 focus:border-indigo focus:outline-none focus:ring-1 focus:ring-indigo"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-xs text-red-600">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-indigo py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-dk disabled:opacity-60"
          >
            {loading ? "Ingresando…" : "Ingresar"}
          </button>
        </form>
      </div>
    </div>
  );
}
