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
      className="glass-panel rounded-2xl overflow-hidden"
    >
      <table className="w-full text-left text-sm text-slate-300">
        <thead className="bg-slate-800/50 text-xs uppercase text-slate-400">
          <tr>
            <th className="px-6 py-3">Provider</th>
            <th className="px-6 py-3">Vehicle</th>
            <th className="px-6 py-3">ETA</th>
            <th className="px-6 py-3 text-right">Est. Price</th>
          </tr>
        </thead>
        <tbody>
          {options.map((cab, idx) => (
            <tr key={idx} className="border-b border-slate-700/50 hover:bg-slate-800/30 transition-colors">
              <td className="px-6 py-4 font-medium text-white">{cab.provider}</td>
              <td className="px-6 py-4">{cab.vehicle_type}</td>
              <td className="px-6 py-4">{cab.eta}</td>
              <td className="px-6 py-4 text-right text-emerald-400 font-bold">₹{cab.price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </motion.div>
  );
}
