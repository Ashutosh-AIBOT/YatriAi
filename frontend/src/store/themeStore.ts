import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ThemeName = 'warm-cream' | 'soft-sage' | 'cool-mist';

interface ThemeState {
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
}

export const THEMES: { id: ThemeName; label: string; swatchClass: string; description: string }[] = [
  { id: 'warm-cream', label: 'Warm Cream', swatchClass: 'theme-swatch-cream', description: 'Cozy, inviting tones' },
  { id: 'soft-sage', label: 'Soft Sage', swatchClass: 'theme-swatch-sage', description: 'Calming green-grey' },
  { id: 'cool-mist', label: 'Cool Mist', swatchClass: 'theme-swatch-mist', description: 'Modern blue-grey' },
];

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'warm-cream',
      setTheme: (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        set({ theme });
      },
    }),
    {
      name: 'yatri-theme',
      onRehydrateStorage: () => (state) => {
        if (state?.theme) {
          document.documentElement.setAttribute('data-theme', state.theme);
        }
      },
    }
  )
);
