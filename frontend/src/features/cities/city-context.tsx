"use client";

import { useQuery } from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { getCities, getCity, type CityResponse } from "@/lib/api";

const STORAGE_KEY = "civicsense:selected-city";
const DEFAULT_CITY_SLUG = "pune";

type CityContextValue = {
  citySlug: string;
  selectedCity: CityResponse | undefined;
  isLoading: boolean;
  setCitySlug: (slug: string) => void;
  isReportingEnabled: boolean;
  cities: CityResponse[];
};

const CityContext = createContext<CityContextValue | null>(null);

function readStoredSlug(): string {
  if (typeof window === "undefined") {
    return DEFAULT_CITY_SLUG;
  }
  return localStorage.getItem(STORAGE_KEY) ?? DEFAULT_CITY_SLUG;
}

export function CityProvider({ children }: { children: React.ReactNode }) {
  const [citySlug, setCitySlugState] = useState(DEFAULT_CITY_SLUG);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setCitySlugState(readStoredSlug());
    setHydrated(true);
  }, []);

  const citiesQuery = useQuery({
    queryKey: ["cities"],
    queryFn: () => getCities(),
  });

  const cityQuery = useQuery({
    queryKey: ["city", citySlug],
    queryFn: () => getCity(citySlug),
    enabled: hydrated && Boolean(citySlug),
  });

  const setCitySlug = useCallback((slug: string) => {
    setCitySlugState(slug);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, slug);
    }
  }, []);

  const selectedCity = cityQuery.data;
  const isReportingEnabled = Boolean(
    selectedCity?.supports_reporting && selectedCity.status === "active",
  );

  const value = useMemo<CityContextValue>(
    () => ({
      citySlug,
      selectedCity,
      isLoading: !hydrated || citiesQuery.isLoading || cityQuery.isLoading,
      setCitySlug,
      isReportingEnabled,
      cities: citiesQuery.data ?? [],
    }),
    [
      citySlug,
      selectedCity,
      hydrated,
      citiesQuery.isLoading,
      citiesQuery.data,
      cityQuery.isLoading,
      setCitySlug,
      isReportingEnabled,
    ],
  );

  return <CityContext.Provider value={value}>{children}</CityContext.Provider>;
}

export function useCity() {
  const context = useContext(CityContext);
  if (!context) {
    throw new Error("useCity must be used within CityProvider");
  }
  return context;
}
