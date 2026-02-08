import { useEffect, useRef, useState } from 'react';

type ColorKey = 'blue' | 'emerald' | 'violet' | 'amber' | 'rose';

interface StatsCardProps {
  title: string;
  value: string | number;
  trend?: string;
  highlight?: boolean;
  icon?: React.ReactNode;
  color?: ColorKey;
}

const COLOR_MAP: Record<ColorKey, { bg: string; text: string; icon: string; bar: string; ring: string }> = {
  blue:    { bg: 'bg-blue-50',    text: 'text-blue-600',    icon: 'text-blue-500',    bar: 'bg-blue-500',    ring: 'ring-blue-100' },
  emerald: { bg: 'bg-emerald-50', text: 'text-emerald-600', icon: 'text-emerald-500', bar: 'bg-emerald-500', ring: 'ring-emerald-100' },
  violet:  { bg: 'bg-primary-50', text: 'text-primary-600', icon: 'text-primary-500', bar: 'bg-primary-500', ring: 'ring-primary-100' },
  amber:   { bg: 'bg-amber-50',   text: 'text-amber-600',   icon: 'text-amber-500',   bar: 'bg-amber-500',   ring: 'ring-amber-100' },
  rose:    { bg: 'bg-rose-50',    text: 'text-rose-600',    icon: 'text-rose-500',    bar: 'bg-rose-500',    ring: 'ring-rose-100' },
};

function AnimatedNumber({ value }: { value: string | number }) {
  const numericValue = typeof value === 'number' ? value : parseFloat(value);
  const isNumeric = !isNaN(numericValue);
  const [display, setDisplay] = useState(isNumeric ? 0 : value);
  const ref = useRef<number>(0);

  useEffect(() => {
    if (!isNumeric) { setDisplay(value); return; }
    const start = ref.current;
    const end = numericValue;
    const duration = 600;
    const startTime = performance.now();

    function animate(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + (end - start) * eased;
      setDisplay(Number.isInteger(end) ? Math.round(current) : +current.toFixed(1));
      if (progress < 1) requestAnimationFrame(animate);
      else ref.current = end;
    }
    requestAnimationFrame(animate);
  }, [value]);

  return <>{display}</>;
}

export function StatsCard({ title, value, trend, highlight = false, icon, color = 'violet' }: StatsCardProps) {
  const c = COLOR_MAP[color];

  return (
    <div className={`
      relative group p-5 rounded-2xl transition-all duration-300 overflow-hidden
      bg-white border shadow-card hover:shadow-card-hover hover:-translate-y-0.5
      ${highlight ? `border-${color === 'emerald' ? 'emerald' : 'primary'}-100 ring-1 ${c.ring}` : 'border-slate-100'}
    `}>
      {/* Color accent bar at top */}
      <div className={`absolute top-0 left-0 right-0 h-[3px] ${c.bar} opacity-80`} />

      <div className="flex items-start justify-between mb-4">
        {/* Icon */}
        {icon && (
          <div className={`w-10 h-10 rounded-xl ${c.bg} flex items-center justify-center ${c.icon} transition-transform group-hover:scale-110`}>
            {icon}
          </div>
        )}
        {/* Trend badge */}
        {trend && (
          <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-lg ${c.bg} ${c.text}`}>
            {trend}
          </span>
        )}
      </div>

      {/* Value */}
      <div className="mb-1">
        <p className={`text-3xl font-bold tracking-tight tabular-nums ${highlight ? c.text : 'text-slate-900'}`}>
          <AnimatedNumber value={value} />
        </p>
      </div>

      {/* Title */}
      <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
        {title}
      </p>
    </div>
  );
}
