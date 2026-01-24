export type RiskLevel = "Safe" | "Caution" | "Elevated" | "Severe";

export const riskStyle: Record<
  RiskLevel,
  {
    border: string;
    badge: string;
    bar: string;
  }
> = {
  Safe: {
    border: "border-green-400/60",
    badge: "bg-green-400/20 text-green-300",
    bar: "bg-green-400",
  },
  Caution: {
    border: "border-yellow-400/60",
    badge: "bg-yellow-400/20 text-yellow-300",
    bar: "bg-yellow-400",
  },
  Elevated: {
    border: "border-orange-400/60",
    badge: "bg-orange-400/20 text-orange-300",
    bar: "bg-orange-400",
  },
  Severe: {
    border: "border-red-500/60 animate-pulse",
    badge: "bg-red-500/30 text-red-300",
    bar: "bg-red-500",
  },
};
