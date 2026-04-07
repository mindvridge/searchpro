import { create } from "zustand";

interface SearchState {
  query: string;
  category: string;
  region: string;
  setQuery: (query: string) => void;
  setCategory: (category: string) => void;
  setRegion: (region: string) => void;
  reset: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  query: "",
  category: "",
  region: "",
  setQuery: (query) => set({ query }),
  setCategory: (category) => set({ category }),
  setRegion: (region) => set({ region }),
  reset: () => set({ query: "", category: "", region: "" }),
}));
