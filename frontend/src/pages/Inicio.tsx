import {
  FileText,
  CheckSquare,
  BarChart3,
  CheckCircle2,
  Circle,
  Clock,
  Server,
  Database,
  ShieldCheck,
  TestTube2,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "../auth/AuthContext";

// ── Phase roadmap ───────────────────────────────────────────────────────────
const PHASES = [
  {
    id: "F0",
    label: "Fase 0 — Habilitación",
    weeks: "Sem. 1–2",
    status: "done" as const,
    pct: 100,
    completed: 4,
    total: 13,
    note: "Infraestructura, BD, CI y auth · completada",
  },
  {
    id: "F1",
    label: "Fase 1 — Canal núcleo de IA",
    weeks: "Sem. 3–6",
    status: "active" as const,
    pct: 40,
    completed: 4,
    total: 10,
    note: "STT + MinIO + worker listos · esperando material Bonsai (F1-05…10)",
  },
  {
    id: "F2",
    label: "Fase 2 — Aplicación web",
    weeks: "Sem. 7–9",
    status: "upcoming" as const,
    pct: 0,
    completed: 0,
    total: 8,
    note: "UI completa · revisión · aprobación",
  },
  {
    id: "F3",
    label: "Fase 3 — Reportería",
    weeks: "Sem. 10–11",
    status: "upcoming" as const,
    pct: 0,
    completed: 0,
    total: 5,
    note: "Asistencia · participación · tiempos",
  },
];

// ── Build metrics ────────────────────────────────────────────────────────────
const METRICS = [
  {
    icon: Server,
    value: "7",
    label: "Servicios Docker",
    sub: "db · redis · minio · mailhog · api · worker · frontend",
    color: "text-blue",
    bg: "bg-blue/10",
  },
  {
    icon: Database,
    value: "15",
    label: "Tablas PostgreSQL",
    sub: "pgvector + Row-Level Security multi-tenant",
    color: "text-indigo",
    bg: "bg-indigo/10",
  },
  {
    icon: ShieldCheck,
    value: "2",
    label: "Migraciones Alembic",
    sub: "0001 schema completo · 0002 políticas RLS",
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
  {
    icon: TestTube2,
    value: "19",
    label: "Tests automatizados",
    sub: "17 backend (auth + tenancy + pipeline) · 2 frontend",
    color: "text-violet-600",
    bg: "bg-violet-50",
  },
];

// ── Navigation cards ─────────────────────────────────────────────────────────
const NAV_CARDS = [
  {
    icon: FileText,
    label: "Reuniones",
    desc: "Cargá grabaciones y revisá actas generadas por IA",
    href: "/reuniones",
    badge: null,
  },
  {
    icon: CheckSquare,
    label: "Acuerdos",
    desc: "Seguimiento de acuerdos por estado y responsable",
    href: "/acuerdos",
    badge: null,
  },
  {
    icon: BarChart3,
    label: "Reportes",
    desc: "Asistencia, participación y cumplimiento de acuerdos",
    href: "/reportes",
    badge: "Fase 3",
  },
];

// ── Helpers ───────────────────────────────────────────────────────────────────
function PhaseStatusIcon({ status }: { status: "done" | "active" | "upcoming" }) {
  if (status === "done")
    return <CheckCircle2 size={16} className="shrink-0 text-emerald-500" />;
  if (status === "active")
    return <Clock size={16} className="shrink-0 text-blue" />;
  return <Circle size={16} className="shrink-0 text-ink/20" />;
}

export default function Inicio() {
  const { user } = useAuth();

  return (
    <div className="space-y-8">
      {/* ── Greeting ── */}
      <div>
        <h2 className="mb-0.5 text-lg font-semibold text-ink">
          Bienvenido, {user?.nombre?.split(" ")[0] ?? "usuario"}
        </h2>
        <p className="text-sm text-ink/50">
          Plataforma de gestión de actas para asociaciones solidaristas · AXIO–Coreintelhub
        </p>
      </div>

      {/* ── Status banners ── */}
      <div className="space-y-2">
        <div className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3.5">
          <CheckCircle2 size={20} className="mt-0.5 shrink-0 text-emerald-500" />
          <div>
            <p className="text-sm font-semibold text-emerald-800">
              Fase 0 completada · Fase 1 en progreso (40%)
            </p>
            <p className="mt-0.5 text-xs text-emerald-700/80">
              Stack completo · transcripción STT verificada end-to-end · MinIO + RQ worker operativos · 19 tests pasando.
            </p>
          </div>
        </div>
        <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3.5">
          <Clock size={20} className="mt-0.5 shrink-0 text-amber-500" />
          <div>
            <p className="text-sm font-semibold text-amber-800">
              Esperando material de Bonsai para continuar F1-05…F1-10
            </p>
            <p className="mt-0.5 text-xs text-amber-700/80">
              Pendiente: plantilla legal del acta · actas históricas (≥20) · grabaciones de muestra · confirmación DPA con Anthropic.
            </p>
          </div>
        </div>
      </div>

      {/* ── Build metrics ── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {METRICS.map(({ icon: Icon, value, label, sub, color, bg }) => (
          <div
            key={label}
            className="rounded-xl border border-border bg-panel p-4"
          >
            <div className={`mb-3 flex h-8 w-8 items-center justify-center rounded-lg ${bg}`}>
              <Icon size={16} className={color} />
            </div>
            <p className="text-2xl font-bold tracking-tight text-ink">{value}</p>
            <p className="mt-0.5 text-xs font-medium text-ink">{label}</p>
            <p className="mt-1 text-[11px] leading-snug text-ink/45">{sub}</p>
          </div>
        ))}
      </div>

      {/* ── Phase roadmap ── */}
      <div className="rounded-xl border border-border bg-panel p-5">
        <h3 className="mb-4 text-sm font-semibold text-ink">Avance del proyecto · 16 semanas</h3>
        <div className="space-y-3">
          {PHASES.map((phase) => (
            <div key={phase.id} className="flex items-center gap-3">
              <PhaseStatusIcon status={phase.status} />
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-2">
                  <span
                    className={`truncate text-xs font-semibold ${
                      phase.status === "upcoming" ? "text-ink/35" : "text-ink"
                    }`}
                  >
                    {phase.label}
                  </span>
                  <span className="shrink-0 text-[11px] font-medium text-ink/40">
                    {phase.weeks}
                  </span>
                </div>
                <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-bg">
                  <div
                    className={`h-1.5 rounded-full transition-all ${
                      phase.status === "done"
                        ? "bg-emerald-400"
                        : phase.status === "active"
                        ? "bg-blue"
                        : "bg-ink/10"
                    }`}
                    style={{ width: `${phase.pct}%` }}
                  />
                </div>
                <p className="mt-0.5 text-[11px] text-ink/40">
                  {phase.status === "upcoming"
                    ? phase.note
                    : `${phase.completed} / ${phase.total} tareas · ${phase.note}`}
                </p>
              </div>
              <span
                className={`shrink-0 text-xs font-bold ${
                  phase.status === "done"
                    ? "text-emerald-500"
                    : phase.status === "active"
                    ? "text-blue"
                    : "text-ink/20"
                }`}
              >
                {phase.pct}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ── Navigation cards ── */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-ink">Módulos</h3>
        <div className="grid gap-4 sm:grid-cols-3">
          {NAV_CARDS.map(({ icon: Icon, label, desc, href, badge }) => (
            <a
              key={label}
              href={href}
              className="group flex flex-col gap-3 rounded-xl border border-border bg-panel p-5 transition-shadow hover:shadow-sm"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-bg">
                  <Icon size={18} className="text-indigo" />
                </div>
                {badge && (
                  <span className="rounded-full bg-indigo/10 px-2 py-0.5 text-[10px] font-semibold text-indigo">
                    {badge}
                  </span>
                )}
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-ink">{label}</p>
                <p className="mt-0.5 text-xs leading-relaxed text-ink/50">{desc}</p>
              </div>
              <div className="flex items-center gap-1 text-[11px] font-medium text-indigo opacity-0 transition-opacity group-hover:opacity-100">
                Ir al módulo <ChevronRight size={12} />
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
