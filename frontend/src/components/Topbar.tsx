import { LogOut } from "lucide-react";
import { useAuth } from "../auth/AuthContext";

export default function Topbar() {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-panel px-6">
      <div />
      <div className="flex items-center gap-4">
        {user && (
          <span className="text-sm text-ink/70">{user.nombre}</span>
        )}
        <button
          onClick={logout}
          className="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm text-ink/60 transition-colors hover:bg-border hover:text-ink"
        >
          <LogOut size={15} />
          Salir
        </button>
      </div>
    </header>
  );
}
