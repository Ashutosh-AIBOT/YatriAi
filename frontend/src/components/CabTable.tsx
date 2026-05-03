import { motion } from 'framer-motion';

interface CabOption {
  provider: string;
  price: number;
  eta: string;
  vehicle_type: string;
}

interface CabTableProps {
  options: CabOption[];
}

export default function CabTable({ options }: CabTableProps) {
  if (!options || options.length === 0) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="clay-card overflow-hidden"
    >
      <table className="w-full text-left text-sm" style={{ color: 'var(--color-neutral-600)' }}>
        <thead style={{ backgroundColor: 'var(--color-neutral-50)', borderBottom: '1px solid var(--color-oat-border)' }}>
          <tr>
            <th className="px-6 py-3 text-xs font-semibold uppercase" style={{ color: 'var(--color-neutral-400)', letterSpacing: '1px' }}>Provider</th>
            <th className="px-6 py-3 text-xs font-semibold uppercase" style={{ color: 'var(--color-neutral-400)', letterSpacing: '1px' }}>Vehicle</th>
            <th className="px-6 py-3 text-xs font-semibold uppercase" style={{ color: 'var(--color-neutral-400)', letterSpacing: '1px' }}>ETA</th>
            <th className="px-6 py-3 text-xs font-semibold uppercase text-right" style={{ color: 'var(--color-neutral-400)', letterSpacing: '1px' }}>Est. Price</th>
          </tr>
        </thead>
        <tbody>
          {options.map((cab, idx) => (
            <tr 
              key={idx} 
              className="transition-colors"
              style={{ borderBottom: '1px solid var(--color-oat-border)' }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--color-neutral-50)')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
            >
              <td className="px-6 py-4 font-semibold" style={{ color: 'var(--color-clay-black)' }}>{cab.provider}</td>
              <td className="px-6 py-4">{cab.vehicle_type}</td>
              <td className="px-6 py-4">{cab.eta}</td>
              <td className="px-6 py-4 text-right font-bold" style={{ color: 'var(--color-emerald-600)' }}>₹{cab.price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </motion.div>
  );
}
