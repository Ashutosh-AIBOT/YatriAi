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
      className="glass-panel rounded-2xl overflow-hidden"
    >
      <table className="w-full text-left text-sm text-slate-300">
        <thead className="bg-slate-800/50 text-xs uppercase text-slate-400">
          <tr>
            <th className="px-6 py-3">Airline</th>
            <th className="px-6 py-3">Departure</th>
            <th className="px-6 py-3">Arrival</th>
            <th className="px-6 py-3 text-right">Price</th>
          </tr>
        </thead>
        <tbody>
          {flights.map((flight, idx) => (
            <tr key={idx} className="border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors">
              <td className="px-6 py-4 font-medium text-white">{flight.airline || 'Standard Air'}</td>
              <td className="px-6 py-4">{flight.departure}</td>
              <td className="px-6 py-4">{flight.arrival}</td>
              <td className="px-6 py-4 text-right text-emerald-400 font-bold">₹{flight.price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </motion.div>
  );
}
