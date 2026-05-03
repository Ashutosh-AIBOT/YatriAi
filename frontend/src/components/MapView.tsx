import { motion } from 'framer-motion';

interface MapViewProps {
  origin: string;
  destination: string;
  polyline?: string;
}

export default function MapView({ origin, destination, polyline }: MapViewProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full h-64 rounded-2xl overflow-hidden glass-panel relative"
    >
      {/* Placeholder for actual Google Maps embed / overlay */}
      <div className="absolute inset-0 bg-slate-800/80 flex flex-col items-center justify-center p-4 text-center">
        <div className="text-indigo-400 mb-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="18"></line><line x1="15" y1="6" x2="15" y2="21"></line></svg>
        </div>
        <h3 className="font-bold text-white mb-1">Interactive Route Map</h3>
        <p className="text-sm text-slate-400">
          {origin} <span className="mx-2">→</span> {destination}
        </p>
        {polyline && (
          <p className="text-xs text-emerald-400 mt-2">Route generated successfully</p>
        )}
      </div>
    </motion.div>
  );
}
