import { create } from 'zustand';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface StageCard {
  id: string;
  type: 'transport' | 'hotel' | 'food' | 'place' | 'cab';
  data: any;
  isConfirmed: boolean;
}

interface TripState {
  tripId: string | null;
  messages: Message[];
  stages: StageCard[];
  currentStageIdx: number;
  isGenerating: boolean;
  setTripId: (id: string) => void;
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  addStage: (stage: StageCard) => void;
  updateStage: (id: string, updates: Partial<StageCard>) => void;
  setGenerating: (generating: boolean) => void;
}

export const useTripStore = create<TripState>((set) => ({
  tripId: null,
  messages: [],
  stages: [],
  currentStageIdx: 1,
  isGenerating: false,
  setTripId: (id) => set({ tripId: id }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setMessages: (messages) => set({ messages }),
  addStage: (stage) => set((state) => ({ stages: [...state.stages, stage] })),
  updateStage: (id, updates) => set((state) => ({
    stages: state.stages.map((s) => s.id === id ? { ...s, ...updates } : s)
  })),
  setGenerating: (generating) => set({ isGenerating: generating }),
}));
