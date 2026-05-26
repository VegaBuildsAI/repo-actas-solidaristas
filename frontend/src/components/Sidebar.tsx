import { BarChart3, CheckSquare, FileText, LayoutDashboard } from "lucide-react";
import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/", icon: LayoutDashboard, label: "Inicio" },
  { to: "/reuniones", icon: FileText, label: "Reuniones" },
  { to: "/acuerdos", icon: CheckSquare, label: "Acuerdos" },
  { to: "/reportes", icon: BarChart3, label: "Reportes" },
];

export default function Sidebar() {
  return (
    <aside className="flex h-full w-56 flex-col bg-sidebar">
      <div className="flex h-16 items-center px-6">
        <span className="text-sm font-semibold tracking-wide text-white/80">Actas Solidaristas</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-sidebar-active text-white"
                  : "text-white/60 hover:bg-sidebar-active/60 hover:text-white/90"
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
