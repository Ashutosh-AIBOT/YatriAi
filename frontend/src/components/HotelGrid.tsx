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
          className="glass-panel p-4 rounded-xl border border-slate-700 hover:border-indigo-500/50 transition-all cursor-pointer"
        >
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-bold text-white text-base">{hotel.name}</h3>
            <span className="flex items-center text-yellow-400 text-sm">
              ★ {hotel.rating}
            </span>
          </div>
          <div className="text-emerald-400 font-bold text-lg mb-3">
            ₹{hotel.price_per_night} <span className="text-xs text-slate-400 font-normal">/ night</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {hotel.amenities.map((amenity, i) => (
              <span key={i} className="px-2 py-1 bg-slate-800 rounded text-xs text-slate-300">
                {amenity}
              </span>
            ))}
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}
