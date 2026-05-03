import { motion } from 'framer-motion';

interface FlightOption {
  id: string;
  airline: string;
  departure: string;
  arrival: string;
  price: number;
}

interface FlightTableProps {
  flights: FlightOption[];
}

export default function FlightTable({ flights }: FlightTableProps) {
  if (!flights || flights.length === 0) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="clay-card overflow-hidden"
    >
      <table className="w-full text-left text-sm" style={{ color: 'var(--color-neutral-600)' }}>
        <thead style={{ backgroundColor: 'var(--color-neutral-50)', borderBottom: '1px solid var(--color-oat-border)' }}>
          <tr>
            <th className="px-6 py-3 text-xs font-semibold uppercase" style={{ color: 'var(--color-neutral-400)', letterSpacing: '1px' }}>Airline</th>
            <th className="px-6 py-3 text-xs font-semibold uppercase" style={{ color: 'var(--color-neutral-400)', letterSpacing: '1px' }}>Departure</th>
            <th className="px-6 py-3 text-xs font-semibold uppercase" style={{ color: 'var(--color-neutral-400)', letterSpacing: '1px' }}>Arrival</th>
            <th className="px-6 py-3 text-xs font-semibold uppercase text-right" style={{ color: 'var(--color-neutral-400)', letterSpacing: '1px' }}>Price</th>
          </tr>
        </thead>
        <tbody>
          {flights.map((flight, idx) => (
            <tr 
              key={idx} 
              className="transition-colors"
              style={{ borderBottom: '1px solid var(--color-oat-border)' }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--color-neutral-50)')}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
            >
              <td className="px-6 py-4 font-semibold" style={{ color: 'var(--color-clay-black)' }}>{flight.airline || 'Standard Air'}</td>
              <td className="px-6 py-4">{flight.departure}</td>
              <td className="px-6 py-4">{flight.arrival}</td>
              <td className="px-6 py-4 text-right font-bold" style={{ color: 'var(--color-emerald-600)' }}>₹{flight.price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </motion.div>
  );
}
