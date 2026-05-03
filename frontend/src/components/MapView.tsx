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
      className="clay-card w-full h-64 overflow-hidden relative"
    >
      {/* Placeholder for actual Google Maps embed / overlay */}
      <div 
        className="absolute inset-0 flex flex-col items-center justify-center p-4 text-center"
        style={{ backgroundColor: 'var(--color-neutral-50)' }}
      >
        <div className="mb-3" style={{ color: 'var(--color-emerald-500)' }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon>
            <line x1="9" y1="3" x2="9" y2="18"></line>
            <line x1="15" y1="6" x2="15" y2="21"></line>
          </svg>
        </div>
        <h3 className="font-semibold mb-1" style={{ color: 'var(--color-clay-black)', letterSpacing: '-0.3px' }}>
          Interactive Route Map
        </h3>
        <p className="text-sm" style={{ color: 'var(--color-neutral-400)' }}>
          {origin} <span className="mx-2" style={{ color: 'var(--color-emerald-500)' }}>→</span> {destination}
        </p>
        {polyline && (
          <p className="text-xs mt-2 font-medium" style={{ color: 'var(--color-emerald-600)' }}>
            ✓ Route generated successfully
          </p>
        )}
      </div>
    </motion.div>
  );
}
