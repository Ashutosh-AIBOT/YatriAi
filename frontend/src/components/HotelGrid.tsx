import { motion } from 'framer-motion';

interface HotelOption {
  id: string;
  name: string;
  rating: number;
  price_per_night: number;
  amenities: string[];
}

interface HotelGridProps {
  hotels: HotelOption[];
}

export default function HotelGrid({ hotels }: HotelGridProps) {
  if (!hotels || hotels.length === 0) return null;

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="grid grid-cols-1 md:grid-cols-2 gap-4"
    >
      {hotels.map((hotel, idx) => (
        <motion.div 
          key={idx}
          whileHover={{ scale: 1.02 }}
          className="clay-card p-5 cursor-pointer"
        >
          <div className="flex justify-between items-start mb-3">
            <h3 className="font-semibold text-base" style={{ color: 'var(--color-clay-black)', letterSpacing: '-0.3px' }}>
              {hotel.name}
            </h3>
            <span className="flex items-center text-sm font-medium" style={{ color: 'var(--color-lemon-700)' }}>
              ★ {hotel.rating}
            </span>
          </div>
          <div className="font-bold text-lg mb-3" style={{ color: 'var(--color-emerald-600)' }}>
            ₹{hotel.price_per_night} <span className="text-xs font-normal" style={{ color: 'var(--color-neutral-400)' }}>/ night</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {hotel.amenities.map((amenity, i) => (
              <span 
                key={i} 
                className="px-2.5 py-1 rounded-md text-xs font-medium"
                style={{ 
                  backgroundColor: 'var(--color-neutral-100)', 
                  color: 'var(--color-neutral-600)',
                  border: '1px solid var(--color-oat-border)'
                }}
              >
                {amenity}
              </span>
            ))}
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}
